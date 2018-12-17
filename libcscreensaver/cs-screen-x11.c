/*
 * CsScreen: An introspectable C class that establishes an event
 * trap for the screensaver.  It watches for any X events that could result
 * in other windows showing up over our Stage, and ensures the Stage stays on
 * top.  This will only ever be other override-redirect (non-managed) X windows,
 * such as native Firefox or Chrome notification popups.
 *
 */

#include "config.h"
#include "cs-screen.h"

#include <string.h>

#include <X11/Xlib.h>
#include <X11/Xutil.h>

#ifdef HAVE_SOLARIS_XINERAMA
#include <X11/extensions/xinerama.h>
#endif
#ifdef HAVE_XFREE_XINERAMA
#include <X11/extensions/Xinerama.h>
#endif
#ifdef HAVE_RANDR
#include <X11/extensions/Xrandr.h>
#endif

enum {
        SCREEN_MONITORS_CHANGED,
        SCREEN_SIZE_CHANGED,
        LAST_SIGNAL
};

static guint signals [LAST_SIGNAL] = { 0, };

G_DEFINE_TYPE (CsScreen, cs_screen, G_TYPE_OBJECT);

static gboolean debug_mode = FALSE;
#define DEBUG(...) if (debug_mode) g_printerr (__VA_ARGS__)

#define cs_XFree(p) do { if ((p)) XFree ((p)); } while (0)

#define PRIMARY_MONITOR 0

static gboolean
cs_rectangle_equal (const GdkRectangle *src1,
                    const GdkRectangle *src2)
{
    return ((src1->x == src2->x) &&
            (src1->y == src2->y) &&
            (src1->width == src2->width) &&
            (src1->height == src2->height));
}

/* The list of monitors reported by the windowing system might include
 * mirrored monitors with identical bounds. Since mirrored monitors
 * shouldn't be treated as separate monitors for most purposes, we
 * filter them out here. (We ignore the possibility of partially
 * overlapping monitors because they are rare and it's hard to come
 * up with any sensible interpretation.)
 */
static void
filter_mirrored_monitors (CsScreen *screen)
{
    int i, j;

    /* Currently always true and simplifies things */
    g_assert (screen->primary_monitor_index == 0);

    for (i = 1; i < screen->n_monitor_infos; i++)
    {
        /* In case we've filtered previous monitors */
        screen->monitor_infos[i].number = i;

        for (j = 0; j < i; j++)
        {
            if (cs_rectangle_equal (&screen->monitor_infos[i].rect,
                                    &screen->monitor_infos[j].rect))
            {
                memmove (&screen->monitor_infos[i],
                         &screen->monitor_infos[i + 1],
                         (screen->n_monitor_infos - i - 1) * sizeof (CsMonitorInfo));
                screen->n_monitor_infos--;
                i--;

                continue;
            }
        }
    }
}

#ifdef HAVE_RANDR
static CsMonitorInfo *
find_monitor_with_rect (CsScreen *screen, int x, int y, int w, int h)
{
    CsMonitorInfo *info;
    int i;

    for (i = 0; i < screen->n_monitor_infos; i++)
    {
        info = &screen->monitor_infos[i];
        if (x == info->rect.x &&
            y == info->rect.y &&
            w == info->rect.width &&
            h == info->rect.height)
        {
            return info;
        }
    }

  return NULL;
}

/* In the case of multiple outputs of a single crtc (mirroring), we consider one of the
 * outputs the "main". This is the one we consider "owning" the windows, so if
 * the mirroring is changed to a dual monitor setup then the windows are moved to the
 * crtc that now has that main output. If one of the outputs is the primary that is
 * always the main, otherwise we just use the first.
 */
