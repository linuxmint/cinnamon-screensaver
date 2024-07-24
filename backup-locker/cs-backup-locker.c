#include "config.h"
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <errno.h>
#include <sys/time.h>
#include <sys/types.h>
#include <sys/wait.h>

#include <glib/gi18n.h>
#include <glib-unix.h>
#include <gtk/gtk.h>
#include <gdk/gdkx.h>

#include <libcscreensaver/cs-gdk-event-filter.h>
#include <libcscreensaver/cs-event-grabber.h>
#include <libcscreensaver/cs-screen.h>

static gboolean debug = FALSE;
static guint term_tty = 0;
static guint session_tty = 0;

static GMutex pretty_xid_mutex;
static GCancellable *window_monitor_cancellable = NULL;
static guint sigterm_src_id;

#define BACKUP_TYPE_WINDOW (backup_window_get_type ())

G_DECLARE_FINAL_TYPE (BackupWindow, backup_window, BACKUP, WINDOW, GtkWindow)

static void setup_window_monitor (BackupWindow *window, gulong xid);
static void quit (BackupWindow *window);

struct _BackupWindow
{
    GtkWindow parent_instance;
    GtkWidget *fixed;
    GtkWidget *info_box;

    CsGdkEventFilter *event_filter;
    CsEventGrabber *grabber;

    gulong pretty_xid;
    guint activate_idle_id;

    gboolean should_grab;
};

G_DEFINE_TYPE (BackupWindow, backup_window, GTK_TYPE_WINDOW)

static void
position_info_box (BackupWindow *window)
{
    GdkDisplay *display = gdk_display_get_default ();
    GdkMonitor *monitor = gdk_display_get_primary_monitor (display);
    GdkRectangle rect;
    GtkRequisition natural_size;

    gtk_widget_get_preferred_size (window->info_box, NULL, &natural_size);

    if (natural_size.width == 0 || natural_size.height == 0)
    {
        return;
    }

    gdk_monitor_get_workarea (monitor, &rect);

    g_debug ("Positioning info box (%dx%d) to primary monitor (%d+%d+%dx%d)",
             natural_size.width, natural_size.height,
             rect.x, rect.y, rect.width, rect.height);

    gtk_fixed_move (GTK_FIXED (window->fixed), window->info_box,
                    rect.x + (rect.width / 2) - (natural_size.width / 2),
                    rect.y + (rect.height / 2) - (natural_size.height / 2));
}

static void
root_window_size_changed (CsGdkEventFilter *filter,
                          gpointer          user_data)
{
    BackupWindow *window = BACKUP_WINDOW (user_data);
    GdkWindow *gdk_win;
    Display *xdisplay;

    gint w, h, screen_num;

    gdk_win = gtk_widget_get_window (GTK_WIDGET (window));

    xdisplay =  GDK_DISPLAY_XDISPLAY (gdk_window_get_display (gdk_win));
    screen_num = DefaultScreen (xdisplay);

    w = DisplayWidth (xdisplay, screen_num);
    h = DisplayHeight (xdisplay, screen_num);

    gdk_window_move_resize (gtk_widget_get_window (GTK_WIDGET (window)), 
                            0, 0, w, h);
    position_info_box (window);

    gtk_widget_queue_resize (GTK_WIDGET (window));
}

static void
set_active_background (BackupWindow *window,
                       gboolean      active)
{
    GtkStyleContext *context;

    context = gtk_widget_get_style_context (GTK_WIDGET (window));

    if (active)
    {
        gtk_style_context_remove_class (context, "backup-dormant");
        gtk_style_context_add_class (context, "backup-active");
    }
    else
    {
        gtk_style_context_remove_class (context, "backup-active");
        gtk_style_context_add_class (context, "backup-dormant");
    }

    gtk_widget_queue_draw (GTK_WIDGET (window));
}

static void
backup_window_show (GtkWidget *widget)
{
    g_return_if_fail (BACKUP_IS_WINDOW (widget));

    if (GTK_WIDGET_CLASS (backup_window_parent_class)->show) {
        GTK_WIDGET_CLASS (backup_window_parent_class)->show (widget);
    }
}

static void window_grab_broken (gpointer data);

