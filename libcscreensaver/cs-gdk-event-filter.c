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

G_DEFINE_TYPE (CsGdkEventFilter, cs_gdk_event_filter, G_TYPE_OBJECT);

static void clear_widget (CsGdkEventFilter *filter);

static void
unshape_window (CsGdkEventFilter *filter)
{
    g_return_if_fail (CS_IS_GDK_EVENT_FILTER (filter));

    gdk_window_shape_combine_region (gtk_widget_get_window (GTK_WIDGET (filter->stage)),
                                     NULL,
                                     0,
                                     0);
}

static void
raise_stage (CsGdkEventFilter *filter)
{
    GdkWindow *win;

    g_return_if_fail (CS_IS_GDK_EVENT_FILTER (filter));

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
cs_gdk_event_filter_xevent (CsGdkEventFilter *filter,
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
          {
#ifdef HAVE_SHAPE_EXT
            if (ev->xany.type == (filter->shape_event_base + ShapeNotify)) {
                unshape_window (filter);
            }
#endif
        break;
          }
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
select_shape_events (CsGdkEventFilter *filter)
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
               CsGdkEventFilter *filter)
{
    cs_gdk_event_filter_xevent (filter, xevent);

    return GDK_FILTER_CONTINUE;
}

static void
cs_gdk_event_filter_init (CsGdkEventFilter *filter)
{
    filter->shape_event_base = 0;
    filter->stage = NULL;
}

static void
cs_gdk_event_filter_finalize (GObject *object)
{
    CsGdkEventFilter *filter;

    g_return_if_fail (object != NULL);
    g_return_if_fail (CS_IS_GDK_EVENT_FILTER (object));

    filter = CS_GDK_EVENT_FILTER (object);

    cs_gdk_event_filter_stop (filter);

    G_OBJECT_CLASS (cs_gdk_event_filter_parent_class)->finalize (object);
}

static void
cs_gdk_event_filter_class_init (CsGdkEventFilterClass *klass)
{
        GObjectClass   *object_class = G_OBJECT_CLASS (klass);

        object_class->finalize     = cs_gdk_event_filter_finalize;
}

static void
on_widget_finalized (CsGdkEventFilter *filter,
                     GtkWidget                  *stage)
{
    cs_gdk_event_filter_stop (filter);
    clear_widget (filter);
}

static void
clear_widget (CsGdkEventFilter *filter)
{
    if (filter->stage == NULL)
        return;

    g_object_weak_unref (G_OBJECT (filter->stage), (GWeakNotify) on_widget_finalized, filter);
    filter->stage = NULL;
}

void
cs_gdk_event_filter_start (CsGdkEventFilter *filter,
                           GtkWidget        *stage)
{
    g_return_if_fail(stage != NULL);

    filter->stage = stage;

    g_object_weak_ref (G_OBJECT (stage), (GWeakNotify) on_widget_finalized, filter);

    select_popup_events ();
    select_shape_events (filter);

    gdk_window_add_filter (NULL, (GdkFilterFunc) xevent_filter, filter);
}

void
cs_gdk_event_filter_stop (CsGdkEventFilter *filter)
{
    gdk_window_remove_filter (NULL, (GdkFilterFunc) xevent_filter, filter);
    clear_widget (filter);
}

CsGdkEventFilter *
cs_gdk_event_filter_new (void)
{
    GObject     *result;

    result = g_object_new (CS_TYPE_GDK_EVENT_FILTER,
                           NULL);

    return CS_GDK_EVENT_FILTER (result);
}

