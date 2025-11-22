from layers_edx.element import Element
from layers_edx.fitting.parameter import Parameter
from layers_edx.xrt import XRayTransitionSet, XRayTransition


class ModelParameter(Parameter):

    def __init__(self,
                 element: Element,
                 xrt_set: XRayTransitionSet,
                 intensities: dict[XRayTransition, float]):
        self._intensities = intensities
        super().__init__(element, xrt_set)

    @property
    def intensities(self) -> dict[XRayTransition, float]:
        """Returns the associated x-ray transitions."""
        return self._intensities
