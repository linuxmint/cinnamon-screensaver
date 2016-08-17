
#ifndef __CSCREENSAVER_GDK_EVENT_FILTER_H
#define __CSCREENSAVER_GDK_EVENT_FILTER_H

#include <gtk/gtk.h>
#include <gdk/gdk.h>

G_BEGIN_DECLS

#define CSCREENSAVER_TYPE_GDK_EVENT_FILTER         (cscreensaver_gdk_event_filter_get_type ())
#define CSCREENSAVER_GDK_EVENT_FILTER(o)           (G_TYPE_CHECK_INSTANCE_CAST ((o), CSCREENSAVER_TYPE_GDK_EVENT_FILTER, CScreensaverGdkEventFilter))
#define CSCREENSAVER_GDK_EVENT_FILTER_CLASS(k)     (G_TYPE_CHECK_CLASS_CAST((k), CSCREENSAVER_TYPE_GDK_EVENT_FILTER, CScreensaverGdkEventFilterClass))
#define CSCREENSAVER_IS_GDK_EVENT_FILTER(o)        (G_TYPE_CHECK_INSTANCE_TYPE ((o), CSCREENSAVER_TYPE_GDK_EVENT_FILTER))
#define CSCREENSAVER_IS_GDK_EVENT_FILTER_CLASS(k)  (G_TYPE_CHECK_CLASS_TYPE ((k), CSCREENSAVER_TYPE_GDK_EVENT_FILTER))
#define CSCREENSAVER_GDK_EVENT_FILTER_GET_CLASS(o) (G_TYPE_INSTANCE_GET_CLASS ((o), CSCREENSAVER_TYPE_GDK_EVENT_FILTER, CScreensaverGdkEventFilterClass))

typedef struct
{
        GObject        obj;

        GtkWidget     *stage;
        int            shape_event_base;
} CScreensaverGdkEventFilter;

typedef struct
{
        GObjectClass    parent_class;
} CScreensaverGdkEventFilterClass;

GType                        cscreensaver_gdk_event_filter_get_type           (void);

CScreensaverGdkEventFilter  *cscreensaver_gdk_event_filter_new (void);

void                         cscreensaver_gdk_event_filter_start (CScreensaverGdkEventFilter *filter,
                                                                  GtkWidget *stage);
void                         cscreensaver_gdk_event_filter_stop  (CScreensaverGdkEventFilter *filter);

G_END_DECLS

#endif /* __CSCREENSAVER_GDK_EVENT_FILTER_H */
