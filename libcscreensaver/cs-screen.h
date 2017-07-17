
#ifndef __CS_SCREEN_H
#define __CS_SCREEN_H

#include <gtk/gtk.h>
#include <gdk/gdk.h>
#include <gdk/gdkx.h>

G_BEGIN_DECLS

#define CS_TYPE_SCREEN         (cs_screen_get_type ())
#define CS_SCREEN(o)           (G_TYPE_CHECK_INSTANCE_CAST ((o), CS_TYPE_SCREEN, CsScreen))
#define CS_SCREEN_CLASS(k)     (G_TYPE_CHECK_CLASS_CAST((k), CS_TYPE_SCREEN, CsScreenClass))
#define CS_IS_SCREEN(o)        (G_TYPE_CHECK_INSTANCE_TYPE ((o), CS_TYPE_SCREEN))
#define CS_IS_SCREEN_CLASS(k)  (G_TYPE_CHECK_CLASS_TYPE ((k), CS_TYPE_SCREEN))
#define CS_SCREEN_GET_CLASS(o) (G_TYPE_INSTANCE_GET_CLASS ((o), CS_TYPE_SCREEN, CsScreenClass))

typedef struct _CsMonitorInfo CsMonitorInfo;

struct _CsMonitorInfo
{
  int number;
  GdkRectangle rect;
  gboolean is_primary;
  XID output; /* The primary or first output for this crtc, None if no xrandr */
};

typedef struct
{
    GObject        obj;

    GdkRectangle rect;

    GdkScreen     *gdk_screen;

    CsMonitorInfo *monitor_infos;

    gint primary_monitor_index;
    gint n_monitor_infos;

    gulong monitors_changed_id;
    gulong screen_size_changed_id;
} CsScreen;

typedef struct
{
    GObjectClass    parent_class;
} CsScreenClass;

GType                        cs_screen_get_type           (void);

CsScreen                    *cs_screen_new (gboolean debug);

void                         cs_screen_get_monitor_geometry (CsScreen     *screen,
                                                             gint          monitor,
                                                             GdkRectangle *geometry);

void                         cs_screen_get_screen_geometry (CsScreen     *screen,
                                                            GdkRectangle *geometry);

gint                         cs_screen_get_primary_monitor (CsScreen *screen);

gint                         cs_screen_get_n_monitors (CsScreen *screen);

gint                         cs_screen_get_mouse_monitor (CsScreen *screen);

void                         cs_screen_nuke_focus (void);

G_END_DECLS

#endif /* __CS_SCREEN_H */
