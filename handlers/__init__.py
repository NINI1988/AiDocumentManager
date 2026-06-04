# handlers package
from .canway import CanwayRechnungHandler

HANDLERS = [
    CanwayRechnungHandler(),
]

__all__ = ["CanwayRechnungHandler", "HANDLERS"]
