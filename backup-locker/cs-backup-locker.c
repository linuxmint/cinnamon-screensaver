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
#include "event-grabber.h"

static gboolean debug = FALSE;
static guint term_tty = 0;
static guint session_tty = 0;

#define BACKUP_TYPE_WINDOW (backup_window_get_type ())

G_DECLARE_FINAL_TYPE (BackupWindow, backup_window, BACKUP, WINDOW, GtkWindow)

struct _BackupWindow
{
    GtkWindow parent_instance;
    GtkWidget *fixed;
    GtkWidget *info_box;

    CsGdkEventFilter *event_filter;
    EventGrabber *grabber;

    gulong pretty_xid;
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
    gint baseline;

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

    if (debug)
    {
        w /= 2;
        h /= 2;
    }

    gdk_window_move_resize (gtk_widget_get_window (GTK_WIDGET (window)), 
                            0, 0, w, h);
    position_info_box (window);

    gtk_widget_queue_draw (GTK_WIDGET (window));
}

static gboolean
paint_background (GtkWidget    *widget,
                  cairo_t      *cr,
                  gpointer      user_data)
{
    cairo_set_source_rgba (cr, 0.0, 0.0, 0.0, 1.0);
    cairo_paint (cr);

    return FALSE;
}

static void
backup_window_show (GtkWidget *widget)
{
    g_return_if_fail (BACKUP_IS_WINDOW (widget));

    if (GTK_WIDGET_CLASS (backup_window_parent_class)->show) {
        GTK_WIDGET_CLASS (backup_window_parent_class)->show (widget);
    }

    cs_gdk_event_filter_start (BACKUP_WINDOW (widget)->event_filter);
}

static gboolean window_grab_broken (gpointer data);

static void
activate_backup_window (BackupWindow *window)
{
    event_grabber_move_to_window (window->grabber,
                                  gtk_widget_get_window (GTK_WIDGET (window)),
                                  gtk_widget_get_screen (GTK_WIDGET (window)),
                                  FALSE);

    g_signal_connect_swapped (window, "grab-broken-event", G_CALLBACK (window_grab_broken), window);

    gtk_widget_show (window->info_box);
    position_info_box (window);

    window->should_grab = TRUE;
}

static void
backup_window_ungrab (BackupWindow *window)
{
    event_grabber_release (window->grabber);

    window->should_grab = FALSE;
}

static gboolean
window_grab_broken (gpointer data)
{
    BackupWindow *window = BACKUP_WINDOW (data);

    g_signal_handlers_disconnect_by_func (window, window_grab_broken, window);

    if (window->should_grab)
    {
        activate_backup_window (window);
    }
}

static void
on_composited_changed (gpointer data)
{
    BackupWindow *window = BACKUP_WINDOW (data);

    if (gtk_widget_get_realized (GTK_WIDGET (window)))
    {
        gtk_widget_hide (GTK_WIDGET (window));
        gtk_widget_unrealize (GTK_WIDGET (window));
        gtk_widget_realize (GTK_WIDGET (window));

        if (window->should_grab)
        {
            guint32 user_time;

            user_time = gdk_x11_display_get_user_time (gtk_widget_get_display (GTK_WIDGET (window)));
            gdk_x11_window_set_user_time (gtk_widget_get_window (GTK_WIDGET (window)), user_time);
        }

        gtk_widget_show (GTK_WIDGET (window));
    }

    if (window->should_grab)
    {
        activate_backup_window (window);
    }
}

static void
backup_window_realize (GtkWidget *widget)
{
    if (GTK_WIDGET_CLASS (backup_window_parent_class)->realize) {
        GTK_WIDGET_CLASS (backup_window_parent_class)->realize (widget);
    }

    root_window_size_changed (BACKUP_WINDOW (widget)->event_filter, (gpointer) widget);

    gtk_window_set_keep_above (GTK_WINDOW (widget), TRUE);
}

