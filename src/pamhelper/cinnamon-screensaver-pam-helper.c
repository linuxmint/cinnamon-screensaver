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
#include <string.h>
#include <sys/time.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>
#include <signal.h>

#include <glib/gi18n.h>
#include <gio/gunixinputstream.h>
#include <gtk/gtk.h>

#include <libcscreensaver/setuid.h>
#include <libcscreensaver/cs-auth.h>

#define MAX_FAILURES 5

#define DEBUG(...) if (debug_mode) g_printerr (__VA_ARGS__)

static gboolean debug_mode = FALSE;

static gboolean quit_request = FALSE;
static gchar *password_ptr = NULL;
static GMutex password_mutex;

static GCancellable *stdin_cancellable = NULL;

static GOptionEntry entries [] = {
    { "debug", 0, 0, G_OPTION_ARG_NONE, &debug_mode,
      N_("Show debugging output"), NULL },
    { NULL }
};

#define CS_PAM_AUTH_FAILURE "CS_PAM_AUTH_FAILURE\n"
#define CS_PAM_AUTH_SUCCESS "CS_PAM_AUTH_SUCCESS\n"
#define CS_PAM_AUTH_CANCELLED "CS_PAM_AUTH_CANCELLED\n"
#define CS_PAM_AUTH_BUSY_TRUE "CS_PAM_AUTH_BUSY_TRUE\n"
#define CS_PAM_AUTH_BUSY_FALSE "CS_PAM_AUTH_BUSY_FALSE\n"

#define CS_PAM_AUTH_SET_PROMPT_ "CS_PAM_AUTH_SET_PROMPT_"
#define CS_PAM_AUTH_SET_INFO_ "CS_PAM_AUTH_SET_INFO_"

#define CS_PAM_AUTH_REQUEST_SUBPROCESS_EXIT "CS_PAM_AUTH_REQUEST_SUBPROCESS_EXIT"

static void
shutdown_and_quit (void)
{
    if (!g_cancellable_is_cancelled (stdin_cancellable))
    {
        g_cancellable_cancel (stdin_cancellable);
    }
    else
    {
        g_clear_object (&stdin_cancellable);
        g_clear_pointer (&password_ptr, g_free);

        gtk_main_quit ();
    }
}

static gboolean
idle_shutdown_and_quit_cb (gpointer data)
{
    shutdown_and_quit ();
    return FALSE;
}

static void
send_failure (void)
{
    printf (CS_PAM_AUTH_FAILURE);
    fflush (stdout);
}

static void
send_success (void)
{
    printf (CS_PAM_AUTH_SUCCESS);
    fflush (stdout);
}

static void
send_cancelled (void)
{
    printf (CS_PAM_AUTH_CANCELLED);
    fflush (stdout);
}

static void
send_busy (gboolean busy)
{
    if (busy)
    {
        printf (CS_PAM_AUTH_BUSY_TRUE);
    }
    else
    {
        printf (CS_PAM_AUTH_BUSY_FALSE);
    }

    fflush (stdout);
}

static void
send_prompt (const gchar *msg)
{
    printf (CS_PAM_AUTH_SET_PROMPT_ "%s_\n", msg);
    fflush (stdout);
}

static void
send_info (const gchar *msg)
{
    printf (CS_PAM_AUTH_SET_INFO_ "%s_\n", msg);
    fflush (stdout);
}

static gboolean
received_quit (const gchar *str)
{
    if (g_strstr_len (str, -1, CS_PAM_AUTH_REQUEST_SUBPROCESS_EXIT))
    {
        return TRUE;
    }

    return FALSE;
}

