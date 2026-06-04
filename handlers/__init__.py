# handlers package
from handlers.rente import RentenversicherungHandler

from .canway import CanwayMeldebescheinigungZurSozialversicherungHandler, CanwayRechnungHandler

HANDLERS = [
    CanwayRechnungHandler(),
    CanwayMeldebescheinigungZurSozialversicherungHandler(),
    RentenversicherungHandler()
]

__all__ = ["CanwayRechnungHandler", "CanwayMeldebescheinigungZurSozialversicherungHandler", "RentenversicherungHandler", "HANDLERS"]
