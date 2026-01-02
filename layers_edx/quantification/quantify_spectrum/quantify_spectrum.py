from typing import Type
from layers_edx.detector.detector import TDetector
from layers_edx.element import Element
from layers_edx.fitting.linear_fit import TLinearFit
from layers_edx.fitting.culling import TCullingStrategy
from layers_edx.fitting.filter_fit.filter_fit import FilterFit
from layers_edx.kratio import KRatioSet
from layers_edx.quantification.quantify_spectrum.reference_spectrum import (
    ReferenceSpectrum,
)
from layers_edx.quantification.quantify_spectrum.standard_spectrum import (
    StandardSpectrum,
)
from layers_edx.quantification.quantify_using_standards import QuantifyUsingStandards
from layers_edx.roi import RegionOfInterest
from layers_edx.spectrum.base_spectrum import BaseSpectrum


class QuantifySpectrum(QuantifyUsingStandards):
    @staticmethod
    def pre_process_spectrum(spectrum: BaseSpectrum):
        return spectrum.copy().apply_zero_peak_discriminator()

    def __init__(
        self,
        detector: TDetector,
        beam_energy: float,
        standards: dict[Element, StandardSpectrum],
        user_references: dict[RegionOfInterest, ReferenceSpectrum] = None,
        culling_strategy: TCullingStrategy = None,
    ):
        super().__init__(beam_energy, standards, user_references, culling_strategy)
        self._detector = detector

    @staticmethod
    def create_reference(standard: StandardSpectrum) -> ReferenceSpectrum:
        return ReferenceSpectrum(standard.spectrum, standard.composition)

    @property
    def detector(self) -> TDetector:
        return self._detector

    @property
    def fitting_class(self) -> Type[TLinearFit]:
        return FilterFit

    @property
    def linear_fit(self) -> FilterFit:
        return FilterFit(
            self.references, self.detector, self.culling_strategy, naive=False
        )

    def compute(self, unknown: BaseSpectrum) -> KRatioSet:
        return super().compute(self.pre_process_spectrum(unknown))
