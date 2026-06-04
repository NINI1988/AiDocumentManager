# handlers package
from .canway import CanwayMeldebescheinigungZurSozialversicherungHandler, CanwayRechnungHandler

HANDLERS = [
    CanwayRechnungHandler(),
    CanwayMeldebescheinigungZurSozialversicherungHandler()
]

__all__ = ["CanwayRechnungHandler", "CanwayMeldebescheinigungZurSozialversicherungHandler", "HANDLERS"]