static gboolean
auth_message_handler (CsAuthMessageStyle style,
                      const char        *msg,
                      char             **response,
                      gpointer           data)
{
    gboolean    ret;

    DEBUG ("Got message style %d: '%s'\n", style, msg);

    ret = TRUE;
    *response = NULL;

    switch (style)
    {
        case CS_AUTH_MESSAGE_PROMPT_ECHO_ON:
            break;
        case CS_AUTH_MESSAGE_PROMPT_ECHO_OFF:
            if (msg != NULL)
            {
                gchar *resp;

                send_prompt (msg);
                send_busy (FALSE);

                while (password_ptr == NULL)
                {
                    gtk_main_iteration_do (FALSE);
                    usleep (100 * 1000);
                }

                g_mutex_lock (&password_mutex);

                resp = g_strdup (password_ptr);

                DEBUG ("auth_message_handler processing response string\n");

                if (!received_quit (resp))
                {
                    *response = resp;
                }
                else
                {
                    quit_request = TRUE;
                    *response = NULL;
                    g_free (resp);
                }

                memset (password_ptr, '\b', strlen (password_ptr));
                g_clear_pointer (&password_ptr, g_free);

                g_mutex_unlock (&password_mutex);
            }
            break;
        case CS_AUTH_MESSAGE_ERROR_MSG:
            break;
        case CS_AUTH_MESSAGE_TEXT_INFO:
            if (msg != NULL)
            {
              send_info(msg);
            }
            break;
        default:
            g_assert_not_reached ();
    }

    if (*response == NULL) {
        DEBUG ("Got no response\n");
        ret = FALSE;
    } else {
        send_busy (TRUE);
    }

    /* we may have pending events that should be processed before continuing back into PAM */
    while (gtk_events_pending ()) {
        gtk_main_iteration ();
    }

    if (quit_request)
    {
        send_cancelled ();
        g_idle_add ((GSourceFunc) idle_shutdown_and_quit_cb, NULL);
    }

    return ret;
}

static gboolean
do_auth_check (void)
{
    GError *error;
    gboolean res;

    error = NULL;

    res = cs_auth_verify_user (g_get_user_name (),
                               g_getenv ("DISPLAY"),
                               auth_message_handler,
                               NULL,
                               &error);

    DEBUG ("Verify user returned: %s\n", res ? "TRUE" : "FALSE");

    if (!res)
    {
        if (error != NULL)
        {
            DEBUG ("Verify user returned error: %s\n", error->message);
        }

        if (error != NULL) {
            g_error_free (error);
        }
    }

    return res;
}

static gboolean
auth_check_idle (gpointer user_data)
{
    gboolean     res;
    gboolean     again;
    static guint loop_counter = 0;

    again = TRUE;
    res = do_auth_check ();

    if (res)
    {
        again = FALSE;
        send_success ();
        g_idle_add ((GSourceFunc) idle_shutdown_and_quit_cb, NULL);
    }
    else
    {
        loop_counter++;

        if (loop_counter < MAX_FAILURES)
        {
            send_failure ();
            DEBUG ("Authentication failed, retrying (%u)\n", loop_counter);
        }
        else
        {
            DEBUG ("Authentication failed, quitting (max failures)\n");
            again = FALSE;
            /* Don't quit immediately, but rather request that cinnamon-screensaver
             * terminates us after it has finished the dialog shake. Time out
             * after 5 seconds and quit anyway if this doesn't happen though */
            send_cancelled ();
            g_idle_add ((GSourceFunc) idle_shutdown_and_quit_cb, NULL);
        }
    }

    return again;
}

static void
stdin_monitor_task_thread (GTask        *task,
                           gpointer      source_object,
                           gpointer      task_data,
                           GCancellable *cancellable)
{
    while (!g_cancellable_is_cancelled (stdin_cancellable))
    {
        gchar buf[255];
        gchar *input;
        input = fgets (buf, sizeof (buf) - 1, stdin);

        g_mutex_lock (&password_mutex);

        if (input [strlen (input) - 1] == '\n')
        {
            input [strlen (input) - 1] = 0;
        }

        password_ptr = g_strdup (input);
        memset (input, '\b', strlen (input));

        g_mutex_unlock (&password_mutex);
    }

    g_task_return_boolean (task, TRUE);
}

