from dataclasses import dataclass
from typing import Any


@dataclass
class PendingAction:
    action: str
    data:dict[str, Any]