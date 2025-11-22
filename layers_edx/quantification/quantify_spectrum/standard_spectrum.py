from layers_edx.detector.detector import TDetector
from layers_edx.detector.eds_detector import EDSDetector
from layers_edx.element import Element, Composition
from layers_edx.quantification.standard_material import StandardMaterial
from layers_edx.roi import RegionOfInterestSet, RegionOfInterest
from layers_edx.simulation import BasicSimulator
from layers_edx.spectrum.base_spectrum import BaseSpectrum
from layers_edx.spectrum.spectrum_properties import SpectrumProperties
from layers_edx.units import ToSI, FromSI
from layers_edx.xrt import XRayTransition


class StandardSpectrum(StandardMaterial):

    def __init__(self,
                 spectrum: BaseSpectrum,
                 element: Element,
                 composition: Composition,
                 stripped_elements: set[Element] = None,
                 min_intensity: float = 1.0e-3):
        self._spectrum = spectrum
        self._detector = spectrum.properties.detector
        if not isinstance(self.detector, EDSDetector):
            raise ValueError("Detector must be an instance of the EDSDetector class")
        self._beam_energy = ToSI.kev(spectrum.properties.beam_energy)
        super().__init__(element, composition, stripped_elements, min_intensity)

    @property
    def spectrum(self) -> BaseSpectrum:
        return self._spectrum

    @property
    def detector(self) -> TDetector:
        """The detector associated with this standard spectrum."""
        return self._detector

    @property
    def beam_energy(self) -> float:
        """The beam energy at which the spectrum was recorded in SI units."""
        return self._beam_energy

    def create_element_roi_set(self, element: Element) -> RegionOfInterestSet:
        """Create the ROIs associated with the specified element. Finds the X-ray transition which are defined by the
        detector's lineshape model and limited by the minimum intensity."""
        model = self.detector.calibration.model
        broadening = ToSI.ev(model.fwhm_at_mn_ka)
        roi_set = RegionOfInterestSet(model, self.min_intensity, 0.6 * broadening, 0.6 * broadening)
        for xrt in self.detector.visible_xrts(element, self.beam_energy).xrts:
            roi_set.add_xrt(xrt)
        return roi_set

    def compute_intensities(self, roi: RegionOfInterest) -> dict[XRayTransition, float]:
        """Computes the x-ray intensity as would be measured for this standard at 60 nA.s dose by the specified
        detector."""
        intensities: dict[XRayTransition, float] = {}
        spectrum_properties = SpectrumProperties(
            detector=self.detector,
            beam_energy=FromSI.kev(self.beam_energy),
            probe_current=1.0,
            live_time=60.0
        )
        shells = {xrt.destination for xrt in roi.xrts}
        simulator = BasicSimulator(self.composition, spectrum_properties, shells)
        xrt_set = roi.xrt_set(roi.first_element)
        for xrt, intensity in simulator.measured_intensities.items():
            if xrt in xrt_set.xrts:
                intensities[xrt] = intensity
        return intensities
