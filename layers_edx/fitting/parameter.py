from abc import ABC
from typing import TypeVar
from layers_edx.element import Element
from layers_edx.xrt import XRayTransitionSet


class Parameter(ABC):
    """Contains the data for an independent fit variable."""

    def __init__(self, element: Element, xrt_set: XRayTransitionSet):
        self._element = element
        self._xrt_set = xrt_set
        self._kratio = 0.0

    @property
    def element(self) -> Element:
        """Returns the element associated with this parameter."""
        return self._element

    @property
    def xrt_set(self) -> XRayTransitionSet:
        """Returns the set of X-ray transitions associated with this parameter."""
        return self._xrt_set

    @property
    def kratio(self) -> float:
        """Returns the current k-ratio value of this feature."""
        return self._kratio

    @kratio.setter
    def kratio(self, value: float):
        """Sets a new k-ratio value for this feature."""
        self._kratio = value


TParameter = TypeVar('TParameter', bound=Parameter)
