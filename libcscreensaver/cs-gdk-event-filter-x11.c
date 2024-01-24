/*
 * CsGdkEventFilter: An introspectable C class that establishes an event
 * trap for the screensaver.  It watches for any X events that could result
 * in other windows showing up over our Stage, and ensures the Stage stays on
 * top.  This will only ever be other override-redirect (non-managed) X windows,
 * such as native Firefox or Chrome notification popups.
 *
 */

#include "config.h"
#include "cs-gdk-event-filter.h"
#include "cs-screen.h"

#ifdef HAVE_SHAPE_EXT
#include <X11/extensions/shape.h>
#endif
#include <X11/Xatom.h>
#include <gtk/gtkx.h>
#include <string.h>

enum {
        XSCREEN_SIZE,
        SCREENSAVER_WINDOW_CHANGED,
        LAST_SIGNAL
};

static guint signals [LAST_SIGNAL] = { 0, };

G_DEFINE_TYPE (CsGdkEventFilter, cs_gdk_event_filter, G_TYPE_OBJECT)

static gboolean
ignore_fcitx_input_window (CsGdkEventFilter *filter, Window xid)
{
    XClassHint *clh;
    Display *xdpy;
    gboolean ret = FALSE;
    int status;

    gdk_x11_display_error_trap_push (filter->display);

    xdpy = GDK_DISPLAY_XDISPLAY (filter->display);

    clh = XAllocClassHint();
    status = XGetClassHint (xdpy, xid, clh);

    if (status)
    {
        if (g_strcmp0 (clh->res_name, "fcitx") == 0)
        {
            ret = TRUE;
        }

        g_clear_pointer (&clh->res_name, XFree);
        g_clear_pointer (&clh->res_class, XFree);
    }

    XFree (clh);

    if (!ret)
    {
        return FALSE;
    }

    ret = FALSE;

    XTextProperty text;

    status = XGetWMName(xdpy, xid, &text);
    if (status)
    {
        gint count;
        gchar **list;
        status = XmbTextPropertyToTextList (xdpy, &text, &list, &count);

        if (status == Success && count > 0)
        {
            gint i;

            for (i = 0; i < count; i++)
            {
                if (g_strcmp0 (list[i], "Fcitx Input Window") == 0)
                {
                    ret = TRUE;
                    break;
                }
            }

            XFreeStringList (list);
            XFree (text.value);
        }
    }

    gdk_x11_display_error_trap_pop_ignored (filter->display);

    return ret;
}

static void
unshape_window (CsGdkEventFilter *filter)
{
    g_return_if_fail (CS_IS_GDK_EVENT_FILTER (filter));

    gdk_window_shape_combine_region (gtk_widget_get_window (GTK_WIDGET (filter->managed_window)),
                                     NULL,
                                     0,
                                     0);
}

static void
restack (CsGdkEventFilter *filter,
         Window            event_window,
         const gchar      *event_type)
{
    g_autofree gchar *net_wm_name = NULL;

    gdk_x11_display_error_trap_push (filter->display);

    net_wm_name = cs_screen_get_net_wm_name (event_window);

    if (g_strcmp0 (net_wm_name, "event-grabber-window") == 0)
    {
        g_debug ("(Ignoring %s from CsEventGrabber window)", event_type);
        gdk_x11_display_error_trap_pop_ignored (filter->display);
        return;
    }

    // Screensaver windows get re-made but we want to pick up new ones
    // so the backup locker can stay in place always.
    if (filter->pretty_xid != event_window)
    {
        if (g_strcmp0 (net_wm_name, "cinnamon-screensaver-window") == 0)
        {
            g_debug ("New screensaver window found: 0x%lx (replaces 0x%lx)", event_window, filter->pretty_xid);
            filter->pretty_xid = event_window;
            g_signal_emit (filter, signals[SCREENSAVER_WINDOW_CHANGED], 0, event_window);
        }
    }

    if (filter->we_are_backup_window)
    {
        if (event_window != filter->pretty_xid)
        {
            g_debug ("BackupWindow received %s from window '%s' (0x%lx), raising ourselves.",
                      event_type,
                      net_wm_name,
                      event_window);

            XRaiseWindow(GDK_DISPLAY_XDISPLAY (filter->display), filter->my_xid);
        }
    }
    else
    {
        g_debug ("Screensaver received %s from window '%s' (0x%lx), raising ourselves.",
                  event_type,
                  net_wm_name,
                  event_window);

        XRaiseWindow(GDK_DISPLAY_XDISPLAY (filter->display), filter->my_xid);
    }

    XFlush (GDK_DISPLAY_XDISPLAY (filter->display));

    gdk_x11_display_error_trap_pop_ignored (filter->display);
}

