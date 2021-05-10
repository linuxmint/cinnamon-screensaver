/* -*- Mode: C; tab-width: 8; indent-tabs-mode: nil; c-basic-offset: 8 -*-
 *
 * Copyright (C) 2004-2006 William Jon McCann <mccann@jhu.edu>
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation; either version 2 of the
 * License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin Street - Suite 500, Boston, MA
 * 02110-1335, USA.
 *
 * Authors: William Jon McCann <mccann@jhu.edu>
 *
 */

#include "config.h"
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <gdk/gdk.h>
#include <gdk/gdkx.h>
#include <gtk/gtk.h>

#ifdef HAVE_XF86MISCSETGRABKEYSSTATE
# include <X11/extensions/xf86misc.h>
#endif /* HAVE_XF86MISCSETGRABKEYSSTATE */

#include "event-grabber.h"

static void     event_grabber_class_init (EventGrabberClass *klass);
static void     event_grabber_init       (EventGrabber      *grab);
static void     event_grabber_finalize   (GObject        *object);

#define EVENT_GRABBER_GET_PRIVATE(o) (G_TYPE_INSTANCE_GET_PRIVATE ((o), EVENT_TYPE_GRABBER, EventGrabberPrivate))

G_DEFINE_TYPE (EventGrabber, event_grabber, G_TYPE_OBJECT)

static gpointer grab_object = NULL;

struct EventGrabberPrivate
{
        GDBusConnection *session_bus;

        guint      mouse_hide_cursor : 1;
        GdkWindow *mouse_grab_window;
        GdkWindow *keyboard_grab_window;
        GdkScreen *mouse_grab_screen;
        GdkScreen *keyboard_grab_screen;

        GtkWidget *invisible;
};

static const char *
grab_string (int status)
{
        switch (status) {
        case GDK_GRAB_SUCCESS:          return "GrabSuccess";
        case GDK_GRAB_ALREADY_GRABBED:  return "AlreadyGrabbed";
        case GDK_GRAB_INVALID_TIME:     return "GrabInvalidTime";
        case GDK_GRAB_NOT_VIEWABLE:     return "GrabNotViewable";
        case GDK_GRAB_FROZEN:           return "GrabFrozen";
        default:
                {
                        static char foo [255];
                        sprintf (foo, "unknown status: %d", status);
                        return foo;
                }
        }
}

#ifdef HAVE_XF86MISCSETGRABKEYSSTATE
/* This function enables and disables the Ctrl-Alt-KP_star and 
   Ctrl-Alt-KP_slash hot-keys, which (in XFree86 4.2) break any
   grabs and/or kill the grabbing client.  That would effectively
   unlock the screen, so we don't like that.

   The Ctrl-Alt-KP_star and Ctrl-Alt-KP_slash hot-keys only exist
   if AllowDeactivateGrabs and/or AllowClosedownGrabs are turned on
   in XF86Config.  I believe they are disabled by default.

   This does not affect any other keys (specifically Ctrl-Alt-BS or
   Ctrl-Alt-F1) but I wish it did.  Maybe it will someday.
 */
static void
xorg_lock_smasher_set_active (EventGrabber  *grab,
                              gboolean active)
{
        int status, event, error;

    if (!XF86MiscQueryExtension (GDK_DISPLAY_XDISPLAY (gdk_display_get_default ()), &event, &error)) {
        g_debug ("No XFree86-Misc extension present");
        return;
    }

        if (active) {
                g_debug ("Enabling the x.org grab smasher");
        } else {
                g_debug ("Disabling the x.org grab smasher");
        }

        gdk_error_trap_push ();

        status = XF86MiscSetGrabKeysState (GDK_DISPLAY_XDISPLAY (gdk_display_get_default ()), active);

        gdk_display_sync (gdk_display_get_default ());
        error = gdk_error_trap_pop ();

        if (active && status == MiscExtGrabStateAlready) {
                /* shut up, consider this success */
                status = MiscExtGrabStateSuccess;
        }

        if (error == Success) {
                g_debug ("XF86MiscSetGrabKeysState(%s) returned %s\n",
                          active ? "on" : "off",
                          (status == MiscExtGrabStateSuccess ? "MiscExtGrabStateSuccess" :
                           status == MiscExtGrabStateLocked  ? "MiscExtGrabStateLocked"  :
                           status == MiscExtGrabStateAlready ? "MiscExtGrabStateAlready" :
                           "unknown value"));
        } else {
                g_debug ("XF86MiscSetGrabKeysState(%s) failed with error code %d\n",
                          active ? "on" : "off", error);
        }
}
#else
static void
xorg_lock_smasher_set_active (EventGrabber  *grab,
                              gboolean active)
{
}
#endif /* HAVE_XF86MISCSETGRABKEYSSTATE */

