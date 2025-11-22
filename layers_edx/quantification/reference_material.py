from abc import ABC
from typing import TypeVar

from layers_edx.element import Composition, Element


class ReferenceMaterial(ABC):
    def __init__(self, composition: Composition):
        self._composition = composition

    @property
    def composition(self) -> Composition:
        return self._composition

    @property
    def elements(self) -> list[Element]:
        return self.composition.elements


TReferenceMaterial = TypeVar('TReferenceMaterial', bound=ReferenceMaterial)