import numpy as np
from numpy import typing as npt
from layers_edx.fitting.linear_fit import LinearFit
from layers_edx.fitting.model_fit.model_parameter import ModelParameter
from layers_edx.fitting.culling import TCullingStrategy
from layers_edx.quantification.quantify_model.reference_model import ReferenceModel
from layers_edx.roi import RegionOfInterest
from layers_edx.xrt import XRayTransition


class ModelFit(LinearFit):

    def __init__(self,
                 references: dict[RegionOfInterest, ReferenceModel],
                 culling_strategy: TCullingStrategy = None):
        super().__init__(references, culling_strategy)

    def _assign_parameters(self) -> None:
        self._parameters = []
        for roi, reference in self.references.items():
            element = roi.first_element
            xrt_set = roi.xrt_set(element)
            intensities = {xrt: intensity for xrt, intensity in reference.model.items() if xrt in xrt_set.xrts}
            self._parameters.append(ModelParameter(element, xrt_set, intensities))

    def features_and_targets(self, unknown: dict[XRayTransition, float], selected: list[ModelParameter]) -> tuple[npt.NDArray[np.floating], npt.NDArray[np.floating]]:
        features = []
        for p in selected:
            features.append([p.intensities[xrt] if xrt in p.intensities else 0.0 for xrt in unknown])
        return np.array(features), np.array(list(unknown.values())).reshape(-1, 1)