static int
event_grabber_get_keyboard (EventGrabber    *grab,
                      GdkWindow *window,
                      GdkScreen *screen)
{
        GdkGrabStatus status;

        g_return_val_if_fail (window != NULL, FALSE);
        g_return_val_if_fail (screen != NULL, FALSE);

        g_debug ("Grabbing keyboard widget=%X", (guint32) GDK_WINDOW_XID (window));
        status = gdk_keyboard_grab (window, FALSE, GDK_CURRENT_TIME);

        if (status == GDK_GRAB_SUCCESS) {
                if (grab->priv->keyboard_grab_window != NULL) {
                        g_object_remove_weak_pointer (G_OBJECT (grab->priv->keyboard_grab_window),
                                                      (gpointer *) &grab->priv->keyboard_grab_window);
                }
                grab->priv->keyboard_grab_window = window;

                g_object_add_weak_pointer (G_OBJECT (grab->priv->keyboard_grab_window),
                                           (gpointer *) &grab->priv->keyboard_grab_window);

                grab->priv->keyboard_grab_screen = screen;
        } else {
                g_debug ("Couldn't grab keyboard!  (%s)", grab_string (status));
        }

        return status;
}

static int
event_grabber_get_mouse (EventGrabber    *grab,
                   GdkWindow *window,
                   GdkScreen *screen,
                   gboolean   hide_cursor)
{
        GdkGrabStatus status;
        GdkCursor    *cursor;

        g_return_val_if_fail (window != NULL, FALSE);
        g_return_val_if_fail (screen != NULL, FALSE);

        cursor = gdk_cursor_new (GDK_BLANK_CURSOR);

        g_debug ("Grabbing mouse widget=%X", (guint32) GDK_WINDOW_XID (window));
        status = gdk_pointer_grab (window, TRUE, 0, NULL,
                                   (hide_cursor ? cursor : NULL),
                                   GDK_CURRENT_TIME);

        if (status == GDK_GRAB_SUCCESS) {
                if (grab->priv->mouse_grab_window != NULL) {
                        g_object_remove_weak_pointer (G_OBJECT (grab->priv->mouse_grab_window),
                                                      (gpointer *) &grab->priv->mouse_grab_window);
                }
                grab->priv->mouse_grab_window = window;

                g_object_add_weak_pointer (G_OBJECT (grab->priv->mouse_grab_window),
                                           (gpointer *) &grab->priv->mouse_grab_window);

                grab->priv->mouse_grab_screen = screen;
                grab->priv->mouse_hide_cursor = hide_cursor;
        }

        g_object_unref (cursor);

        return status;
}

void
event_grabber_keyboard_reset (EventGrabber *grab)
{
        if (grab->priv->keyboard_grab_window != NULL) {
                g_object_remove_weak_pointer (G_OBJECT (grab->priv->keyboard_grab_window),
                                              (gpointer *) &grab->priv->keyboard_grab_window);
        }
        grab->priv->keyboard_grab_window = NULL;
        grab->priv->keyboard_grab_screen = NULL;
}

static gboolean
event_grabber_release_keyboard (EventGrabber *grab)
{
        g_debug ("Ungrabbing keyboard");
        gdk_keyboard_ungrab (GDK_CURRENT_TIME);

        event_grabber_keyboard_reset (grab);

        return TRUE;
}

void
event_grabber_mouse_reset (EventGrabber *grab)
{
        if (grab->priv->mouse_grab_window != NULL) {
                g_object_remove_weak_pointer (G_OBJECT (grab->priv->mouse_grab_window),
                                              (gpointer *) &grab->priv->mouse_grab_window);
        }

        grab->priv->mouse_grab_window = NULL;
        grab->priv->mouse_grab_screen = NULL;
}

