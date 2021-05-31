/*
 * CsGdkEventFilter: An introspectable C class that establishes an event
 * trap for the screensaver.  It watches for any X events that could result
 * in other windows showing up over our Stage, and ensures the Stage stays on
 * top.  This will only ever be other override-redirect (non-managed) X windows,
 * such as native Firefox or Chrome notification popups.
 *
 */

#include "cs-gdk-event-filter.h"
#include "config.h"

#ifdef HAVE_SHAPE_EXT
#include <X11/extensions/shape.h>
#endif
#include <gtk/gtkx.h>
#include <string.h>

enum {
        XSCREEN_SIZE,
        LAST_SIGNAL
};

static guint signals [LAST_SIGNAL] = { 0, };

G_DEFINE_TYPE (CsGdkEventFilter, cs_gdk_event_filter, G_TYPE_OBJECT);

static gboolean
we_are_fallback_window (CsGdkEventFilter *filter)
{
    return filter->pretty_xid > 0;
}

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
raise_managed_window (CsGdkEventFilter *filter)
{
    GdkWindow *win;

    g_return_if_fail (CS_IS_GDK_EVENT_FILTER (filter));

    win = gtk_widget_get_window (GTK_WIDGET (filter->managed_window));

    gdk_window_raise (win);
}

static gboolean
x11_window_is_ours (CsGdkEventFilter *filter, Window window)
{
    GdkWindow *gwindow;
    gboolean   ret;

    ret = FALSE;

    gwindow = gdk_x11_window_lookup_for_display (filter->display, window);
    if (gwindow && (window != GDK_ROOT_WINDOW ())) {
            ret = TRUE;
    }

    return ret;
}

static gboolean
is_pretty_window (CsGdkEventFilter *filter,
                  Window            window)
{
    if (filter->pretty_xid == 0)
    {
        return FALSE;
    }

    return window == filter->pretty_xid;
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

            if (ignore_fcitx_input_window (filter, xme->window) && we_are_fallback_window (filter))
            {
                break;
            }

            if (! x11_window_is_ours (filter, xme->window) && !is_pretty_window (filter, xme->window)) {
                raise_managed_window (filter);
            }

            break;
          }
        case ConfigureNotify:
          {
            XConfigureEvent *xce = &ev->xconfigure;

            if (ignore_fcitx_input_window (filter, xce->window) && we_are_fallback_window (filter))
            {
                break;
            }

            if (! x11_window_is_ours (filter, xce->window) && !is_pretty_window (filter, xce->window)) {
                raise_managed_window (filter);
            }

            // If the reported window is the root window, and we're the backup window (we have a pretty
            // xid) then signal to resize to the root window (screen).
            // if (xce->window == GDK_ROOT_WINDOW () && filter->pretty_xid > 0)
            if (xce->window == GDK_ROOT_WINDOW ())
            {
                // Screen size may have changed, tell the fallback
                g_signal_emit (filter, signals[XSCREEN_SIZE], 0);
            }
          }
        default:
          {
#ifdef HAVE_SHAPE_EXT
            if (ev->xany.type == (filter->shape_event_base + ShapeNotify)) {
                unshape_window (filter);
            }
#endif
            // return GDK_FILTER_REMOVE;
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
}

void
cs_gdk_event_filter_start (CsGdkEventFilter *filter)
{
    select_popup_events (filter);
    select_shape_events (filter);

    gdk_window_add_filter (NULL, (GdkFilterFunc) xevent_filter, filter);
}

void
cs_gdk_event_filter_stop (CsGdkEventFilter *filter)
{
    gdk_window_remove_filter (NULL, (GdkFilterFunc) xevent_filter, filter);
}

CsGdkEventFilter *
cs_gdk_event_filter_new (GtkWidget *managed_window,
                         gulong     pretty_xid)
{
    CsGdkEventFilter *filter;

    filter = g_object_new (CS_TYPE_GDK_EVENT_FILTER,
                           NULL);

    filter->display = gdk_display_get_default ();
    filter->managed_window = g_object_ref (managed_window);
    filter->pretty_xid = pretty_xid;

    return filter;
}