static XID
find_main_output_for_crtc (XRRScreenResources *resources,
                           XRRCrtcInfo        *crtc,
                           Display            *xdisplay,
                           XID                 xroot)
{
    XRROutputInfo *output;
    RROutput primary_output;
    int i;
    XID res;

    primary_output = XRRGetOutputPrimary (xdisplay, xroot);

    res = None;
    for (i = 0; i < crtc->noutput; i++)
    {
        output = XRRGetOutputInfo (xdisplay, resources, crtc->outputs[i]);
        if (output->connection != RR_Disconnected &&
            (res == None || crtc->outputs[i] == primary_output))
        {
            res = crtc->outputs[i];
        }

        XRRFreeOutputInfo (output);
    }

    return res;
}
#endif

static void
apply_scale_factor (CsMonitorInfo *infos,
                    gint           n_infos,
                    gint           factor)
{
    gint i;

    for (i = 0; i < n_infos; i++)
    {
        infos[i].rect.x /= factor;
        infos[i].rect.y /= factor;
        infos[i].rect.width /= factor;
        infos[i].rect.height /= factor;

        DEBUG ("Scale factor of %d applied.  Monitor %d is %d,%d %d x %d\n",
               factor,
               infos[i].number,
               infos[i].rect.x,
               infos[i].rect.y,
               infos[i].rect.width,
               infos[i].rect.height);
    }
}

#define MONITOR_WIDTH_THRESHOLD 1200
#define MONITOR_HEIGHT_THRESHOLD 1000

static gboolean
get_low_res_mode (CsScreen      *screen,
                  CsMonitorInfo *infos,
                  gint           n_infos)
{
    gint i;
    gint smallest_width, smallest_height;

    smallest_width = smallest_height = G_MAXINT;

    for (i = 0; i < n_infos; i++)
    {
        smallest_width = MIN (infos[i].rect.width, smallest_width);
        smallest_height = MIN (infos[i].rect.height, smallest_height);
    }

    screen->smallest_width = smallest_width;
    screen->smallest_height = smallest_height;

    if (smallest_width < MONITOR_WIDTH_THRESHOLD || smallest_height < MONITOR_HEIGHT_THRESHOLD)
    {
        DEBUG ("Narrowest monitor width after scaling (%dx%d) is below threshold of %dx%d, applying low-res mode\n",
               smallest_width,
               smallest_height,
               MONITOR_WIDTH_THRESHOLD,
               MONITOR_HEIGHT_THRESHOLD);

        return TRUE;
    }

    return FALSE;
}