gboolean
event_grabber_release_mouse (EventGrabber *grab)
{
        g_debug ("Ungrabbing pointer");
        gdk_pointer_ungrab (GDK_CURRENT_TIME);

        event_grabber_mouse_reset (grab);

        return TRUE;
}

static gboolean
event_grabber_move_mouse (EventGrabber    *grab,
                    GdkWindow *window,
                    GdkScreen *screen,
                    gboolean   hide_cursor)
{
        gboolean   result;
        GdkWindow *old_window;
        GdkScreen *old_screen;
        gboolean   old_hide_cursor;

        /* if the pointer is not grabbed and we have a
           mouse_grab_window defined then we lost the grab */
        if (! gdk_pointer_is_grabbed ()) {
                event_grabber_mouse_reset (grab);
        }

        if (grab->priv->mouse_grab_window == window) {
                g_debug ("Window %X is already grabbed, skipping",
                          (guint32) GDK_WINDOW_XID (grab->priv->mouse_grab_window));
                return TRUE;
        }

#if 0
        g_debug ("Intentionally skipping move pointer grabs");
        /* FIXME: GTK doesn't like having the pointer grabbed */
        return TRUE;
#else
        if (grab->priv->mouse_grab_window) {
                g_debug ("Moving pointer grab from %X to %X",
                          (guint32) GDK_WINDOW_XID (grab->priv->mouse_grab_window),
                          (guint32) GDK_WINDOW_XID (window));
        } else {
                g_debug ("Getting pointer grab on %X",
                          (guint32) GDK_WINDOW_XID (window));
        }
#endif

        g_debug ("*** doing X server grab");
        gdk_x11_grab_server ();

        old_window = grab->priv->mouse_grab_window;
        old_screen = grab->priv->mouse_grab_screen;
        old_hide_cursor = grab->priv->mouse_hide_cursor;

        if (old_window) {
                event_grabber_release_mouse (grab);
        }

        result = event_grabber_get_mouse (grab, window, screen, hide_cursor);

        if (result != GDK_GRAB_SUCCESS) {
                sleep (1);
                result = event_grabber_get_mouse (grab, window, screen, hide_cursor);
        }

        if ((result != GDK_GRAB_SUCCESS) && old_window) {
                g_debug ("Could not grab mouse for new window.  Resuming previous grab.");
                event_grabber_get_mouse (grab, old_window, old_screen, old_hide_cursor);
        }

        g_debug ("*** releasing X server grab");
        gdk_x11_ungrab_server ();
        gdk_flush ();

        return (result == GDK_GRAB_SUCCESS);
}

static gboolean
event_grabber_move_keyboard (EventGrabber    *grab,
                       GdkWindow *window,
                       GdkScreen *screen)
{
        gboolean   result;
        GdkWindow *old_window;
        GdkScreen *old_screen;

        if (grab->priv->keyboard_grab_window == window) {
                g_debug ("Window %X is already grabbed, skipping",
                          (guint32) GDK_WINDOW_XID (grab->priv->keyboard_grab_window));
                return TRUE;
        }

        if (grab->priv->keyboard_grab_window != NULL) {
                g_debug ("Moving keyboard grab from %X to %X",
                          (guint32) GDK_WINDOW_XID (grab->priv->keyboard_grab_window),
                          (guint32) GDK_WINDOW_XID (window));
        } else {
                g_debug ("Getting keyboard grab on %X",
                          (guint32) GDK_WINDOW_XID (window));

        }

        g_debug ("*** doing X server grab");
        gdk_x11_grab_server ();

        old_window = grab->priv->keyboard_grab_window;
        old_screen = grab->priv->keyboard_grab_screen;

        if (old_window) {
                event_grabber_release_keyboard (grab);
        }

        result = event_grabber_get_keyboard (grab, window, screen);

        if (result != GDK_GRAB_SUCCESS) {
                sleep (1);
                result = event_grabber_get_keyboard (grab, window, screen);
        }

        if ((result != GDK_GRAB_SUCCESS) && old_window) {
                g_debug ("Could not grab keyboard for new window.  Resuming previous grab.");
                event_grabber_get_keyboard (grab, old_window, old_screen);
        }

        g_debug ("*** releasing X server grab");
        gdk_x11_ungrab_server ();
        gdk_flush ();

        return (result == GDK_GRAB_SUCCESS);
}

