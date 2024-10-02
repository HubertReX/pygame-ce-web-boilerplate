
from dataclasses import dataclass
from typing import Any


@dataclass
class NPCBase:
    name = "NPCBase"
    ai: Any

    def init_ai(self) -> None:
        pass
