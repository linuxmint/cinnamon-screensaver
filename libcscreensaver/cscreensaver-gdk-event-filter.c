#include "cscreensaver-gdk-event-filter.h"

#ifdef HAVE_SHAPE_EXT
#include <X11/extensions/shape.h>
#endif
#include <gtk/gtkx.h>
#include <string.h>

G_DEFINE_TYPE (CScreensaverGdkEventFilter, cscreensaver_gdk_event_filter, G_TYPE_OBJECT);

static void clear_widget (CScreensaverGdkEventFilter *filter);

static void
unshape_window (CScreensaverGdkEventFilter *filter)
{
    g_return_if_fail (CSCREENSAVER_IS_GDK_EVENT_FILTER (filter));

    gdk_window_shape_combine_region (gtk_widget_get_window (GTK_WIDGET (filter->stage)),
                                     NULL,
                                     0,
                                     0);
}

static void
raise_stage (CScreensaverGdkEventFilter *filter)
{
    GdkWindow *win;

    g_return_if_fail (CSCREENSAVER_IS_GDK_EVENT_FILTER (filter));

    win = gtk_widget_get_window (GTK_WIDGET (filter->stage));

    gdk_window_raise (win);
}

static gboolean
x11_window_is_ours (Window window)
{
    GdkWindow *gwindow;
    gboolean   ret;

    ret = FALSE;

    gwindow = gdk_x11_window_lookup_for_display (gdk_display_get_default (), window);
    if (gwindow && (window != GDK_ROOT_WINDOW ())) {
            ret = TRUE;
    }

    return ret;
}

static void
cscreensaver_gdk_event_filter_xevent (CScreensaverGdkEventFilter *filter,
                                      GdkXEvent *xevent)
{
    XEvent *ev;

    ev = xevent;

    /* MapNotify is used to tell us when new windows are mapped.
       ConfigureNofify is used to tell us when windows are raised. */
    switch (ev->xany.type) {
        case MapNotify:
            {
                XMapEvent *xme = &ev->xmap;

                if (! x11_window_is_ours (xme->window)) {
                    raise_stage (filter);
                }

                break;
            }
        case ConfigureNotify:
            {
                XConfigureEvent *xce = &ev->xconfigure;

                if (! x11_window_is_ours (xce->window)) {
                    raise_stage (filter);
                }

                break;
        }
    default:
#ifdef HAVE_SHAPE_EXT
        if (ev->xany.type == (window->priv->shape_event_base + ShapeNotify)) {
            unshape_window (window);
        }
#endif
        break;
    }
}

static void
select_popup_events (void)
{
        XWindowAttributes attr;
        unsigned long     events;

        gdk_error_trap_push ();

        memset (&attr, 0, sizeof (attr));
        XGetWindowAttributes (GDK_DISPLAY_XDISPLAY (gdk_display_get_default ()), GDK_ROOT_WINDOW (), &attr);

        events = SubstructureNotifyMask | attr.your_event_mask;
        XSelectInput (GDK_DISPLAY_XDISPLAY (gdk_display_get_default ()), GDK_ROOT_WINDOW (), events);

        gdk_error_trap_pop_ignored ();
}

static void
select_shape_events (CScreensaverGdkEventFilter *filter)
{
#ifdef HAVE_SHAPE_EXT
        unsigned long events;
        int           shape_error_base;

        gdk_error_trap_push ();

        if (XShapeQueryExtension (GDK_DISPLAY_XDISPLAY (gdk_display_get_default ()), &filter->shape_event_base, &shape_error_base)) {
            events = ShapeNotifyMask;

            XShapeSelectInput (GDK_DISPLAY_XDISPLAY (gdk_display_get_default ()),
                               GDK_WINDOW_XID (gtk_widget_get_window (GTK_WIDGET (filter->stage))),
                               events);
        }

        gdk_error_trap_pop_ignored ();
#endif
}


static GdkFilterReturn
xevent_filter (GdkXEvent *xevent,
               GdkEvent  *event,
               CScreensaverGdkEventFilter *filter)
{
        cscreensaver_gdk_event_filter_xevent (filter, xevent);

        return GDK_FILTER_CONTINUE;
}

static void
cscreensaver_gdk_event_filter_init (CScreensaverGdkEventFilter *filter)
{
    filter->shape_event_base = 0;
    filter->stage = NULL;
}

static void
cscreensaver_gdk_event_filter_finalize (GObject *object)
{
        CScreensaverGdkEventFilter *filter;

        g_return_if_fail (object != NULL);
        g_return_if_fail (CSCREENSAVER_IS_GDK_EVENT_FILTER (object));

        filter = CSCREENSAVER_GDK_EVENT_FILTER (object);

        cscreensaver_gdk_event_filter_stop (filter);

        G_OBJECT_CLASS (cscreensaver_gdk_event_filter_parent_class)->finalize (object);
}

static void
cscreensaver_gdk_event_filter_class_init (CScreensaverGdkEventFilterClass *klass)
{
        GObjectClass   *object_class = G_OBJECT_CLASS (klass);

        object_class->finalize     = cscreensaver_gdk_event_filter_finalize;
}

static void
on_widget_finalized (CScreensaverGdkEventFilter *filter,
                     GtkWidget                  *stage)
{
    cscreensaver_gdk_event_filter_stop (filter);
    clear_widget (filter);
}

static void
clear_widget (CScreensaverGdkEventFilter *filter)
{
    if (filter->stage == NULL)
        return;

    g_object_weak_unref (G_OBJECT (filter->stage), (GWeakNotify) on_widget_finalized, filter);
    filter->stage = NULL;
}

void
cscreensaver_gdk_event_filter_start (CScreensaverGdkEventFilter *filter,
                                     GtkWidget                  *stage)
{
    g_return_if_fail(stage != NULL);

    filter->stage = stage;

    g_object_weak_ref (G_OBJECT (stage), (GWeakNotify) on_widget_finalized, filter);

    select_popup_events ();
    select_shape_events (filter);

    gdk_window_add_filter (NULL, (GdkFilterFunc) xevent_filter, filter);
}

void
cscreensaver_gdk_event_filter_stop (CScreensaverGdkEventFilter *filter)
{
    gdk_window_remove_filter (NULL, (GdkFilterFunc) xevent_filter, filter);
    clear_widget (filter);
}

CScreensaverGdkEventFilter *
cscreensaver_gdk_event_filter_new (void)
{
        GObject     *result;

        result = g_object_new (CSCREENSAVER_TYPE_GDK_EVENT_FILTER,
                               NULL);

        return CSCREENSAVER_GDK_EVENT_FILTER (result);
}