static void
reload_monitor_infos (CsScreen *screen)
{
    GdkDisplay *gdk_display;
    Display *xdisplay;
    Window xroot;

    gdk_display = gdk_screen_get_display (screen->gdk_screen);
    xdisplay = gdk_x11_display_get_xdisplay (gdk_display);

    xroot = gdk_x11_window_get_xid (gdk_screen_get_root_window (screen->gdk_screen));

    /* Any previous screen->monitor_infos is freed by the caller */

    screen->monitor_infos = NULL;
    screen->n_monitor_infos = 0;

    /* Xinerama doesn't have a concept of primary monitor, however XRandR
     * does. However, the XRandR xinerama compat code always sorts the
     * primary output first, so we rely on that here. We could use the
     * native XRandR calls instead of xinerama, but that would be
     * slightly problematic for _NET_WM_FULLSCREEN_MONITORS support, as
     * that is defined in terms of xinerama monitor indexes.
     * So, since we don't need anything in xrandr except the primary
     * we can keep using xinerama and use the first monitor as the
     * primary.
     */

    screen->primary_monitor_index = PRIMARY_MONITOR;


#ifdef HAVE_XFREE_XINERAMA
    if (screen->n_monitor_infos == 0 &&
        XineramaIsActive (xdisplay))
    {
        XineramaScreenInfo *infos;
        int n_infos;
        int i;

        n_infos = 0;
        infos = XineramaQueryScreens (xdisplay, &n_infos);

        DEBUG ("Found %d Xinerama screens on display %s\n",
               n_infos, gdk_display_get_name (gdk_display));

        if (n_infos > 0)
        {
            screen->monitor_infos = g_new0 (CsMonitorInfo, n_infos);
            screen->n_monitor_infos = n_infos;

            i = 0;
            while (i < n_infos)
            {
                screen->monitor_infos[i].number = infos[i].screen_number;
                screen->monitor_infos[i].rect.x = infos[i].x_org;
                screen->monitor_infos[i].rect.y = infos[i].y_org;
                screen->monitor_infos[i].rect.width = infos[i].width;
                screen->monitor_infos[i].rect.height = infos[i].height;

                DEBUG ("Monitor %d is %d,%d %d x %d\n",
                       screen->monitor_infos[i].number,
                       screen->monitor_infos[i].rect.x,
                       screen->monitor_infos[i].rect.y,
                       screen->monitor_infos[i].rect.width,
                       screen->monitor_infos[i].rect.height);

                ++i;
            }
        }

        cs_XFree (infos);

#ifdef HAVE_RANDR
    {
        XRRScreenResources *resources;

        resources = XRRGetScreenResourcesCurrent (xdisplay, xroot);

        if (resources)
        {
            for (i = 0; i < resources->ncrtc; i++)
            {
                XRRCrtcInfo *crtc;
                CsMonitorInfo *info;

                crtc = XRRGetCrtcInfo (xdisplay, resources, resources->crtcs[i]);
                info = find_monitor_with_rect (screen, crtc->x, crtc->y, (int)crtc->width, (int)crtc->height);

                if (info)
                {
                  info->output = find_main_output_for_crtc (resources, crtc, xdisplay, xroot);
                }

                XRRFreeCrtcInfo (crtc);
            }

            XRRFreeScreenResources (resources);
        }
    }
#endif
    }
    else if (screen->n_monitor_infos > 0)
    {
        DEBUG ("No XFree86 Xinerama extension or XFree86 Xinerama inactive on display %s\n",
               gdk_display_get_name (gdk_display));
    }
#else
    DEBUG ("Muffin compiled without XFree86 Xinerama support\n");
#endif /* HAVE_XFREE_XINERAMA */

#ifdef HAVE_SOLARIS_XINERAMA
    /* This code from GDK, Copyright (C) 2002 Sun Microsystems */
    if (screen->n_monitor_infos == 0 &&
        XineramaGetState (xdisplay,
                          gdk_screen_get_number (screen->gdk_screen)))
    {
        XRectangle monitors[MAXFRAMEBUFFERS];
        unsigned char hints[16];
        int result;
        int n_monitors;
        int i;

        n_monitors = 0;
        result = XineramaGetInfo (xdisplay,
                                  gdk_screen_get_number (screen->gdk_screen),
                                  monitors, hints,
                                  &n_monitors);
        /* Yes I know it should be Success but the current implementation
         * returns the num of monitor
         */
        if (result > 0)
        {
            g_assert (n_monitors > 0);

            screen->monitor_infos = g_new0 (CsMonitorInfo, n_monitors);
            screen->n_monitor_infos = n_monitors;

            i = 0;
            while (i < n_monitors)
            {
                screen->monitor_infos[i].number = i;
                screen->monitor_infos[i].rect.x = monitors[i].x;
                screen->monitor_infos[i].rect.y = monitors[i].y;
                screen->monitor_infos[i].rect.width = monitors[i].width;
                screen->monitor_infos[i].rect.height = monitors[i].height;

                DEBUG ("Monitor %d is %d,%d %d x %d\n",
                       screen->monitor_infos[i].number,
                       screen->monitor_infos[i].rect.x,
                       screen->monitor_infos[i].rect.y,
                       screen->monitor_infos[i].rect.width,
                       screen->monitor_infos[i].rect.height);
                ++i;
            }
        }
    }
    else if (screen->n_monitor_infos == 0)
    {
        DEBUG ("No Solaris Xinerama extension or Solaris Xinerama inactive on display %s\n",
               gdk_display_get_name (gdk_display));
    }
#else
    DEBUG ("Cinnamon Screensaver compiled without Solaris Xinerama support\n");
#endif /* HAVE_SOLARIS_XINERAMA */

    /* If no Xinerama, fill in the single screen info so
     * we can use the field unconditionally
    */
    if (screen->n_monitor_infos == 0)
    {
        DEBUG ("No Xinerama screens, using default screen info\n");

        screen->monitor_infos = g_new0 (CsMonitorInfo, 1);
        screen->n_monitor_infos = 1;

        screen->monitor_infos[0].number = 0;
        screen->monitor_infos[0].rect = screen->rect;
    }

    filter_mirrored_monitors (screen);

    screen->monitor_infos[screen->primary_monitor_index].is_primary = TRUE;

    apply_scale_factor (screen->monitor_infos,
                        screen->n_monitor_infos,
                        gdk_screen_get_monitor_scale_factor (screen->gdk_screen, PRIMARY_MONITOR));

    screen->low_res = get_low_res_mode (screen,
                                        screen->monitor_infos,
                                        screen->n_monitor_infos);

    g_assert (screen->n_monitor_infos > 0);
    g_assert (screen->monitor_infos != NULL);
}

