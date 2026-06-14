from typing import List

from handlers.deka import DekaBankHandler
from utils.common import BaseHandler

from .canway import CanwayMeldebescheinigungZurSozialversicherungHandler, CanwayRechnungHandler

HANDLERS: List[BaseHandler] = [
    CanwayRechnungHandler(),
    CanwayMeldebescheinigungZurSozialversicherungHandler(),
    DekaBankHandler()
]

__all__ = ["CanwayRechnungHandler", "CanwayMeldebescheinigungZurSozialversicherungHandler", "DekaBankHandler", "HANDLERS"]