static GdkFilterReturn
cs_gdk_event_filter_xevent (CsGdkEventFilter *filter,
                            GdkXEvent        *xevent)
{
    XEvent *ev;

    ev = xevent;
    /* MapNotify is used to tell us when new windows are mapped.
       ConfigureNofify is used to tell us when windows are raised. */
    switch (ev->xany.type) {
        case MapNotify:
          {
            XMapEvent *xme = &ev->xmap;

            if (ignore_fcitx_input_window (filter, xme->window) && filter->we_are_backup_window)
            {
                g_debug ("Ignoring MapNotify for fcitx window (we're the backup-locker).");
                break;
            }

            // Ignore my own events.
            if (xme->window == filter->my_xid)
            {
                break;
            }

            restack (filter, xme->window, "MapNotify");
            break;
          }
        case ConfigureNotify:
          {
            XConfigureEvent *xce = &ev->xconfigure;

            // If the reported window is the root window, and we're the backup window (we have a pretty
            // xid) then signal to resize to the root window (screen).
            if (xce->window == GDK_ROOT_WINDOW ())
            {
                // Screen size may have changed, tell the fallback
                g_debug ("ConfigureNotify from root window (0x%lx), screen size may have changed. %s",
                             xce->window,
                             filter->we_are_backup_window ? "(we're the backup-locker)" : "");

                // The screensaver doesn't need to know, it will get notified by CsScreen.
                if (filter->we_are_backup_window)
                {
                    g_signal_emit (filter, signals[XSCREEN_SIZE], 0);
                }
                break;
            }

            if (ignore_fcitx_input_window (filter, xce->window) && filter->we_are_backup_window)
            {
                g_debug ("Ignoring ConfigureNotify for fcitx window (we're the backup-locker).");
                break;
            }

            // Ignore my own events
            if (xce->window == filter->my_xid)
            {
                break;
            }

            restack (filter, xce->window, "ConfigureNotify");
            break;
          }
        default:
          {
#ifdef HAVE_SHAPE_EXT
            if (ev->xany.type == (filter->shape_event_base + ShapeNotify)) {
                g_debug ("ShapeNotify event. %s",
                             filter->we_are_backup_window ? "(we're the backup-locker)" : "");
                unshape_window (filter);
            }
#endif
          }
    }

    return GDK_FILTER_CONTINUE;
}

static void
select_popup_events (CsGdkEventFilter *filter)
{
    XWindowAttributes attr;
    unsigned long     events;

    gdk_x11_display_error_trap_push (filter->display);

    memset (&attr, 0, sizeof (attr));
    XGetWindowAttributes (GDK_DISPLAY_XDISPLAY (filter->display), GDK_ROOT_WINDOW (), &attr);

    events = SubstructureNotifyMask | attr.your_event_mask;
    XSelectInput (GDK_DISPLAY_XDISPLAY (filter->display), GDK_ROOT_WINDOW (), events);

    gdk_x11_display_error_trap_pop_ignored (filter->display);
}

static void
select_shape_events (CsGdkEventFilter *filter)
{
#ifdef HAVE_SHAPE_EXT
    unsigned long events;
    int           shape_error_base;

    gdk_x11_display_error_trap_push (filter->display);

    if (XShapeQueryExtension (GDK_DISPLAY_XDISPLAY (filter->display), &filter->shape_event_base, &shape_error_base)) {
        events = ShapeNotifyMask;

        XShapeSelectInput (GDK_DISPLAY_XDISPLAY (filter->display),
                           GDK_WINDOW_XID (gtk_widget_get_window (GTK_WIDGET (filter->managed_window))),
                           events);
    }

    gdk_x11_display_error_trap_pop_ignored (filter->display);
#endif
}