static void
reload_screen_info (CsScreen *screen)
{
    screen->rect.x = screen->rect.y = 0;
    screen->rect.width = gdk_screen_get_width (screen->gdk_screen);
    screen->rect.height = gdk_screen_get_height (screen->gdk_screen);
}

static void
on_monitors_changed (GdkScreen *gdk_screen, gpointer user_data)
{
    CsMonitorInfo *old_monitor_infos;
    CsScreen *screen;

    screen = CS_SCREEN (user_data);

    reload_screen_info (screen);
    g_signal_emit (screen, signals[SCREEN_SIZE_CHANGED], 0);

    gdk_flush ();

    DEBUG ("CsScreen received 'monitors-changed' signal from GdkScreen\n");

    old_monitor_infos = screen->monitor_infos;
    reload_monitor_infos (screen);

    g_free (old_monitor_infos);

    g_signal_emit (screen, signals[SCREEN_MONITORS_CHANGED], 0);
}

static void
on_screen_changed (GdkScreen *gdk_screen, gpointer user_data)
{
    CsScreen *screen;

    screen = CS_SCREEN (user_data);

    DEBUG ("CsScreen received 'size-changed' signal from GdkScreen\n");

    reload_screen_info (screen);
    g_signal_emit (screen, signals[SCREEN_SIZE_CHANGED], 0);
}

static void
cs_screen_init (CsScreen *screen)
{
    screen->gdk_screen = gdk_screen_get_default ();

    screen->monitors_changed_id = g_signal_connect (screen->gdk_screen, "monitors-changed", G_CALLBACK (on_monitors_changed), screen);
    screen->screen_size_changed_id = g_signal_connect (screen->gdk_screen, "size-changed", G_CALLBACK (on_screen_changed), screen);

    reload_screen_info (screen);
    reload_monitor_infos (screen);
}

static void
cs_screen_finalize (GObject *object)
{
    CsScreen *screen;

    g_return_if_fail (object != NULL);
    g_return_if_fail (CS_IS_SCREEN (object));

    screen = CS_SCREEN (object);

    if (screen->monitor_infos)
    {
        g_free (screen->monitor_infos);
    }

    DEBUG ("CsScreen finalize\n");

    G_OBJECT_CLASS (cs_screen_parent_class)->finalize (object);
}