static void
stdin_monitor_task_finished (GObject      *source,
                           GAsyncResult *result,
                           gpointer      user_data)
{
    g_task_propagate_boolean (G_TASK (result), NULL);

    g_clear_object (&stdin_cancellable);
    g_clear_pointer (&password_ptr, g_free);
    quit_request = FALSE;

    while (gtk_events_pending ())
    {
        gtk_main_iteration ();
    }

    g_idle_add ((GSourceFunc) gtk_main_quit, NULL);
}

static void
setup_stdin_monitor (void)
{
    GTask *task;

    stdin_cancellable = g_cancellable_new ();
    task = g_task_new (NULL, stdin_cancellable, stdin_monitor_task_finished, NULL);

    g_task_set_return_on_cancel (task, TRUE);

    g_task_run_in_thread (task, stdin_monitor_task_thread);
    g_object_unref (task);
}


/*
 * Copyright (c) 1991-2004 Jamie Zawinski <jwz@jwz.org>
 * Copyright (c) 2005 William Jon McCann <mccann@jhu.edu>
 *
 * Initializations that potentially take place as a privileged user:
   If the executable is setuid root, then these initializations
   are run as root, before discarding privileges.
*/
static gboolean
privileged_initialization (int     *argc,
                           char   **argv,
                           gboolean verbose)
{
    gboolean ret;
    char    *nolock_reason;
    char    *orig_uid;
    char    *uid_message;

#ifndef NO_LOCKING
    /* before hack_uid () for proper permissions */
    cs_auth_priv_init ();
#endif /* NO_LOCKING */

    ret = hack_uid (&nolock_reason,
                    &orig_uid,
                    &uid_message);

    if (nolock_reason)
    {
        DEBUG ("Locking disabled: %s\n", nolock_reason);
    }

    if (uid_message && verbose)
    {
        g_print ("Modified UID: %s", uid_message);
    }

    g_free (nolock_reason);
    g_free (orig_uid);
    g_free (uid_message);

    return ret;
}


/*
 * Copyright (c) 1991-2004 Jamie Zawinski <jwz@jwz.org>
 * Copyright (c) 2005 William Jon McCann <mccann@jhu.edu>
 *
 * Figure out what locking mechanisms are supported.
 */
static gboolean
lock_initialization (int     *argc,
                     char   **argv,
                     char   **nolock_reason,
                     gboolean verbose)
{
    if (nolock_reason != NULL)
    {
        *nolock_reason = NULL;
    }

#ifdef NO_LOCKING
    if (nolock_reason != NULL)
    {
        *nolock_reason = g_strdup ("not compiled with locking support");
    }

    return FALSE;
#else /* !NO_LOCKING */

    /* Finish initializing locking, now that we're out of privileged code. */
    if (!cs_auth_init ())
    {
        if (nolock_reason != NULL)
        {
            *nolock_reason = g_strdup ("error getting password");
        }

        return FALSE;
    }

#endif /* NO_LOCKING */

    return TRUE;
}

static void
response_lock_init_failed (void)
{
    /* if we fail to lock then we should drop the dialog */
    send_success ();
}

int
main (int    argc,
      char **argv)
{
    GError *error = NULL;
    char   *nolock_reason = NULL;

    bindtextdomain (GETTEXT_PACKAGE, "/usr/share/locale");

    if (! privileged_initialization (&argc, argv, debug_mode))
    {
        response_lock_init_failed ();
        exit (1);
    }

    error = NULL;
    if (! gtk_init_with_args (&argc, &argv, NULL, entries, NULL, &error))
    {
        if (error != NULL)
        {
            fprintf (stderr, "%s", error->message);
            g_error_free (error);
        }

        exit (1);
    }

    if (! lock_initialization (&argc, argv, &nolock_reason, debug_mode))
    {
        if (nolock_reason != NULL)
        {
            DEBUG ("Screen locking disabled: %s\n", nolock_reason);
            g_free (nolock_reason);
        }
        response_lock_init_failed ();

        exit (1);
    }

    cs_auth_set_verbose (debug_mode);

    quit_request = FALSE;

    setup_stdin_monitor ();

    g_idle_add ((GSourceFunc) auth_check_idle, NULL);

    gtk_main ();
    return 0;
}
