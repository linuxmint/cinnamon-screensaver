#include <config.h>

#include "setuid.h"
#include <glib/gstdio.h>
#include <fcntl.h>
#include <stdio.h>
#include <string.h>
#include <sys/types.h>

#include "cs-init-utils.h"

/*
 * Portions:
 * Copyright (c) 1991-2004 Jamie Zawinski <jwz@jwz.org>
 * Copyright (c) 2005 William Jon McCann <mccann@jhu.edu>
 */

#define PAM_SERVICE_NAME "cinnamon-desktop"

/* from gs-auth-pam.c */
static gboolean
pam_check (void)
{
    gboolean ret = TRUE;

    const char   dir [] = "/etc/pam.d";
    const char  file [] = "/etc/pam.d/" PAM_SERVICE_NAME;
    const char file2 [] = "/etc/pam.conf";
    struct stat st;

    if (g_stat (dir, &st) == 0 && st.st_mode & S_IFDIR) {
        if (g_stat (file, &st) != 0) {
            g_warning ("%s does not exist.\n"
                       "Authentication via PAM is unlikely to work.",
                       file);
            ret = FALSE;
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
                ret = FALSE;
            }
        }
    /* else warn about file2 existing but being unreadable? */
    } else {
        g_warning ("Neither %s nor %s exist.\n"
                   "Authentication via PAM is unlikely to work.",
                   file2, file);
        ret = FALSE;
    }

    return ret;
}

gboolean
cs_init_utils_initialize_locking (gboolean debug)
{
    gboolean ret;
    char    *nolock_reason;
    char    *orig_uid;
    char    *uid_message;

    ret = pam_check () && hack_uid (&nolock_reason,
                                    &orig_uid,
                                    &uid_message);

    if (nolock_reason) {
        g_print ("Locking disabled: %s\n", nolock_reason);
    }

    if (uid_message && debug) {
        g_print ("Modified UID: %s\n", uid_message);
    }

    g_free (nolock_reason);
    g_free (orig_uid);
    g_free (uid_message);

    return ret;
}