static void
cs_screen_dispose (GObject *object)
{
    CsScreen *screen;

    g_return_if_fail (object != NULL);
    g_return_if_fail (CS_IS_SCREEN (object));

    screen = CS_SCREEN (object);

    if (screen->monitors_changed_id > 0)
    {
        g_signal_handler_disconnect (screen->gdk_screen, screen->monitors_changed_id);
        screen->monitors_changed_id = 0;
    }

    if (screen->screen_size_changed_id > 0)
    {
        g_signal_handler_disconnect (screen->gdk_screen, screen->screen_size_changed_id);
        screen->screen_size_changed_id = 0;
    }

    DEBUG ("CsScreen dispose\n");

    G_OBJECT_CLASS (cs_screen_parent_class)->dispose (object);
}

static void
cs_screen_class_init (CsScreenClass *klass)
{
    GObjectClass *object_class = G_OBJECT_CLASS (klass);

    object_class->finalize = cs_screen_finalize;
    object_class->dispose = cs_screen_dispose;

    signals[SCREEN_MONITORS_CHANGED] = g_signal_new ("monitors-changed",
                                              G_TYPE_FROM_CLASS (object_class),
                                              G_SIGNAL_RUN_LAST,
                                              0,
                                              NULL, NULL, NULL,
                                              G_TYPE_NONE, 0);

    signals[SCREEN_SIZE_CHANGED] = g_signal_new ("size-changed",
                                            G_TYPE_FROM_CLASS (object_class),
                                            G_SIGNAL_RUN_LAST,
                                            0,
                                            NULL, NULL, NULL,
                                            G_TYPE_NONE, 0);
}

CsScreen *
cs_screen_new (gboolean debug)
{
    GObject     *result;

    debug_mode = debug;

    result = g_object_new (CS_TYPE_SCREEN, NULL);

    return CS_SCREEN (result);
}

/**
 * cs_screen_get_monitor_geometry:
 * @screen: a #CsScreen
 * @monitor: the monitor number
 * @geometry: (out): location to store the monitor geometry
 *
 * Stores the location and size of the indicated monitor in @geometry.
 */
void
cs_screen_get_monitor_geometry (CsScreen     *screen,
                                gint          monitor,
                                GdkRectangle *geometry)
{
    g_return_if_fail (CS_IS_SCREEN (screen));
    g_return_if_fail (monitor >= 0 && monitor < screen->n_monitor_infos);
    g_return_if_fail (geometry != NULL);

    geometry->x = screen->monitor_infos[monitor].rect.x;
    geometry->y = screen->monitor_infos[monitor].rect.y;
    geometry->width = screen->monitor_infos[monitor].rect.width;
    geometry->height = screen->monitor_infos[monitor].rect.height;
}

/**
 * cs_screen_get_screen_geometry:
 * @screen: a #CsScreen
 * @geometry: (out): location to store the screen geometry
 *
 * Stores the location and size of the screen in @geometry.
 */
void
cs_screen_get_screen_geometry (CsScreen     *screen,
                               GdkRectangle *geometry)
{
    g_return_if_fail (CS_IS_SCREEN (screen));
    g_return_if_fail (geometry != NULL);

    geometry->x = screen->rect.x;
    geometry->y = screen->rect.y;
    geometry->width = screen->rect.width;
    geometry->height = screen->rect.height;
}

/**
 * cs_screen_get_primary_monitor:
 * @screen: a #CsScreen
 *
 * Gets the index of the primary monitor on this @screen.
 *
 * Return value: a monitor index
 */
gint
cs_screen_get_primary_monitor (CsScreen *screen)
{
    g_return_val_if_fail (CS_IS_SCREEN (screen), 0);

    return screen->primary_monitor_index;
}

/**
 * cs_screen_get_n_monitors:
 * @screen: a #CsScreen
 *
 * Gets the number of monitors that are joined together to form @screen.
 *
 * Return value: the number of monitors
 */
gint
cs_screen_get_n_monitors (CsScreen *screen)
{
    g_return_val_if_fail (CS_IS_SCREEN (screen), 0);

    return screen->n_monitor_infos;
}

