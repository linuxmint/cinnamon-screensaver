from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class LocationData:
    lat: float
    lon: float
    city: Optional[str] = None
    country: Optional[str] = None
    timeZone: Optional[str] = None
    entryText: Optional[str] = None


class LocationProvider(ABC):
    @abstractmethod
    def GetLocation(self) -> LocationData:
        pass
