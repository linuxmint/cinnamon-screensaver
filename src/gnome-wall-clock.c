/* -*- mode: C; c-file-style: "linux"; indent-tabs-mode: t -*-
 * gnome-wall-clock.h - monitors TZ setting files and signals changes
 *
 * Copyright (C) 2010 Red Hat, Inc.
 * Copyright (C) 2011 Red Hat, Inc.
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU Library General Public License
 * as published by the Free Software Foundation; either version 2 of
 * the License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * Library General Public License for more details.
 *
 * You should have received a copy of the GNU Library General Public
 * License along with this program; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA
 * 02111-1307, USA.
 *
 * Author: Colin Walters <walters@verbum.org>
 */

#include "config.h"

#include <glib/gi18n-lib.h>

#define GNOME_DESKTOP_USE_UNSTABLE_API
#include "gnome-wall-clock.h"
#include <gdesktop-enums.h>
#include "gnome-datetime-source.h"

struct _GnomeWallClockPrivate {
	guint clock_update_id;

	char *clock_string;
	char *date_format;
	char *time_format;
	
	GFileMonitor *tz_monitor;	
};

enum {
	PROP_0,
	PROP_CLOCK,
	PROP_TIME_FORMAT,
	PROP_DATE_FORMAT,
};

G_DEFINE_TYPE (GnomeWallClock, gnome_wall_clock, G_TYPE_OBJECT);

static gboolean update_clock (gpointer data);

static void on_tz_changed (GFileMonitor *monitor,
                           GFile        *file,
                           GFile        *other_file,
                           GFileMonitorEvent *event,
                           gpointer      user_data);


static void
gnome_wall_clock_init (GnomeWallClock *self)
{
	GFile *tz;

	self->priv = G_TYPE_INSTANCE_GET_PRIVATE (self, GNOME_TYPE_WALL_CLOCK, GnomeWallClockPrivate);
	
	self->priv->clock_string = NULL;
	
	tz = g_file_new_for_path ("/etc/localtime");
	self->priv->tz_monitor = g_file_monitor_file (tz, 0, NULL, NULL);
	g_object_unref (tz);
	
	g_signal_connect (self->priv->tz_monitor, "changed", G_CALLBACK (on_tz_changed), self);
			
	update_clock (self);
}

static void
gnome_wall_clock_dispose (GObject *object)
{
	GnomeWallClock *self = GNOME_WALL_CLOCK (object);

	if (self->priv->clock_update_id) {
		g_source_remove (self->priv->clock_update_id);
		self->priv->clock_update_id = 0;
	}

	if (self->priv->tz_monitor != NULL) {
		g_object_unref (self->priv->tz_monitor);
		self->priv->tz_monitor = NULL;
	}
	
	G_OBJECT_CLASS (gnome_wall_clock_parent_class)->dispose (object);
}

static void
gnome_wall_clock_finalize (GObject *object)
{
	GnomeWallClock *self = GNOME_WALL_CLOCK (object);

	g_free (self->priv->clock_string);
	g_free (self->priv->time_format);
	g_free (self->priv->date_format);

	G_OBJECT_CLASS (gnome_wall_clock_parent_class)->finalize (object);
}

void
gnome_wall_clock_set_date_format (GnomeWallClock  *clock,
                            	  const char *format)
{
    g_free (clock->priv->date_format);
    clock->priv->date_format = NULL;

    if (format) {
           clock->priv->date_format = g_strdup (format);
    }
    update_clock(clock);
}
void
gnome_wall_clock_set_time_format (GnomeWallClock  *clock,
                            	  const char *format)
{
    g_free (clock->priv->time_format);
    clock->priv->time_format = NULL;

    if (format) {
           clock->priv->time_format = g_strdup (format);
    }
    update_clock(clock);
}

