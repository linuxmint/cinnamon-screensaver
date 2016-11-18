#include <config.h>

#include <glib.h>
#include <glib/gstdio.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#include <unistd.h>

#include "setuid.h"

/*
 * Portions:
 * Copyright (c) 1991-2004 Jamie Zawinski <jwz@jwz.org>
 * Copyright (c) 2005 William Jon McCann <mccann@jhu.edu>
 */

#define PAM_SERVICE_NAME "cinnamon-desktop"

/* from gs-auth-pam.c */
static void
pam_check (void)
{
    const char   dir [] = "/etc/pam.d";
    const char  file [] = "/etc/pam.d/" PAM_SERVICE_NAME;
    const char file2 [] = "/etc/pam.conf";
    struct stat st;

    if (g_stat (dir, &st) == 0 && st.st_mode & S_IFDIR) {
        if (g_stat (file, &st) != 0) {
            g_warning ("%s does not exist.\n"
                       "Authentication via PAM is unlikely to work.",
                       file);
        }
    } else if (g_stat (file2, &st) == 0) {
        FILE *f = g_fopen (file2, "r");
        if (f) {
            gboolean ok = FALSE;
            char buf[255];
            while (fgets (buf, sizeof(buf), f)) {
                if (strstr (buf, PAM_SERVICE_NAME)) {
                    ok = TRUE;
                    break;
                }
            }

            fclose (f);
            if (!ok) {
                g_warning ("%s does not list the `%s' service.\n"
                           "Authentication via PAM is unlikely to work.",
                           file2, PAM_SERVICE_NAME);
            }
        }
    /* else warn about file2 existing but being unreadable? */
    } else {
        g_warning ("Neither %s nor %s exist.\n"
                   "Authentication via PAM is unlikely to work.",
                   file2, file);
    }
}

int
main (int    argc,
      char **argv)
{
    gboolean can_lock, ret;
    gchar    *nolock_reason;
    gchar    *orig_uid;
    gchar    *uid_message;
    gchar   **out_argv;
    gchar    *out_cmd;
    GPtrArray *array = g_ptr_array_new ();
    const gchar * const *dirs;

    pam_check ();

    can_lock = hack_uid (&nolock_reason,
                    &orig_uid,
                    &uid_message);

    if (nolock_reason) {
        g_print ("Locking disabled: %s\n", nolock_reason);
    }

    if (uid_message) {
        g_print ("Modified UID: %s\n", uid_message);
    }

    g_free (nolock_reason);
    g_free (orig_uid);
    g_free (uid_message);

    /* Locate the cinnamon-screensaver datadir */
    out_cmd = NULL;
    dirs = g_get_system_data_dirs ();

    if (dirs != NULL)
    {
        guint j;

        for (j = 0; j < g_strv_length ((gchar **) dirs); j++)
        {
            const gchar *dir = dirs[j];

            gchar *tryname = g_build_filename (dir, "cinnamon-screensaver", "cinnamon-screensaver-main.py", NULL);

            if (g_file_test (tryname, G_FILE_TEST_EXISTS | G_FILE_TEST_IS_EXECUTABLE))
            {
                out_cmd = g_strdup (tryname);
            }

            g_free (tryname);

            if (out_cmd != NULL)
            {
                break;
            }
        }
    }

    if (out_cmd == NULL)
    {
        g_printerr ("Could not locate cinnamon-screensaver install location");
        exit(1);
    }

    /* Construct the argv[] for cinnamon-screensaver-main.py */
    g_ptr_array_add (array, g_strdup ("cinnamon-screensaver-main.py"));

    if (argc > 1)
    {
        gint i;
        /* Skip argv[0] - which would be 'cinnamon-screensaver' */
        for (i = 1; i < argc; i++)
        {
            g_ptr_array_add (array, g_strdup (argv[i]));
        }
    }

    if (!can_lock)
    {
        g_ptr_array_add (array, g_strdup ("--disable-lock"));
    }

    g_ptr_array_add (array, NULL);

    out_argv = (gchar **) g_ptr_array_free (array, FALSE);

    ret = execv (out_cmd, out_argv);

    g_strfreev (out_argv);
    g_free (out_cmd);

    return ret;
}

