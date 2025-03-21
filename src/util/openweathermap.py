import json
from types import SimpleNamespace

import requests
from gi.repository import Pango

from util.weather_types import (
    APIUniqueField,
    BuiltinIcons,
    Condition,
    CustomIcons,
    Location,
    LocationData,
    WeatherData,
    WeatherProvider,
    Wind,
)

OWM_URL = "https://api.openweathermap.org/data/2.5/weather"
# this is the OpenWeatherMap API key used by linux-mint/cinnamon-spices-applets/weather@mockturtl
# presumably belongs to the org?
OWM_API_KEY = "1c73f8259a86c6fd43c7163b543c8640"
OWM_SUPPORTED_LANGS = [
    "af",
    "al",
    "ar",
    "az",
    "bg",
    "ca",
    "cz",
    "da",
    "de",
    "el",
    "en",
    "eu",
    "fa",
    "fi",
    "fr",
    "gl",
    "he",
    "hi",
    "hr",
    "hu",
    "id",
    "it",
    "ja",
    "kr",
    "la",
    "lt",
    "mk",
    "no",
    "nl",
    "pl",
    "pt",
    "pt_br",
    "ro",
    "ru",
    "se",
    "sk",
    "sl",
    "sp",
    "es",
    "sr",
    "th",
    "tr",
    "ua",
    "uk",
    "vi",
    "zh_cn",
    "zh_tw",
    "zu",
]


class OWMWeatherProvider(WeatherProvider):
    """
    WeatherProvider implementation for OpenWeatherMap.org
    """

    def __init__(self):
        self.needsApiKey = False
        self.prettyName = _("OpenWeatherMap")
        self.name = "OpenWeatherMap_Open"
        self.maxForecastSupport = 7
        self.maxHourlyForecastSupport = 0
        self.website = "https://openweathermap.org/"
        self.remainingCalls = None
        self.supportHourlyPrecipChance = False
        self.supportHourlyPrecipVolume = False

    def GetWeather(self, loc: LocationData):
        lang = self.locale_to_owm_lang(Pango.language_get_default().to_string())
        pref = list(
            map(
                lambda p: self.locale_to_owm_lang(p.to_string()),
                Pango.language_get_preferred(),
            )
        )
        if lang not in OWM_SUPPORTED_LANGS:
            for locale in pref:
                if self.locale_to_owm_lang(locale) in OWM_SUPPORTED_LANGS:
                    lang = self.locale_to_owm_lang(locale)
                    break
        # if we still have not found a supported language...
        if lang not in OWM_SUPPORTED_LANGS:
            lang = "en"

        response = requests.get(
            OWM_URL,
            {
                "lat": loc.lat,
                "lon": loc.lon,
                "units": "standard",
                "appid": OWM_API_KEY,
                "lang": lang,
            },
        )

        # actual object structure: https://github.com/linuxmint/cinnamon-spices-applets/weather@mockturtl/src/3_8/providers/openweathermap/payload/weather.ts
        data = json.loads(response.text, object_hook=lambda d: SimpleNamespace(**d))
        return self.owm_data_to_weather_data(data)

    @staticmethod
    def locale_to_owm_lang(locale_string):
        if locale_string is None:
            return "en"

        # Dialect? support by OWM
        if (
            locale_string == "zh-cn"
            or locale_string == "zh-cn"
            or locale_string == "pt-br"
        ):
            return locale_string

        lang = locale_string.split("-")[0]
        # OWM uses different language code for Swedish, Czech, Korean, Latvian, Norwegian
        if lang == "sv":
            return "se"
        elif lang == "cs":
            return "cz"
        elif lang == "ko":
            return "kr"
        elif lang == "lv":
            return "la"
        elif lang == "nn" or lang == "nb":
            return "no"
        return lang

    def owm_data_to_weather_data(self, owm_data) -> WeatherData:
        """
        Returns as much of a complete WeatherData object as we can
        """
        return WeatherData(
            **dict(
                date=owm_data.dt,
                sunrise=owm_data.sys.sunrise,
                sunset=owm_data.sys.sunset,
                coord=owm_data.coord,
                location=Location(
                    **dict(
                        city=owm_data.name,
                        country=owm_data.sys.country,
                        url="https://openweathermap.org/city/%s" % owm_data.id,
                    )
                ),
                condition=Condition(
                    **dict(
                        main=owm_data.weather[0].main,
                        description=owm_data.weather[0].description,
                        icons=self.owm_icon_to_builtin_icons(owm_data.weather[0].icon),
                        customIcon=self.owm_icon_to_custom_icon(
                            owm_data.weather[0].icon
                        ),
                    )
                ),
                wind=Wind(**dict(speed=owm_data.wind.speed, degree=owm_data.wind.deg)),
                temperature=owm_data.main.temp,
                pressure=owm_data.main.pressure,
                humidity=owm_data.main.humidity,
                dewPoint=None,
                extra_field=APIUniqueField(
                    **dict(
                        type="temperature",
                        name=_("Feels Like"),
                        value=owm_data.main.feels_like,
                    )
                ),
            )
        )

    @staticmethod
    def owm_icon_to_builtin_icons(icon) -> list[BuiltinIcons]:
        # https://openweathermap.org/weather-conditions
        # fallback icons are: weather-clear-night
        # weather-clear weather-few-clouds-night weather-few-clouds
        # weather-fog weather-overcast weather-severe-alert weather-showers
        # weather-showers-scattered weather-snow weather-storm
        match icon:
            case "10d":
                # rain day */
                return [
                    "weather-rain",
                    "weather-showers-scattered",
                    "weather-freezing-rain",
                ]
            case "10n":
                # rain night */
                return [
                    "weather-rain",
                    "weather-showers-scattered",
                    "weather-freezing-rain",
                ]
            case "09n":
                # showers night*/
                return ["weather-showers"]
            case "09d":
                # showers day */
                return ["weather-showers"]
            case "13d":
                # snow day*/
                return ["weather-snow"]
            case "13n":
                # snow night */
                return ["weather-snow"]
            case "50d":
                # mist day */
                return ["weather-fog"]
            case "50n":
                # mist night */
                return ["weather-fog"]
            case "04d":
                # broken clouds day */
                return ["weather-overcast", "weather-clouds", "weather-few-clouds"]
            case "04n":
                # broken clouds night */
                return [
                    "weather-overcast",
                    "weather-clouds-night",
                    "weather-few-clouds-night",
                ]
            case "03n":
                # mostly cloudy (night) */
                return ["weather-clouds-night", "weather-few-clouds-night"]
            case "03d":
                # mostly cloudy (day) */
                return ["weather-clouds", "weather-few-clouds", "weather-overcast"]
            case "02n":
                # partly cloudy (night) */
                return ["weather-few-clouds-night"]
            case "02d":
                # partly cloudy (day) */
                return ["weather-few-clouds"]
            case "01n":
                # clear (night) */
                return ["weather-clear-night"]
            case "01d":
                # sunny */
                return ["weather-clear"]
            case "11d":
                # storm day */
                return ["weather-storm"]
            case "11n":
                # storm night */
                return ["weather-storm"]
            case _:
                return ["weather-severe-alert"]

    @staticmethod
    def owm_icon_to_custom_icon(icon) -> CustomIcons:
        return None  # TODO
