#! /usr/bin/python3
# coding: utf-8

from gi.repository import Gtk

import status

class FocusNavigator:
    """
    FocusNavigator helps with tab navigation between
    widgets in our status.focusWidgets list.

    Since we handle most user events ourselves, we also
    need to handle Tab events correctly.
    """
    def __init__(self, widgets=[]):
        status.focusWidgets = widgets

    def _get_focus_index(self):
        widgets = status.focusWidgets
        focus_index = -1
        for widget in widgets:
            if widget.has_focus():
                focus_index = widgets.index(widget)
                break

        return focus_index

    def _focus_first_possible(self):
        widgets = status.focusWidgets

        for widget in widgets:
            if widget.get_sensitive():
                widget.grab_focus()
                widget.grab_default()
                break

    def _focus_next(self, current):
        widgets = status.focusWidgets
        new = current + 1

        if new >= len(widgets):
            new = 0

        if not widgets[new].get_sensitive():
            self._focus_next(new)
            return

        widgets[new].grab_focus()
        widgets[new].grab_default()

    def _focus_previous(self, current):
        widgets = status.focusWidgets
        new = current - 1

        if new < 0:
            new = len(widgets) - 1

        if not widgets[new].get_sensitive():
            self._focus_previous(new)
            return

        widgets[new].grab_focus()
        widgets[new].grab_default()

    def navigate(self, reverse):
        current_index = self._get_focus_index()

        if current_index == -1:
            self._focus_first_possible()
        if reverse:
            self._focus_previous(current_index)
        else:
            self._focus_next(current_index)

    def activate_focus(self):
        widgets = status.focusWidgets

        focus_index = self._get_focus_index()

        if focus_index == -1:
            return

        widget = widgets[focus_index]

        if isinstance(widget, Gtk.Button):
            widget.clicked()
        elif isinstance(widget, Gtk.Entry):
            widget.activate()

    def get_focused_widget(self):
        widgets = status.focusWidgets

        focus_index = self._get_focus_index()

        if focus_index == -1:
            return None

        return widgets[focus_index]

