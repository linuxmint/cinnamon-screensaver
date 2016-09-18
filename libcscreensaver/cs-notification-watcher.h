
#ifndef __CS_NOTIFICATION_WATCHER_H
#define __CS_NOTIFICATION_WATCHER_H

#include <glib.h>
#include <glib-object.h>
#include <gio/gio.h>

G_BEGIN_DECLS

#define CS_TYPE_NOTIFICATION_WATCHER         (cs_notification_watcher_get_type ())
#define CS_NOTIFICATION_WATCHER(o)           (G_TYPE_CHECK_INSTANCE_CAST ((o), CS_TYPE_NOTIFICATION_WATCHER, CsNotificationWatcher))
#define CS_NOTIFICATION_WATCHER_CLASS(k)     (G_TYPE_CHECK_CLASS_CAST((k), CS_TYPE_NOTIFICATION_WATCHER, CsNotificationWatcherClass))
#define CS_IS_NOTIFICATION_WATCHER(o)        (G_TYPE_CHECK_INSTANCE_TYPE ((o), CS_TYPE_NOTIFICATION_WATCHER))
#define CS_IS_NOTIFICATION_WATCHER_CLASS(k)  (G_TYPE_CHECK_CLASS_TYPE ((k), CS_TYPE_NOTIFICATION_WATCHER))
#define CS_NOTIFICATION_WATCHER_GET_CLASS(o) (G_TYPE_INSTANCE_GET_CLASS ((o), CS_TYPE_NOTIFICATION_WATCHER, CsNotificationWatcherClass))

typedef struct
{
    GObject        obj;

    GDBusConnection *connection;
    gint             filter_id;
} CsNotificationWatcher;

typedef struct
{
    GObjectClass    parent_class;

    void (* notification_received) (CsNotificationWatcher *watcher, const gchar *sender);
} CsNotificationWatcherClass;

GType                        cs_notification_watcher_get_type           (void);

CsNotificationWatcher       *cs_notification_watcher_new (void);

G_END_DECLS

#endif /* __CS_NOTIFICATION_WATCHER_H */