static void
gnome_wall_clock_set_property (GObject            *object,
                               guint               prop_id,
                               const GValue       *value,
                               GParamSpec         *pspec)
{
	GnomeWallClock *self = GNOME_WALL_CLOCK (object);
	switch (prop_id)
	{
		case PROP_TIME_FORMAT:
			gnome_wall_clock_set_time_format(self, g_value_get_string(value));
			break;
		case PROP_DATE_FORMAT:
			gnome_wall_clock_set_date_format(self, g_value_get_string(value));
			break;
		default:
			G_OBJECT_WARN_INVALID_PROPERTY_ID(object, prop_id, pspec);
			break;
	}
}


static void
gnome_wall_clock_get_property (GObject    *gobject,
			       guint       prop_id,
			       GValue     *value,
			       GParamSpec *pspec)
{
	GnomeWallClock *self = GNOME_WALL_CLOCK (gobject);

	switch (prop_id)
	{
		case PROP_CLOCK:
			g_value_set_string (value, self->priv->clock_string);
			break;
		case PROP_TIME_FORMAT:
			g_value_set_string (value, self->priv->time_format);
			break;
		case PROP_DATE_FORMAT:
			g_value_set_string (value, self->priv->date_format);
			break;
	default:
		G_OBJECT_WARN_INVALID_PROPERTY_ID (gobject, prop_id, pspec);
		break;
	}
}



static void
gnome_wall_clock_class_init (GnomeWallClockClass *klass)
{
	GObjectClass *gobject_class = G_OBJECT_CLASS (klass);

	gobject_class->get_property = gnome_wall_clock_get_property;
	gobject_class->set_property = gnome_wall_clock_set_property;
	gobject_class->dispose = gnome_wall_clock_dispose;
	gobject_class->finalize = gnome_wall_clock_finalize;

	/**
	 * GnomeWallClock:clock:
	 *
	 * A formatted string representing the current clock display.
	 */
	g_object_class_install_property (gobject_class,
					 PROP_CLOCK,
					 g_param_spec_string ("clock",
							      "",
							      "",
							      NULL,
							      G_PARAM_READABLE));
	g_object_class_install_property (gobject_class,
					 PROP_TIME_FORMAT,
					 g_param_spec_string ("time-format",
							      "",
							      "",
							      NULL,
							      G_PARAM_READWRITE));
	g_object_class_install_property (gobject_class,
					 PROP_DATE_FORMAT,
					 g_param_spec_string ("date-format",
							      "",
							      "",
							      NULL,
							      G_PARAM_READWRITE));


	g_type_class_add_private (gobject_class, sizeof (GnomeWallClockPrivate));
}

static gboolean
update_clock (gpointer data)
{
	GnomeWallClock   *self = data;	
	const char *format_string;	
	GSource *source;
	GDateTime *now;
	GDateTime *expiry;

	now = g_date_time_new_now_local ();	
	expiry = g_date_time_add_seconds (now, 60 - g_date_time_get_second (now));
  
	if (self->priv->clock_update_id)
		g_source_remove (self->priv->clock_update_id);
  
	source = _gnome_datetime_source_new (now, expiry, TRUE);
	g_source_set_priority (source, G_PRIORITY_HIGH);
	g_source_set_callback (source, update_clock, self, NULL);
	self->priv->clock_update_id = g_source_attach (source, NULL);
	g_source_unref (source);
	
    format_string = g_strdup_printf (
    "<b><span font_desc=\"Ubuntu 64\" foreground=\"#FFFFFF\">%s</span></b>\n<b><span font_desc=\"Ubuntu 24\" foreground=\"#FFFFFF\">%s</span></b>",
     (self->priv->time_format ? self->priv->time_format : _("%R")),
     (self->priv->date_format ? self->priv->date_format : _("%A, %B %e")));
        
	g_free (self->priv->clock_string);
	self->priv->clock_string = g_date_time_format (now, format_string);

	g_date_time_unref (now);
	g_date_time_unref (expiry);
      
	g_object_notify ((GObject*)self, "clock");

	return FALSE;
}

static void
on_tz_changed (GFileMonitor      *monitor,
               GFile             *file,
               GFile             *other_file,
               GFileMonitorEvent *event,
               gpointer           user_data)
{
	update_clock (user_data);
}

const char *
gnome_wall_clock_get_clock (GnomeWallClock *clock)
{	
    return clock->priv->clock_string;
}