static gboolean
activate_backup_window_cb (BackupWindow *window)
{
    g_debug ("Grabbing input");

    if (window->should_grab)
    {
        if (cs_event_grabber_grab_root (window->grabber, FALSE))
        {
            guint32 user_time;
            cs_event_grabber_move_to_window (window->grabber,
                                          gtk_widget_get_window (GTK_WIDGET (window)),
                                          gtk_widget_get_screen (GTK_WIDGET (window)),
                                          FALSE);
            g_signal_connect_swapped (window, "grab-broken-event", G_CALLBACK (window_grab_broken), window);

            set_active_background (window, TRUE);

            user_time = gdk_x11_display_get_user_time (gtk_widget_get_display (GTK_WIDGET (window)));
            gdk_x11_window_set_user_time (gtk_widget_get_window (GTK_WIDGET (window)), user_time);

            gtk_widget_show (window->info_box);
            position_info_box (window);
        }
        else
        {
            return G_SOURCE_CONTINUE;
        }
    }

    window->activate_idle_id = 0;
    return G_SOURCE_REMOVE;
}

static void
activate_backup_window (BackupWindow *window)
{
    g_clear_handle_id (&window->activate_idle_id, g_source_remove);
    window->activate_idle_id = g_idle_add ((GSourceFunc) activate_backup_window_cb, window);
}

static void
backup_window_ungrab (BackupWindow *window)
{
    cs_event_grabber_release (window->grabber);

    window->should_grab = FALSE;
}

static void
window_grab_broken (gpointer data)
{
    BackupWindow *window = BACKUP_WINDOW (data);

    g_signal_handlers_disconnect_by_func (window, window_grab_broken, window);

    if (window->should_grab)
    {
        g_debug ("Grab broken, retrying");
        activate_backup_window (window);
    }
}

static gboolean
update_for_compositing (gpointer data)
{
    BackupWindow *window = BACKUP_WINDOW (data);
    GdkVisual *visual;
    visual = gdk_screen_get_rgba_visual (gdk_screen_get_default ());
    if (!visual)
    {
        g_critical ("Can't get RGBA visual to paint backup window");
        return FALSE;
    }

    if (visual != NULL && gdk_screen_is_composited (gdk_screen_get_default ()))
    {
        gtk_widget_hide (GTK_WIDGET (window));
        gtk_widget_unrealize (GTK_WIDGET (window));
        gtk_widget_set_visual (GTK_WIDGET (window), visual);
        gtk_widget_realize (GTK_WIDGET (window));

        gtk_widget_show (GTK_WIDGET (window));
    }
    g_debug ("update for compositing\n");

    if (window->should_grab)
    {
        activate_backup_window (window);
    }

    return TRUE;
}

static void
on_composited_changed (gpointer data)
{
    g_debug ("Received composited-changed");

    g_return_if_fail (BACKUP_IS_WINDOW (data));

    BackupWindow *window = BACKUP_WINDOW (data);

    if (!update_for_compositing (window))
    {
        g_critical ("Error realizing backup-locker window - exiting");
        quit(window);
    }
}

static void
screensaver_window_changed (CsGdkEventFilter *filter,
                            Window            xwindow,
                            BackupWindow     *window)
{
    backup_window_ungrab (window);

    set_active_background (window, FALSE);
    setup_window_monitor (window, xwindow);
}

static void
backup_window_realize (GtkWidget *widget)
{
    if (GTK_WIDGET_CLASS (backup_window_parent_class)->realize) {
        GTK_WIDGET_CLASS (backup_window_parent_class)->realize (widget);
    }

    BackupWindow *window = BACKUP_WINDOW (widget);

    cs_screen_set_net_wm_name (gtk_widget_get_window (widget),
                               "backup-locker");

    root_window_size_changed (window->event_filter, (gpointer) widget);

    cs_gdk_event_filter_stop (window->event_filter);
    cs_gdk_event_filter_start (window->event_filter, FALSE, debug);
}

