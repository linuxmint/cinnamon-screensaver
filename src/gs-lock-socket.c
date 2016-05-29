/* -*- Mode: C; tab-width: 8; indent-tabs-mode: nil; c-basic-offset: 8 -*-
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin Street - Suite 500, Boston, MA 02110-1335, USA.
 *
 */

#include "config.h"
#include "gs-lock-socket.h"
#include "string.h"
#include <gdk/gdk.h>

static void gs_lock_socket_class_init (GSLockSocketClass *klass);
static void gs_lock_socket_init       (GSLockSocket      *window);

G_DEFINE_TYPE (GSLockSocket, gs_lock_socket, GTK_TYPE_SOCKET)

static void
gs_lock_socket_send_configure_event (GSLockSocket *lock_socket)
{
  GtkAllocation allocation;
  XConfigureEvent xconfigure;
  gint x, y;

  GtkSocket *socket = GTK_SOCKET (lock_socket);

  GdkWindow *window = gtk_socket_get_plug_window (socket);

  g_return_if_fail (window != NULL);

  memset (&xconfigure, 0, sizeof (xconfigure));
  xconfigure.type = ConfigureNotify;

  xconfigure.event = GDK_WINDOW_XID (window);
  xconfigure.window = GDK_WINDOW_XID (window);

  /* The ICCCM says that synthetic events should have root relative
   * coordinates. We still aren't really ICCCM compliant, since
   * we don't send events when the real toplevel is moved.
   */
  gdk_error_trap_push ();
  gdk_window_get_origin (window, &x, &y);
  gdk_error_trap_pop_ignored ();

  gtk_widget_get_allocation (GTK_WIDGET(socket), &allocation);
  gint scale = gtk_widget_get_scale_factor (GTK_WIDGET (socket));
  xconfigure.x = x;
  xconfigure.y = y;
  xconfigure.width = allocation.width * scale;
  xconfigure.height = allocation.height * scale;

  xconfigure.border_width = 0;
  xconfigure.above = None;
  xconfigure.override_redirect = False;

  gdk_error_trap_push ();
  XSendEvent (GDK_WINDOW_XDISPLAY (window),
          GDK_WINDOW_XID (window),
          False, NoEventMask, (XEvent *)&xconfigure);
  gdk_error_trap_pop_ignored ();
}

static void
gs_lock_socket_get_preferred_height (GtkWidget      *widget,
                                     gint           *min_size,
                                     gint           *natural_size)
{
    GTK_WIDGET_CLASS (gs_lock_socket_parent_class)->get_preferred_height (widget,
                                                                          min_size,
                                                                          natural_size);

    gint scale = gtk_widget_get_scale_factor (widget);
    *min_size = *min_size / scale;
    *natural_size = *natural_size / scale;
}

static void
gs_lock_socket_get_preferred_width (GtkWidget      *widget,
                                    gint           *min_size,
                                    gint           *natural_size)
{
    GTK_WIDGET_CLASS (gs_lock_socket_parent_class)->get_preferred_width (widget,
                                                                         min_size,
                                                                         natural_size);

    gint scale = gtk_widget_get_scale_factor (widget);
    *min_size = *min_size / scale;
    *natural_size = *natural_size / scale;
}

static void
gs_lock_socket_size_allocate (GtkWidget      *widget,
                                    GtkAllocation  *allocation)
{
    GSLockSocket *socket = GS_LOCK_SOCKET (widget);

    gs_lock_socket_send_configure_event (socket);

    GTK_WIDGET_CLASS (gs_lock_socket_parent_class)->size_allocate (widget,
                                                                 allocation);
    gs_lock_socket_send_configure_event (socket);
}

static void
gs_lock_socket_class_init (GSLockSocketClass *klass)
{
    GObjectClass   *object_class = G_OBJECT_CLASS (klass);
    GtkWidgetClass *widget_class = GTK_WIDGET_CLASS (klass);

    widget_class->size_allocate = gs_lock_socket_size_allocate;
    widget_class->get_preferred_height = gs_lock_socket_get_preferred_height;
    widget_class->get_preferred_width = gs_lock_socket_get_preferred_width;
}

static void
gs_lock_socket_init (GSLockSocket *window)
{
}

GSLockSocket *
gs_lock_socket_new (void)
{
    GObject     *result;

    result = g_object_new (GS_TYPE_LOCK_SOCKET,
                           NULL);

    return GS_LOCK_SOCKET (result);
}
