from typing import List

from handlers.deka import DekaBankHandler
from handlers.rente import RentenversicherungHandler
from utils.common import BaseHandler

from .canway import CanwayMeldebescheinigungZurSozialversicherungHandler, CanwayRechnungHandler

HANDLERS: List[BaseHandler] = [
    CanwayRechnungHandler(),
    CanwayMeldebescheinigungZurSozialversicherungHandler(),
    RentenversicherungHandler(),
    DekaBankHandler()
]

__all__ = ["CanwayRechnungHandler", "CanwayMeldebescheinigungZurSozialversicherungHandler", "RentenversicherungHandler", "DekaBankHandler", "HANDLERS"]
