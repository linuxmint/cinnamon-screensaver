#!/usr/bin/python3
from gi.repository import Gtk, Pango

from baseWindow import BaseWindow
from floating import Floating
from util import settings, trackers
from util.geojs import GeoJSLocationProvider
from util.location import LocationData
from util.openweathermap import OWMWeatherProvider

ICON_SIZE = 128  # probably works OK on most screens


class WeatherWidget(Floating, BaseWindow):
    """
    WeatherWidget displays current weather on screen

    It is a child of the Stage's GtkOverlay, and its placement is
    controlled by the overlay's child positioning function.

    When not Awake, it positions itself around all monitors
    using a timer which randomizes its halign and valign properties
    as well as its current monitor.
    """

    def __init__(self, initial_monitor=0, low_res=False):
        super(WeatherWidget, self).__init__(initial_monitor)
        self.get_style_context().add_class("weather")
        # trying to find a spot that won't overlap with clock or albumArt on init
        self.set_halign(Gtk.Align.CENTER)
        self.set_valign(Gtk.Align.END)
        self.set_property("margin", 6)

        self.low_res = low_res

        if not settings.get_show_weather():
            return

        # overall container
        big_box = Gtk.Box(Gtk.Orientation.HORIZONTAL)
        self.add(big_box)
        big_box.show()

        # icon
        self.icon_size = ICON_SIZE
        self.condition_icon = Gtk.Image()
        self.condition_icon.set_size_request(self.icon_size, self.icon_size)
        big_box.pack_start(self.condition_icon, False, False, 6)
        self.condition_icon.show()

        # temp + condition
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        big_box.pack_start(box, True, False, 6)
        box.show()

        self.temp_label = Gtk.Label()
        self.temp_label.show()
        self.temp_label.set_line_wrap(True)
        self.temp_label.set_alignment(0.5, 0.5)

        box.pack_start(self.temp_label, True, False, 6)

        self.desc_label = Gtk.Label()
        self.desc_label.show()
        self.desc_label.set_line_wrap(True)
        self.desc_label.set_alignment(0.5, 0.5)

        if self.low_res:
            self.desc_label.set_max_width_chars(50)
        else:
            self.desc_label.set_max_width_chars(80)

        box.pack_start(self.desc_label, True, True, 6)

        # TODO: get from settings once other providers are available
        self.location_provider = GeoJSLocationProvider()
        self.weather_provider = OWMWeatherProvider()

        self.location = self.get_location()
        self.update_weather()

        trackers.timer_tracker_get().start_seconds("weather", 600, self.update_weather)

    def get_location(self):
        loc_string = settings.get_weather_location()
        if loc_string == "" or "," not in loc_string:
            return self.location_provider.GetLocation()
        lat = float(loc_string.split(",")[0])
        lon = float(loc_string.split(",")[1])
        return LocationData(lat, lon)

    def update_weather(self):
        desc_font = Pango.FontDescription.from_string(settings.get_message_font())
        weather_font = Pango.FontDescription.from_string(settings.get_weather_font())

        if self.low_res:
            desc_size = desc_font.get_size() * 0.66
            desc_font.set_size(int(desc_size))

        weather_data = self.weather_provider.GetWeather(self.location)

        in_str = " " + _("in") + " "

        temp = (
            weather_data.temp_f()
            if settings.get_weather_units() == "imperial"
            else weather_data.temp_c()
        )
        temp_string = str(round(temp))
        desc_message = (
            weather_data.condition.description.title()
            + in_str
            + weather_data.location.city.capitalize()
        )

        markup = '<b><span font_desc="%s" foreground="#CCCCCC">%s</span></b>\n ' % (
            desc_font.to_string(),
            desc_message,
        )

        self.temp_label.set_markup(
            '<span font_desc="%s">%s°</span>' % (weather_font.to_string(), temp_string)
        )
        self.desc_label.set_markup(markup)

        self.condition_icon.set_from_icon_name(
            weather_data.condition.icons[0], Gtk.IconSize.DIALOG
        )
        self.condition_icon.set_pixel_size(self.icon_size)

    @staticmethod
    def on_destroy(data=None):
        trackers.timer_tracker_get().cancel("weather")
