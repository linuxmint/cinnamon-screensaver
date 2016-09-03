#! /usr/bin/python3

from gi.repository import Gtk

class TransparentButton(Gtk.Button):
    def __init__(self, name, size):
        super(TransparentButton, self).__init__()
        self.get_style_context().add_class("transparentbutton")
        image = Gtk.Image.new_from_icon_name(name, size)
        self.set_can_default(True)
        self.set_can_focus(True)
        self.set_image(image)
