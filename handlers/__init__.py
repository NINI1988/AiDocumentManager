# handlers package
from handlers.deka import DekaBankHandler
from handlers.rente import RentenversicherungHandler

from .canway import CanwayMeldebescheinigungZurSozialversicherungHandler, CanwayRechnungHandler

HANDLERS = [
    CanwayRechnungHandler(),
    CanwayMeldebescheinigungZurSozialversicherungHandler(),
    RentenversicherungHandler(),
    DekaBankHandler()
]

__all__ = ["CanwayRechnungHandler", "CanwayMeldebescheinigungZurSozialversicherungHandler", "RentenversicherungHandler", "DekaBankHandler", "HANDLERS"]