/**
 * cs_screen_get_mouse_monitor:
 * @screen: a #CsScreen
 *
 * Gets the index of the monitor that the mouse pointer currently
 * occupies.
 *
 * Return value: the monitor index for the pointer
 */
gint
cs_screen_get_mouse_monitor (CsScreen *screen)
{
    GdkDisplay *gdk_display;

    Window xroot, root_return, child_return;
    int root_x_return, root_y_return;
    int win_x_return, win_y_return;
    unsigned int mask_return;
    gint scale_factor;

    gint i;
    gint ret = 0;

    g_return_val_if_fail (CS_IS_SCREEN (screen), 0);

    gdk_display = gdk_screen_get_display (screen->gdk_screen);
    xroot = gdk_x11_window_get_xid (gdk_screen_get_root_window (screen->gdk_screen));

    gdk_error_trap_push ();
    XQueryPointer (gdk_x11_display_get_xdisplay (gdk_display),
                   xroot,
                   &root_return,
                   &child_return,
                   &root_x_return,
                   &root_y_return,
                   &win_x_return,
                   &win_y_return,
                   &mask_return);
    gdk_error_trap_pop_ignored ();

    scale_factor = gdk_screen_get_monitor_scale_factor (screen->gdk_screen, 0);
    root_x_return /= scale_factor;
    root_y_return /= scale_factor;

    for (i = 0; i < screen->n_monitor_infos; i++)
    {
        GdkRectangle iter = screen->monitor_infos[i].rect;

        if (root_x_return >= iter.x && root_x_return <= iter.x + iter.width &&
            root_y_return >= iter.y && root_y_return <= iter.y + iter.height)
        {
            ret = i;
            break;
        }
    }

    return ret;
}

/**
 * cs_screen_get_low_res_mode:
 * @screen: a #CsScreen
 *
 * Gets whether or not one of our monitors falls below the low res threshold (1200 wide).
 * This lets us display certain things at smaller sizes to prevent truncating of images, etc.
 *
 * Returns: Whether or not to use low res mode.
 */
gboolean
cs_screen_get_low_res_mode (CsScreen *screen)
{
    g_return_val_if_fail (CS_IS_SCREEN (screen), FALSE);

    return screen->low_res;
}

/**
 * cs_screen_get_smallest_monitor_sizes:
 * @screen: a #CsScreen
 * @width: (out): width of the smallest monitor
 * @height: (out): height of the smallest monitor
 *
 * Gets whether or not one of our monitors falls below the low res threshold (1200 wide).
 * This lets us display certain things at smaller sizes to prevent truncating of images, etc.
 *
 * Returns: Whether or not to use low res mode.
 */
void
cs_screen_get_smallest_monitor_sizes (CsScreen *screen,
                                      gint     *width,
                                      gint     *height)
{
    g_return_if_fail (CS_IS_SCREEN (screen));

    if (width != NULL)
    {
        *width = screen->smallest_width;
    }

    if (height != NULL)
    {
        *height = screen->smallest_height;
    }
}

/**
 * cs_screen_reset_screensaver:
 *
 * Resets the screensaver idle timer. If called when the screensaver is active
 * it will stop it.
 *
 */
void
cs_screen_reset_screensaver (void)
{
    XResetScreenSaver (GDK_DISPLAY_XDISPLAY (gdk_display_get_default ()));
}

void
cs_screen_nuke_focus (void)
{
    Window focus = 0;
    int    rev = 0;

    DEBUG ("Nuking focus\n");

    gdk_error_trap_push ();

    XGetInputFocus (GDK_DISPLAY_XDISPLAY (gdk_display_get_default ()), &focus, &rev);
    XSetInputFocus (GDK_DISPLAY_XDISPLAY (gdk_display_get_default ()), PointerRoot, RevertToNone, CurrentTime);

    gdk_error_trap_pop_ignored ();
}
