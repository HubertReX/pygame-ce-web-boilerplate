from __future__ import annotations
from dataclasses import dataclass, field
from settings import ZOOM_LEVEL, vec
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from scene import Scene


@dataclass
class Camera():
    scene: Scene
    target: vec = field(default_factory=lambda: vec(0, 0))
    _zoom: float = ZOOM_LEVEL

    @property
    def zoom(self) -> float:
        return self._zoom

    @zoom.setter
    def zoom(self, value: float) -> None:
        self._zoom = value
        if self.scene.map_view:
            self.scene.map_view.zoom = self._zoom
