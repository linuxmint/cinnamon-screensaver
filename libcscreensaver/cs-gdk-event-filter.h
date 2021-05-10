
#ifndef __CS_GDK_EVENT_FILTER_H
#define __CS_GDK_EVENT_FILTER_H

#include <gtk/gtk.h>
#include <gdk/gdk.h>

G_BEGIN_DECLS

#define CS_TYPE_GDK_EVENT_FILTER         (cs_gdk_event_filter_get_type ())
#define CS_GDK_EVENT_FILTER(o)           (G_TYPE_CHECK_INSTANCE_CAST ((o), CS_TYPE_GDK_EVENT_FILTER, CsGdkEventFilter))
#define CS_GDK_EVENT_FILTER_CLASS(k)     (G_TYPE_CHECK_CLASS_CAST((k), CS_TYPE_GDK_EVENT_FILTER, CsGdkEventFilterClass))
#define CS_IS_GDK_EVENT_FILTER(o)        (G_TYPE_CHECK_INSTANCE_TYPE ((o), CS_TYPE_GDK_EVENT_FILTER))
#define CS_IS_GDK_EVENT_FILTER_CLASS(k)  (G_TYPE_CHECK_CLASS_TYPE ((k), CS_TYPE_GDK_EVENT_FILTER))
#define CS_GDK_EVENT_FILTER_GET_CLASS(o) (G_TYPE_INSTANCE_GET_CLASS ((o), CS_TYPE_GDK_EVENT_FILTER, CsGdkEventFilterClass))

typedef struct
{
    GObject        obj;

    GdkDisplay    *display;
    GtkWidget     *managed_window;

    /* Using XID/Window here would complicate introspection. */
    gulong         pretty_xid;

    int            shape_event_base;
} CsGdkEventFilter;

typedef struct
{
    GObjectClass    parent_class;
} CsGdkEventFilterClass;

GType                        cs_gdk_event_filter_get_type           (void);

CsGdkEventFilter            *cs_gdk_event_filter_new (GtkWidget *managed_window, gulong pretty_xid);

void                         cs_gdk_event_filter_start (CsGdkEventFilter *filter);

void                         cs_gdk_event_filter_stop  (CsGdkEventFilter *filter);

G_END_DECLS

#endif /* __CS_GDK_EVENT_FILTER_H */
