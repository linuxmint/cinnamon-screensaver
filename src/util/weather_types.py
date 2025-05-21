# Mostly derived from/compatible with:
# https://github.com/linuxmint/cinnamon-spices-applets/weather@mockturtl/src/3_8/types.ts
# we don't use much of the data, but intending for easy porting of sources + customizations going forward
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal, Optional

from util.location import LocationData
from util.weather import k_to_c, k_to_f

type PrecipitationTypes = Literal[
    "rain", "snow", "none", "ice pellets", "freezing rain"
]
type BuiltinIcons = Literal[
    "weather-clear",
    "weather-clear-night",
    "weather-few-clouds",
    "weather-few-clouds-night",
    "weather-clouds",
    "weather-many-clouds",
    "weather-overcast",
    "weather-showers-scattered",
    "weather-showers-scattered-day",
    "weather-showers-scattered-night",
    "weather-showers-day",
    "weather-showers-night",
    "weather-showers",
    "weather-rain",
    "weather-freezing-rain",
    "weather-snow",
    "weather-snow-day",
    "weather-snow-night",
    "weather-snow-rain",
    "weather-snow-scattered",
    "weather-snow-scattered-day",
    "weather-snow-scattered-night",
    "weather-storm",
    "weather-hail",
    "weather-fog",
    "weather-tornado",
    "weather-windy",
    "weather-breeze",
    "weather-clouds-night",
    "weather-severe-alert",
]
type CustomIcons = Literal[None]  # TODO


@dataclass
class Coord:
    lat: float
    lon: float


@dataclass
class Location:
    city: Optional[str] = None
    country: Optional[str] = None
    timeZone: Optional[str] = None
    url: Optional[str] = None
    tzOffset: Optional[float] = None


@dataclass
class StationInfo:
    distanceFrom: float
    name: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    area: Optional[str] = None


@dataclass
class Wind:
    # m/s
    speed: float
    # meteorological degrees
    degree: float


@dataclass
class Condition:
    main: str
    description: str
    icons: Optional[list[BuiltinIcons]] = None
    customIcon: Optional[CustomIcons] = None  # TODO


class ForecastData:
    date: int
    temp_min: float  # kelvin
    temp_max: float  # kelvin
    condition: Condition


@dataclass
class Precipitation:
    type: PrecipitationTypes
    # /** in mm */
    volume: Optional[float] = None
    # /** % */
    chance: Optional[float] = None


@dataclass
class HourlyForecastData:
    date: int
    # /** Kelvin */
    temp: float
    condition: Condition
    precipitation: Optional[Precipitation] = None


type APIUniqueFieldTypes = Literal["temperature", "percent", "string"]


@dataclass
class APIUniqueField:
    name: str
    value: str | float
    type: APIUniqueFieldTypes


@dataclass
class ImmediatePrecipitation:
    start: int
    end: int


type AlertSeverity = Literal["minor", "moderate", "severe", "extreme", "unknown"]


@dataclass
class AlertData:
    sender_name: str
    level: AlertSeverity
    title: str
    description: str
    icon: Optional[BuiltinIcons | CustomIcons] = None


@dataclass
class WeatherData:
    date: int
    coord: Coord
    location: Location
    condition: Condition
    wind: Wind
    stationInfo: Optional[StationInfo] = None
    # /** in UTC with tz info */
    sunrise: Optional[float] = None
    # /** in UTC with tz info  */
    sunset: Optional[float] = None
    # /** In Kelvin */
    temperature: Optional[float] = None
    # /** In hPa */
    pressure: Optional[float] = None
    # /** In percent */
    humidity: Optional[float] = None
    # /** In kelvin */
    dewPoint: Optional[float] = None
    forecasts: Optional[list[ForecastData]] = None
    hourlyForecasts: Optional[list[HourlyForecastData]] = None
    extra_field: Optional[APIUniqueField] = None
    immediatePrecipitation: Optional[ImmediatePrecipitation] = None
    alerts: Optional[list[AlertData]] = None

    def temp_f(self):
        return k_to_f(self.temperature) if self.temperature else None

    def temp_c(self):
        return k_to_c(self.temperature) if self.temperature else None


class WeatherProvider(ABC):
    """
    WeatherProvider tries to emulate the interface specified in cinnamon-spices-applets/weather@mockturtl
    such that other providers could be easily ported here in the future
    """

    needsApiKey: bool
    prettyName: str
    name: Literal["OpenWeatherMap_Open"]  # expand in the future
    maxForecastSupport: int
    maxHourlyForecastSupport: int
    website: str
    remainingCalls: Optional[int] = None
    supportHourlyPrecipChance: bool
    supportHourlyPrecipVolume: bool
    locationType: Literal["coordinates", "postcode"]

    @abstractmethod
    def GetWeather(self, loc: LocationData) -> WeatherData:
        pass