static void
backup_window_init (BackupWindow *window)
{
    GtkWidget *box;
    GtkWidget *widget;
    PangoAttrList *attrs;

    gtk_widget_set_events (GTK_WIDGET (window),
                           gtk_widget_get_events (GTK_WIDGET (window))
                           | GDK_POINTER_MOTION_MASK
                           | GDK_BUTTON_PRESS_MASK
                           | GDK_BUTTON_RELEASE_MASK
                           | GDK_KEY_PRESS_MASK
                           | GDK_KEY_RELEASE_MASK
                           | GDK_EXPOSURE_MASK
                           | GDK_VISIBILITY_NOTIFY_MASK
                           | GDK_ENTER_NOTIFY_MASK
                           | GDK_LEAVE_NOTIFY_MASK);

    window->fixed = gtk_fixed_new ();
    gtk_container_add (GTK_CONTAINER (window), window->fixed);

    box = gtk_box_new (GTK_ORIENTATION_VERTICAL, 0);
    gtk_widget_set_valign (box, GTK_ALIGN_CENTER);

    widget = gtk_image_new_from_icon_name ("csr-backup-locker-icon", GTK_ICON_SIZE_DIALOG);
    gtk_image_set_pixel_size (GTK_IMAGE (widget), 100);
    gtk_widget_set_halign (widget, GTK_ALIGN_CENTER);
    gtk_box_pack_start (GTK_BOX (box), widget, FALSE, FALSE, 6);
    // This is the first line of text for the backup-locker, explaining how to switch to tty
    // and run 'cinnamon-unlock-desktop' command.  This appears if the screensaver crashes.
    widget = gtk_label_new (_("Something went wrong with the screensaver."));
    attrs = pango_attr_list_new ();
    pango_attr_list_insert (attrs, pango_attr_size_new (20 * PANGO_SCALE));
    pango_attr_list_insert (attrs, pango_attr_foreground_new (65535, 65535, 65535));
    gtk_label_set_attributes (GTK_LABEL (widget), attrs);
    pango_attr_list_unref (attrs);
    gtk_widget_set_halign (widget, GTK_ALIGN_CENTER);
    gtk_box_pack_start (GTK_BOX (box), widget, FALSE, FALSE, 6);

    // (continued) This is a subtitle
    widget = gtk_label_new (_("We'll help you get your desktop back"));
    attrs = pango_attr_list_new ();
    pango_attr_list_insert (attrs, pango_attr_size_new (12 * PANGO_SCALE));
    pango_attr_list_insert (attrs, pango_attr_foreground_new (65535, 65535, 65535));
    gtk_label_set_attributes (GTK_LABEL (widget), attrs);
    pango_attr_list_unref (attrs);
    gtk_widget_set_halign (widget, GTK_ALIGN_CENTER);
    gtk_box_pack_start (GTK_BOX (box), widget, FALSE, FALSE, 6);

    const gchar *steps[] = {
        // (new section) Bulleted list of steps to take to unlock the desktop;
        N_("Switch to a console using <Control-Alt-F%u>."),
        // (list continued)
        N_("Log in by typing your user name followed by your password."),
        // (list continued)
        N_("At the prompt, type 'cinnamon-unlock-desktop' and press Enter."),
        // (list continued)
        N_("Switch back to your unlocked desktop using <Control-Alt-F%u>.")
    };

    const gchar *bug_report[] = {
        // (end section) Final words after the list of steps
        N_("If you can reproduce this behavior, please file a report here:"),
        // (end section continued)
        "https://github.com/linuxmint/cinnamon-screensaver"
    };

    GString *str = g_string_new (NULL);
    gchar *tmp0 = NULL;
    gchar *tmp1 = NULL;

    tmp0 = g_strdup_printf (_(steps[0]), term_tty);
    tmp1 = g_strdup_printf ("• %s\n", tmp0);
    g_string_append (str, tmp1);
    g_free (tmp0);
    g_free (tmp1);
    tmp1 = g_strdup_printf ("• %s\n", _(steps[1]));
    g_string_append (str, tmp1);
    g_free (tmp1);
    tmp1 = g_strdup_printf ("• %s\n", _(steps[2]));
    g_string_append (str, tmp1);
    g_free (tmp1);
    tmp0 = g_strdup_printf (_(steps[3]), session_tty);
    tmp1 = g_strdup_printf ("• %s\n", tmp0);
    g_string_append (str, tmp1);
    g_free (tmp0);
    g_free (tmp1);

    g_string_append (str, "\n");

    for (int i = 0; i < G_N_ELEMENTS (bug_report); i++)
    {
        gchar *line = g_strdup_printf ("%s\n", _(bug_report[i]));
        g_string_append (str, line);
        g_free (line);
    }

    widget = gtk_label_new (str->str);
    g_string_free (str, TRUE);

    attrs = pango_attr_list_new ();
    pango_attr_list_insert (attrs, pango_attr_size_new (10 * PANGO_SCALE));
    pango_attr_list_insert (attrs, pango_attr_foreground_new (65535, 65535, 65535));
    gtk_label_set_attributes (GTK_LABEL (widget), attrs);
    pango_attr_list_unref (attrs);
    gtk_label_set_line_wrap (GTK_LABEL (widget), TRUE);
    gtk_widget_set_halign (widget, GTK_ALIGN_CENTER);
    gtk_box_pack_start (GTK_BOX (box), widget, FALSE, FALSE, 6);

    g_signal_connect_swapped (gdk_screen_get_default (), "composited-changed", G_CALLBACK (on_composited_changed), window);

    gtk_widget_show_all (box);
    gtk_widget_set_no_show_all (box, TRUE);
    gtk_widget_hide (box);
    window->info_box = box;

    g_signal_connect_swapped (window->info_box, "realize", G_CALLBACK (position_info_box), window);

    gtk_fixed_put (GTK_FIXED (window->fixed), window->info_box, 0, 0);
    gtk_widget_show (window->fixed);

    window->grabber = cs_event_grabber_new (debug);
}