static void
event_grabber_nuke_focus (void)
{
        Window focus = 0;
        int    rev = 0;

        g_debug ("Nuking focus");

        gdk_error_trap_push ();

        XGetInputFocus (GDK_DISPLAY_XDISPLAY (gdk_display_get_default ()), &focus, &rev);

        XSetInputFocus (GDK_DISPLAY_XDISPLAY (gdk_display_get_default ()), None, RevertToNone, CurrentTime);

        gdk_error_trap_pop_ignored ();
}

void
event_grabber_release (EventGrabber *grab)
{
        g_debug ("Releasing all grabs");

        event_grabber_release_mouse (grab);
        event_grabber_release_keyboard (grab);

        /* FIXME: is it right to enable this ? */
        xorg_lock_smasher_set_active (grab, TRUE);

        gdk_display_sync (gdk_display_get_default ());
        gdk_flush ();
}

/* The Cinnamon Shell holds an X grab when we're in the overview;
 * ask it to bounce out before we try locking the screen.
 */
static void
request_shell_exit_overview (EventGrabber *grab)
{
        GDBusMessage *message;

        /* Shouldn't happen, but... */
        if (!grab->priv->session_bus)
                return;

        message = g_dbus_message_new_method_call ("org.Cinnamon",
                                                  "/org/Cinnamon",
                                                  "org.freedesktop.DBus.Properties",
                                                  "Set");
        g_dbus_message_set_body (message,
                                 g_variant_new ("(ssv)",
                                                "org.Cinnamon",
                                                "OverviewActive",
                                                g_variant_new ("b",
                                                               FALSE)));

        g_dbus_connection_send_message (grab->priv->session_bus,
                                        message,
                                        G_DBUS_SEND_MESSAGE_FLAGS_NONE,
                                        NULL,
                                        NULL);
        g_object_unref (message);


        message = g_dbus_message_new_method_call ("org.Cinnamon",
                                                  "/org/Cinnamon",
                                                  "org.freedesktop.DBus.Properties",
                                                  "Set");
        g_dbus_message_set_body (message,
                                 g_variant_new ("(ssv)",
                                                "org.Cinnamon",
                                                "ExpoActive",
                                                g_variant_new ("b",
                                                               FALSE)));

        g_dbus_connection_send_message (grab->priv->session_bus,
                                        message,
                                        G_DBUS_SEND_MESSAGE_FLAGS_NONE,
                                        NULL,
                                        NULL);
        g_object_unref (message);
}

gboolean
event_grabber_grab_window (EventGrabber    *grab,
                     GdkWindow *window,
                     GdkScreen *screen,
                     gboolean   hide_cursor)
{
        gboolean mstatus = FALSE;
        gboolean kstatus = FALSE;
        int      i;
        int      retries = 4;
        gboolean focus_fuckus = FALSE;

        /* First, have stuff we control in GNOME un-grab */
        request_shell_exit_overview (grab);

 AGAIN:

        for (i = 0; i < retries; i++) {
                kstatus = event_grabber_get_keyboard (grab, window, screen);
                if (kstatus == GDK_GRAB_SUCCESS) {
                        break;
                }

                /* else, wait a second and try to grab again. */
                sleep (1);
        }

        if (kstatus != GDK_GRAB_SUCCESS) {
                if (!focus_fuckus) {
                        focus_fuckus = TRUE;
                        event_grabber_nuke_focus ();
                        goto AGAIN;
                }
        }

        for (i = 0; i < retries; i++) {
                mstatus = event_grabber_get_mouse (grab, window, screen, hide_cursor);
                if (mstatus == GDK_GRAB_SUCCESS) {
                        break;
                }

                /* else, wait a second and try to grab again. */
                sleep (1);
        }

        if (mstatus != GDK_GRAB_SUCCESS) {
                g_debug ("Couldn't grab pointer!  (%s)",
                          grab_string (mstatus));
        }

#if 0
        /* FIXME: release the pointer grab so GTK will work */
        event_grabber_release_mouse (grab);
#endif

        /* When should we allow blanking to proceed?  The current theory
           is that both a keyboard grab and a mouse grab are mandatory

           - If we don't have a keyboard grab, then we won't be able to
           read a password to unlock, so the kbd grab is manditory.

           - If we don't have a mouse grab, then we might not see mouse
           clicks as a signal to unblank, on-screen widgets won't work ideally,
           and event_grabber_move_to_window() will spin forever when it gets called.
        */

        if (kstatus != GDK_GRAB_SUCCESS || mstatus != GDK_GRAB_SUCCESS) {
                /* Do not blank without a keyboard and mouse grabs. */

                /* Release keyboard or mouse which was grabbed. */
                if (kstatus == GDK_GRAB_SUCCESS) {
                        event_grabber_release_keyboard (grab);
                }
                if (mstatus == GDK_GRAB_SUCCESS) {
                        event_grabber_release_mouse (grab);
                }

                return FALSE;
        }

        /* Grab is good, go ahead and blank.  */
        return TRUE;
}