static void
backup_window_init (BackupWindow *window)
{
    GtkWidget *box;
    GtkWidget *widget;
    PangoAttrList *attrs;

    gtk_window_set_decorated (GTK_WINDOW (window), FALSE);
    gtk_window_set_skip_taskbar_hint (GTK_WINDOW (window), TRUE);
    gtk_window_set_skip_pager_hint (GTK_WINDOW (window), TRUE);
    // gtk_window_fullscreen (GTK_WINDOW (window));

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

    widget = gtk_label_new (_("Something went wrong with the screensaver."));
    attrs = pango_attr_list_new ();
    pango_attr_list_insert (attrs, pango_attr_size_new (20 * PANGO_SCALE));
    pango_attr_list_insert (attrs, pango_attr_foreground_new (65535, 65535, 65535));
    gtk_label_set_attributes (GTK_LABEL (widget), attrs);
    pango_attr_list_unref (attrs);
    gtk_widget_set_halign (widget, GTK_ALIGN_CENTER);
    gtk_box_pack_start (GTK_BOX (box), widget, FALSE, FALSE, 6);

    widget = gtk_label_new (_("We'll help you get your desktop back"));
    attrs = pango_attr_list_new ();
    pango_attr_list_insert (attrs, pango_attr_size_new (12 * PANGO_SCALE));
    pango_attr_list_insert (attrs, pango_attr_foreground_new (65535, 65535, 65535));
    gtk_label_set_attributes (GTK_LABEL (widget), attrs);
    pango_attr_list_unref (attrs);
    gtk_widget_set_halign (widget, GTK_ALIGN_CENTER);
    gtk_box_pack_start (GTK_BOX (box), widget, FALSE, FALSE, 6);

    gchar *inst = g_strdup_printf (_("• Switch to a console using <Control-Alt-F%u>.\n"
                                     "• Log in by typing your user name followed by your password.\n"
                                     "• At the prompt, type 'cinnamon-unlock-desktop' and press Enter.\n"
                                     "• Switch back to your unlocked desktop using <Control-Alt-F%u>.\n\n"
                                     "If you can reproduce this behavior, please file a report here:\n"
                                     "https://github.com/linuxmint/cinnamon-screensaver"),
                                     term_tty, session_tty);

    widget = gtk_label_new (inst);
    g_free (inst);

    attrs = pango_attr_list_new ();
    pango_attr_list_insert (attrs, pango_attr_size_new (10 * PANGO_SCALE));
    pango_attr_list_insert (attrs, pango_attr_foreground_new (65535, 65535, 65535));
    gtk_label_set_attributes (GTK_LABEL (widget), attrs);
    pango_attr_list_unref (attrs);
    gtk_label_set_line_wrap (GTK_LABEL (widget), TRUE);
    gtk_widget_set_halign (widget, GTK_ALIGN_CENTER);
    gtk_box_pack_start (GTK_BOX (box), widget, FALSE, FALSE, 6);

    g_signal_connect (GTK_WIDGET (window), "draw", G_CALLBACK (paint_background), window);
    g_signal_connect_swapped (gdk_screen_get_default (), "composited-changed", G_CALLBACK (on_composited_changed), window);

    gtk_widget_show_all (box);
    gtk_widget_set_no_show_all (box, TRUE);
    gtk_widget_hide (box);
    window->info_box = box;

    g_signal_connect_swapped (window->info_box, "realize", G_CALLBACK (position_info_box), window);

    gtk_fixed_put (GTK_FIXED (window->fixed), window->info_box, 0, 0);
    gtk_widget_show (window->fixed);

    window->grabber = event_grabber_new ();
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

GtkWidget *
backup_window_new (gulong pretty_xid)
{
    BackupWindow *window;
    GObject     *result;

    result = g_object_new (BACKUP_TYPE_WINDOW,
                           "type", GTK_WINDOW_POPUP,
                           "app-paintable", TRUE,
                           NULL);

    window = BACKUP_WINDOW (result);

    window->event_filter = cs_gdk_event_filter_new (GTK_WIDGET (window), pretty_xid);
    g_signal_connect (window->event_filter, "xscreen-size", G_CALLBACK (root_window_size_changed), window);

    window->pretty_xid = pretty_xid;

    return GTK_WIDGET (result);
}

static GCancellable *window_monitor_cancellable = NULL;
static guint sigterm_src_id;

static void
window_monitor_thread (GTask        *task,
                       gpointer      source_object,
                       gpointer      task_data,
                       GCancellable *cancellable)
{
    GSubprocess *xprop_proc;
    GError *error;

    gulong xid = GDK_POINTER_TO_XID (task_data);
    gchar *xid_str = g_strdup_printf ("%lu", xid);
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
        g_clear_error (&error);
    }
    else
    {
        g_subprocess_wait (xprop_proc, cancellable, NULL);
    }

    g_task_return_boolean (task, TRUE);
}

