from typing import Type
from layers_edx.fitting.linear_fit import TLinearFit
from layers_edx.fitting.model_fit.model_fit import ModelFit
from layers_edx.kratio import KRatioSet
from layers_edx.quantification.quantify_model.standard_model import StandardModel
from layers_edx.quantification.quantify_model.reference_model import ReferenceModel
from layers_edx.quantification.quantify_using_standards import QuantifyUsingStandards
from layers_edx.xrt import XRayTransition


class QuantifyModel(QuantifyUsingStandards):
    @staticmethod
    def create_reference(standard: StandardModel) -> ReferenceModel:
        return ReferenceModel(standard.model, standard.composition)

    @property
    def fitting_class(self) -> Type[TLinearFit]:
        return ModelFit

    @property
    def linear_fit(self) -> ModelFit:
        return ModelFit(self.references, self.culling_strategy)

    def compute(self, unknown: dict[XRayTransition, float]) -> KRatioSet:
        return super().compute(unknown)
