from layers_edx.element import Composition
from layers_edx.quantification.reference_material import ReferenceMaterial
from layers_edx.spectrum.base_spectrum import BaseSpectrum


class ReferenceSpectrum(ReferenceMaterial):
    def __init__(self, spectrum: BaseSpectrum, composition: Composition):
        super().__init__(composition)
        self._spectrum = spectrum

    @property
    def spectrum(self) -> BaseSpectrum:
        return self._spectrum