static GdkFilterReturn
xevent_filter (GdkXEvent *xevent,
               GdkEvent  *event,
               CsGdkEventFilter *filter)
{
    return cs_gdk_event_filter_xevent (filter, xevent);
}

static void
cs_gdk_event_filter_init (CsGdkEventFilter *filter)
{
    filter->shape_event_base = 0;
    filter->managed_window = NULL;
    filter->pretty_xid = 0;
    filter->my_xid = 0;
}

static void
cs_gdk_event_filter_finalize (GObject *object)
{
    CsGdkEventFilter *filter;

    g_return_if_fail (object != NULL);
    g_return_if_fail (CS_IS_GDK_EVENT_FILTER (object));

    filter = CS_GDK_EVENT_FILTER (object);

    cs_gdk_event_filter_stop (filter);
    g_object_unref (filter->managed_window);

    G_OBJECT_CLASS (cs_gdk_event_filter_parent_class)->finalize (object);
}

static void
cs_gdk_event_filter_class_init (CsGdkEventFilterClass *klass)
{
        GObjectClass   *object_class = G_OBJECT_CLASS (klass);

        object_class->finalize     = cs_gdk_event_filter_finalize;

        signals[XSCREEN_SIZE] = g_signal_new ("xscreen-size",
                                              G_TYPE_FROM_CLASS (object_class),
                                              G_SIGNAL_RUN_LAST,
                                              0,
                                              NULL, NULL, NULL,
                                              G_TYPE_NONE, 0);
        signals[SCREENSAVER_WINDOW_CHANGED] = g_signal_new ("screensaver-window-changed",
                                              G_TYPE_FROM_CLASS (object_class),
                                              G_SIGNAL_RUN_LAST,
                                              0,
                                              NULL, NULL, NULL,
                                              G_TYPE_NONE, 1, G_TYPE_ULONG);
}

static void
muted_log_handler (const char     *log_domain,
                   GLogLevelFlags  log_level,
                   const char     *message,
                   gpointer        data)
{
  /* Intentionally empty to discard message */
}

void
cs_gdk_event_filter_start (CsGdkEventFilter *filter,
                           gboolean          fractional_scaling,
                           gboolean          debug)
{
    select_popup_events (filter);
    select_shape_events (filter);

    if (debug)
    {
        g_log_set_handler ("Cvc", G_LOG_LEVEL_DEBUG,
                           muted_log_handler, NULL);
        g_setenv ("G_MESSAGES_DEBUG", "all", TRUE);
    }

    filter->my_xid = gdk_x11_window_get_xid (gtk_widget_get_window (GTK_WIDGET (filter->managed_window)));

    g_debug ("Starting event filter for %s - 0x%lx", 
                 filter->we_are_backup_window ? "backup-locker." : "screensaver.",
                 filter->my_xid);
    gdk_window_add_filter (NULL, (GdkFilterFunc) xevent_filter, filter);

    if (filter->we_are_backup_window)
    {
        restack (filter, filter->pretty_xid, NULL);
    }
    else
    {
        restack (filter, 0, NULL);
    }
}

void
cs_gdk_event_filter_stop (CsGdkEventFilter *filter)
{
    gdk_window_remove_filter (NULL, (GdkFilterFunc) xevent_filter, filter);
}

CsGdkEventFilter *
cs_gdk_event_filter_new (GtkWidget *managed_window,
                         gulong    pretty_xid)
{
    CsGdkEventFilter *filter;

    filter = g_object_new (CS_TYPE_GDK_EVENT_FILTER,
                           NULL);

    filter->display = gdk_display_get_default ();
    filter->managed_window = g_object_ref (managed_window);
    filter->pretty_xid = pretty_xid;

    filter->we_are_backup_window = filter->pretty_xid != 0;

    return filter;
}