static void
backup_window_finalize (GObject *object)
{
        BackupWindow *window;

        g_return_if_fail (object != NULL);
        g_return_if_fail (GTK_IS_WINDOW (object));

        window = BACKUP_WINDOW (object);

        backup_window_ungrab (window);

        g_object_unref (window->event_filter);
        g_object_unref (window->grabber);

        G_OBJECT_CLASS (backup_window_parent_class)->finalize (object);
}

static void
backup_window_class_init (BackupWindowClass *klass)
{
    GObjectClass   *object_class = G_OBJECT_CLASS (klass);
    GtkWidgetClass *widget_class = GTK_WIDGET_CLASS (klass);

    object_class->finalize = backup_window_finalize;
    widget_class->show = backup_window_show;
    widget_class->realize = backup_window_realize;
}

static GtkWidget *
backup_window_new (gulong pretty_xid)
{
    BackupWindow *window;
    GtkStyleContext *context;
    GtkCssProvider *provider;
    GObject     *result;

    result = g_object_new (BACKUP_TYPE_WINDOW,
                           "type", GTK_WINDOW_POPUP,
                           NULL);

    window = BACKUP_WINDOW (result);

    context = gtk_widget_get_style_context (GTK_WIDGET (window));
    gtk_style_context_remove_class (context, "background");
    provider = gtk_css_provider_new ();
    gtk_css_provider_load_from_data (provider, ".backup-dormant { background-color: transparent;  }"
                                               ".backup-active  { background-color: black;        }", -1, NULL);
    gtk_style_context_add_provider (context,
                                    GTK_STYLE_PROVIDER (provider),
                                    GTK_STYLE_PROVIDER_PRIORITY_APPLICATION);

    set_active_background (window, FALSE);
 
    window->event_filter = cs_gdk_event_filter_new (GTK_WIDGET (window), pretty_xid);
    g_signal_connect (window->event_filter, "xscreen-size", G_CALLBACK (root_window_size_changed), window);
    g_signal_connect (window->event_filter, "screensaver-window-changed", G_CALLBACK (screensaver_window_changed), window);

    window->pretty_xid = pretty_xid;
    window->should_grab = FALSE;

    if (!update_for_compositing (window))
    {
        return NULL;
    }

    setup_window_monitor (BACKUP_WINDOW (window), window->pretty_xid);

    return GTK_WIDGET (result);
}

static void
window_monitor_thread (GTask        *task,
                       gpointer      source_object,
                       gpointer      task_data,
                       GCancellable *cancellable)
{
    GSubprocess *xprop_proc;
    GError *error;

    gulong xid = GDK_POINTER_TO_XID (task_data);
    gchar *xid_str = g_strdup_printf ("0x%lx", xid);
    error = NULL;

    xprop_proc = g_subprocess_new (G_SUBPROCESS_FLAGS_STDOUT_SILENCE,
                                   &error,
                                   "xprop",
                                   "-spy",
                                   "-id", (const gchar *) xid_str,
                                   NULL);

    g_free (xid_str);

    if (xprop_proc == NULL)
    {
        g_critical ("unable to monitor screensaver window: %s", error->message);
    }
    else
    {
        g_debug ("Monitoring screensaver window (0x%lx)", xid);
        g_subprocess_wait (xprop_proc, cancellable, &error);
        if (error != NULL && error->code != G_IO_ERROR_CANCELLED)
        {
            g_critical ("problem with screensaver window monitor: %s", error->message);
        }
    }
    g_clear_error (&error);
    g_task_return_boolean (task, TRUE);
}