static void
screensaver_window_gone (GObject      *source,
                         GAsyncResult *result,
                         gpointer      user_data)
{
    BackupWindow *window = BACKUP_WINDOW (user_data);

    g_task_propagate_boolean (G_TASK (result), NULL);

    // The normal screensaver window is gone - either thru a crash or normal unlocking.
    // The main process will kill us, or the user will have to.  Either way, grab everything.
    if (!g_cancellable_is_cancelled (g_task_get_cancellable (G_TASK (result))))
    {
        activate_backup_window (window);
    }

    g_clear_object (&window_monitor_cancellable);

}

static void
setup_window_monitor (BackupWindow *window, gulong xid)
{
    GTask *task;

    window_monitor_cancellable = g_cancellable_new ();
    task = g_task_new (NULL, window_monitor_cancellable, screensaver_window_gone, window);

    g_task_set_return_on_cancel (task, TRUE);
    g_task_set_task_data (task, GDK_XID_TO_POINTER (xid), NULL);

    g_task_run_in_thread (task, window_monitor_thread);
    g_object_unref (task);
}

static gboolean
sigterm_received (gpointer data)
{
    g_cancellable_cancel (window_monitor_cancellable);
    gtk_main_quit ();

    sigterm_src_id = 0;
    return G_SOURCE_REMOVE;
}

int
main (int    argc,
      char **argv)
{
    GtkWidget *window;
    GError *error;
    static gboolean     show_version = FALSE;
    static GOptionEntry entries []   = {
        { "version", 0, 0, G_OPTION_ARG_NONE, &show_version, N_("Version of this application"), NULL },
        { "debug", 0, 0, G_OPTION_ARG_NONE, &debug, N_("Enable debugging code"), NULL },
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

    if (!debug && argc < 4)
    {
        g_warning ("usage: cs-backup-locker ss-xid session_tty term_tty");
        exit (1);
    }

    // sleep(1);

    g_debug ("initializing cs-backup-locker");

    gulong xid = 0;

    if (debug)
    {
        xid = 9999;
    }
    else
    {
        xid = strtoul (argv[1], NULL, 0);
        term_tty = strtoul (argv[2], NULL, 0);
        session_tty = strtoul (argv[3], NULL, 0);
    }

    if (xid == 0)
    {
        g_warning ("Couldn't parse screensaver XID argument");
        exit(1);
    }

    window = backup_window_new (xid);

    sigterm_src_id = g_unix_signal_add (SIGTERM, (GSourceFunc) sigterm_received, window);
    setup_window_monitor (BACKUP_WINDOW (window), xid);

    gtk_widget_show (window);

    if (debug)
    {
        g_timeout_add_seconds (10, (GSourceFunc) gtk_main_quit, NULL);
    }

    gtk_main ();

    g_clear_handle_id (&sigterm_src_id, g_source_remove);
    g_cancellable_cancel (window_monitor_cancellable);
    gtk_widget_destroy (window);

    g_debug ("cs-backup-locker finished");

    return 0;
}