/* this is used to grab the keyboard and mouse to the root */
gboolean
event_grabber_grab_root (EventGrabber  *grab,
                   gboolean hide_cursor)
{
        GdkDisplay *display;
        GdkWindow  *root;
        GdkScreen  *screen;
        gboolean    res;

        g_debug ("Grabbing the root window");

        display = gdk_display_get_default ();
        gdk_display_get_pointer (display, &screen, NULL, NULL, NULL);
        root = gdk_screen_get_root_window (screen);

        res = event_grabber_grab_window (grab, root, screen, hide_cursor);

        return res;
}

/* this is used to grab the keyboard and mouse to an offscreen window */
gboolean
event_grabber_grab_offscreen (EventGrabber *grab,
                        gboolean hide_cursor)
{
        GdkScreen *screen;
        gboolean   res;

        g_debug ("Grabbing an offscreen window");

        screen = gtk_invisible_get_screen (GTK_INVISIBLE (grab->priv->invisible));
        res = event_grabber_grab_window (grab, gtk_widget_get_window (grab->priv->invisible), screen, hide_cursor);

        return res;
}

/* This is similar to event_grabber_grab_window but doesn't fail */
void
event_grabber_move_to_window (EventGrabber    *grab,
                        GdkWindow *window,
                        GdkScreen *screen,
                        gboolean   hide_cursor)
{
        gboolean result = FALSE;

        g_return_if_fail (EVENT_IS_GRABBER (grab));

        xorg_lock_smasher_set_active (grab, FALSE);

        do {
                result = event_grabber_move_keyboard (grab, window, screen);
                gdk_flush ();
        } while (!result);

        do {
                result = event_grabber_move_mouse (grab, window, screen, hide_cursor);
                gdk_flush ();
        } while (!result);
}

static void
event_grabber_class_init (EventGrabberClass *klass)
{
        GObjectClass   *object_class = G_OBJECT_CLASS (klass);

        object_class->finalize = event_grabber_finalize;

        g_type_class_add_private (klass, sizeof (EventGrabberPrivate));
}

static void
event_grabber_init (EventGrabber *grab)
{
        grab->priv = EVENT_GRABBER_GET_PRIVATE (grab);

        grab->priv->session_bus = g_bus_get_sync (G_BUS_TYPE_SESSION, NULL, NULL);

        grab->priv->mouse_hide_cursor = FALSE;
        grab->priv->invisible = gtk_invisible_new ();
        gtk_widget_show (grab->priv->invisible);
}

static void
event_grabber_finalize (GObject *object)
{
        EventGrabber *grab;

        g_return_if_fail (object != NULL);
        g_return_if_fail (EVENT_IS_GRABBER (object));

        grab = EVENT_GRABBER (object);

        g_object_unref (grab->priv->session_bus);

        g_return_if_fail (grab->priv != NULL);

        gtk_widget_destroy (grab->priv->invisible);

        G_OBJECT_CLASS (event_grabber_parent_class)->finalize (object);
}

EventGrabber *
event_grabber_new (void)
{
        if (grab_object) {
                g_object_ref (grab_object);
        } else {
                grab_object = g_object_new (EVENT_TYPE_GRABBER, NULL);
                g_object_add_weak_pointer (grab_object,
                                           (gpointer *) &grab_object);
        }

        return EVENT_GRABBER (grab_object);
}
