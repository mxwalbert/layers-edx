from layers_edx.element import Element, Composition
from layers_edx.quantification.standard_material import StandardMaterial
from layers_edx.roi import RegionOfInterestSet, RegionOfInterest
from layers_edx.xrt import XRayTransition, XRayTransitionSet


class StandardModel(StandardMaterial):
    def __init__(
        self,
        model: dict[XRayTransition, float],
        beam_energy: float,
        element: Element,
        composition: Composition,
        stripped_elements: set[Element] = None,
        min_intensity: float = 1.0e-3,
    ):
        self._model = model
        self._beam_energy = beam_energy
        super().__init__(element, composition, stripped_elements, min_intensity)

    @property
    def model(self) -> dict[XRayTransition, float]:
        return self._model

    def create_element_roi_set(self, element: Element) -> RegionOfInterestSet:
        """
        Create the ROIs associated with the specified element. Finds the
        X-ray transitions which are limited by the minimum intensity.
        """
        roi_set = RegionOfInterestSet(min_intensity=self.min_intensity)
        for xrt in XRayTransitionSet.all_xrts(element, self._beam_energy).xrts:
            roi_set.add_xrt(xrt)
        return roi_set

    def compute_intensities(self, roi: RegionOfInterest) -> dict[XRayTransition, float]:
        """Directly uses the intensities from the model."""
        intensities: dict[XRayTransition, float] = {}
        for xrt in roi.xrt_set(roi.first_element).xrts:
            if xrt in self.model:
                intensities[xrt] = self.model[xrt]
        return intensities
