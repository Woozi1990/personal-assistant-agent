from dataclasses import dataclass
from typing import Any


@dataclass
class PendingAction:
    action: str
    data:dict[str, Any]

@dataclass
class SessionState:
    pending_action: PendingAction | None = None

