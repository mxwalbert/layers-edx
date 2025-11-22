from layers_edx.element import Composition
from layers_edx.quantification.reference_material import ReferenceMaterial
from layers_edx.xrt import XRayTransition


class ReferenceModel(ReferenceMaterial):
    def __init__(self, model: dict[XRayTransition, float], composition: Composition):
        self._model = model
        super().__init__(composition)

    @property
    def model(self) -> dict[XRayTransition, float]:
        return self._model