static void
screensaver_window_gone (GObject      *source,
                         GAsyncResult *result,
                         gpointer      user_data)
{
    BackupWindow *window = BACKUP_WINDOW (user_data);
    GCancellable *task_cancellable = g_task_get_cancellable (G_TASK (result));
    gulong xid = GDK_POINTER_TO_XID (g_task_get_task_data (G_TASK (result)));

    g_task_propagate_boolean (G_TASK (result), NULL);

    // The normal screensaver window is gone - either thru a crash or normal unlocking.
    // The main process will kill us, or the user will have to.  Either way, grab everything.
    if (!g_cancellable_is_cancelled (task_cancellable))
    {
        g_mutex_lock (&pretty_xid_mutex);

        g_debug ("Screensaver window gone: 0x%lx", xid);
        if (xid == window->pretty_xid)
        {
            window->should_grab = TRUE;
            window->pretty_xid = 0;
            activate_backup_window (window);
        }
        else
        {
            g_debug ("Already have new screensaver window, not activating ourselves: 0x%lx", window->pretty_xid);
        }

        g_mutex_unlock (&pretty_xid_mutex);
    }

    g_clear_object (&task_cancellable);
}

static void
setup_window_monitor (BackupWindow *window, gulong xid)
{
    GTask *task;

    g_debug ("Beginning to monitor screensaver window 0x%lx", xid);

    g_mutex_lock (&pretty_xid_mutex);

    window->should_grab = FALSE;
    window->pretty_xid = xid;

    window_monitor_cancellable = g_cancellable_new ();
    task = g_task_new (NULL, window_monitor_cancellable, screensaver_window_gone, window);

    g_task_set_return_on_cancel (task, TRUE);
    g_task_set_task_data (task, GDK_XID_TO_POINTER (xid), NULL);

    g_task_run_in_thread (task, window_monitor_thread);
    g_object_unref (task);
    g_mutex_unlock (&pretty_xid_mutex);
}

static void
quit (BackupWindow *window)
{
    g_clear_handle_id (&sigterm_src_id, g_source_remove);
    g_cancellable_cancel (window_monitor_cancellable);

    gtk_widget_destroy (GTK_WIDGET (window));
    gtk_main_quit ();
}

static gboolean
sigterm_received (gpointer data)
{
    g_debug("SIGTERM received, cleaning up.");

    g_return_val_if_fail (BACKUP_IS_WINDOW (data), G_SOURCE_REMOVE);

    quit (BACKUP_WINDOW (data));

    return G_SOURCE_REMOVE;
}

int
main (int    argc,
      char **argv)
{
    GtkWidget *window;
    GError *error;
    static gboolean     show_version = FALSE;
    gchar *xid_str, *term_tty_str, *session_tty_str;

    const GOptionEntry entries []   = {
        { "xid", 0, 0, G_OPTION_ARG_STRING, &xid_str, "Window ID to monitor", NULL },
        { "term", 0, 0, G_OPTION_ARG_STRING, &term_tty_str, "Terminal tty number", NULL },
        { "session", 0, 0, G_OPTION_ARG_STRING, &session_tty_str, "Session tty number", NULL },
        { "version", 0, 0, G_OPTION_ARG_NONE, &show_version, "Version of this application", NULL },
        { "debug", 0, 0, G_OPTION_ARG_NONE, &debug, "Enable debugging code", NULL },
        { NULL }
    };

    bindtextdomain (GETTEXT_PACKAGE, LOCALEDIR);
    bind_textdomain_codeset (GETTEXT_PACKAGE, "UTF-8");
    textdomain (GETTEXT_PACKAGE);

    if (! gtk_init_with_args (&argc, &argv, NULL, entries, NULL, &error)) {
        if (error) {
            g_warning ("%s", error->message);
            g_error_free (error);
        } else {
            g_warning ("Unable to initialize GTK+");
        }
        exit (1);
    }

    if (debug)
    {
        g_setenv ("G_MESSAGES_DEBUG", "all", TRUE);
    }

    if (show_version) {
        g_print ("%s %s\n", g_get_prgname (), VERSION);
        exit (1);
    }

    g_debug ("backup-locker: initializing");

    if (!xid_str || !term_tty_str || !session_tty_str) {
        g_critical ("xid, term and session arguments are mandatory, exiting.");
        exit (1);
    }

    gulong xid = term_tty = session_tty = 0;

    xid = strtoul (xid_str, NULL, 0);
    term_tty = strtoul (term_tty_str, NULL, 0);
    session_tty = strtoul (session_tty_str, NULL, 0);

    if (xid == 0)
    {
        g_warning ("Couldn't parse screensaver XID argument");
        exit(1);
    }

    window = backup_window_new (xid);

    if (window == NULL)
    {
        g_critical ("No backup window");
        exit(1);
    }

    sigterm_src_id = g_unix_signal_add (SIGTERM, (GSourceFunc) sigterm_received, window);

    gtk_main ();

    g_debug ("backup-locker: exit");

    return 0;
}
