/* -*- Mode: C; tab-width: 8; indent-tabs-mode: nil; c-basic-offset: 8 -*-
 *
 * Copyright (C) 2004-2006 William Jon McCann <mccann@jhu.edu>
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
 * Authors: William Jon McCann <mccann@jhu.edu>
 *
 */

#ifndef __EVENT_GRABBER_H
#define __EVENT_GRABBER_H

#include <glib.h>
#include <gdk/gdk.h>

G_BEGIN_DECLS

#define EVENT_TYPE_GRABBER         (event_grabber_get_type ())
#define EVENT_GRABBER(o)           (G_TYPE_CHECK_INSTANCE_CAST ((o), EVENT_TYPE_GRABBER, EventGrabber))
#define EVENT_GRABBER_CLASS(k)     (G_TYPE_CHECK_CLASS_CAST((k), EVENT_TYPE_GRABBER, EventGrabberClass))
#define EVENT_IS_GRABBER(o)        (G_TYPE_CHECK_INSTANCE_TYPE ((o), EVENT_TYPE_GRABBER))
#define EVENT_IS_GRABBER_CLASS(k)  (G_TYPE_CHECK_CLASS_TYPE ((k), EVENT_TYPE_GRABBER))
#define EVENT_GRABBER_GET_CLASS(o) (G_TYPE_INSTANCE_GET_CLASS ((o), EVENT_TYPE_GRABBER, EventGrabberClass))

typedef struct EventGrabberPrivate EventGrabberPrivate;

typedef struct
{
        GObject        parent;
        EventGrabberPrivate *priv;
} EventGrabber;

typedef struct
{
        GObjectClass   parent_class;

} EventGrabberClass;

GType     event_grabber_get_type         (void);

EventGrabber  * event_grabber_new              (void);

void      event_grabber_release          (EventGrabber    *grab);
gboolean  event_grabber_release_mouse    (EventGrabber    *grab);

gboolean  event_grabber_grab_window      (EventGrabber    *grab,
                                    GdkWindow *window,
                                    GdkScreen *screen,
                                    gboolean   hide_cursor);

gboolean  event_grabber_grab_root        (EventGrabber    *grab,
                                    gboolean   hide_cursor);
gboolean  event_grabber_grab_offscreen   (EventGrabber    *grab,
                                    gboolean   hide_cursor);

void      event_grabber_move_to_window   (EventGrabber    *grab,
                                    GdkWindow *window,
                                    GdkScreen *screen,
                                    gboolean   hide_cursor);

void      event_grabber_mouse_reset      (EventGrabber    *grab);
void      event_grabber_keyboard_reset   (EventGrabber    *grab);

G_END_DECLS

#endif /* __EVENT_GRABBER_H */
