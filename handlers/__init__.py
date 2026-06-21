from typing import List

from handlers.deka import DekaBankHandler
from utils.common import BaseHandler
from .tax import TaxHandler
from .subfolder import SubfolderHandler
from .llm_metadata import LLMMetadataHandler
from .fallback import FallbackHandler

from .canway import CanwayMeldebescheinigungZurSozialversicherungHandler, CanwayRechnungHandler

HANDLERS: List[BaseHandler] = [
    SubfolderHandler(),
    CanwayRechnungHandler(),
    CanwayMeldebescheinigungZurSozialversicherungHandler(),
    DekaBankHandler(),
    LLMMetadataHandler(),
    TaxHandler(),
    FallbackHandler(),
]
__all__ = [
    "SubfolderHandler", 
    "CanwayRechnungHandler", 
    "CanwayMeldebescheinigungZurSozialversicherungHandler", 
    "DekaBankHandler", 
    "TaxHandler", 
    "HANDLERS"
]
