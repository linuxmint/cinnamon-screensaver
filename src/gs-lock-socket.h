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

#ifndef __GS_LOCK_SOCKET_H
#define __GS_LOCK_SOCKET_H

#include <gtk/gtk.h>
#include <gtk/gtkx.h>

G_BEGIN_DECLS

#define GS_TYPE_LOCK_SOCKET         (gs_lock_socket_get_type ())
#define GS_LOCK_SOCKET(o)           (G_TYPE_CHECK_INSTANCE_CAST ((o), GS_TYPE_LOCK_SOCKET, GSLockSocket))
#define GS_LOCK_SOCKET_CLASS(k)     (G_TYPE_CHECK_CLASS_CAST((k), GS_TYPE_LOCK_SOCKET, GSLockSocketClass))
#define GS_IS_LOCK_SOCKET(o)        (G_TYPE_CHECK_INSTANCE_TYPE ((o), GS_TYPE_LOCK_SOCKET))
#define GS_IS_LOCK_SOCKET_CLASS(k)  (G_TYPE_CHECK_CLASS_TYPE ((k), GS_TYPE_LOCK_SOCKET))
#define GS_LOCK_SOCKET_GET_CLASS(o) (G_TYPE_INSTANCE_GET_CLASS ((o), GS_TYPE_LOCK_SOCKET, GSLockSocketClass))

typedef struct
{
        GtkSocket            socket;
} GSLockSocket;

typedef struct
{
        GtkSocketClass       socket_class;
} GSLockSocketClass;

GType       gs_lock_socket_get_type           (void);

GSLockSocket  * gs_lock_socket_new                (void);

G_END_DECLS

#endif /* __GS_LOCK_SOCKET_H */
