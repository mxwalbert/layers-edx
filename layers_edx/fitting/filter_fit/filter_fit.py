import numpy as np
import numpy.typing as npt
from layers_edx.fitting.filter_fit.filter_parameter import FilterParameter
from layers_edx.fitting.filter_fit.filtered_spectrum import FilteredSpectrum
from layers_edx.fitting.filter_fit.filter import TopHatFilter
from layers_edx.fitting.filter_fit.interval import Interval
from layers_edx.fitting.linear_fit import LinearFit
from layers_edx.detector.detector import TDetector
from layers_edx.element import Element
from layers_edx.fitting.culling import TCullingStrategy
from layers_edx.quantification.quantify_spectrum.reference_spectrum import ReferenceSpectrum
from layers_edx.roi import RegionOfInterest
from layers_edx.spectrum.base_spectrum import BaseSpectrum
from layers_edx.units import ToSI


class FilterFit(LinearFit):

    @staticmethod
    def fill_data(data: npt.NDArray[np.floating], thresh: float = float('inf')) -> npt.NDArray[np.floating]:
        """Fills NaN values and values which are below the `thresh` with the previous value in the `data`."""
        for idx in np.where(np.isnan(data) | (data < thresh))[0]:
            if idx == 0:
                data[idx] = 0.0 if thresh == float('inf') else float('inf')
            else:
                data[idx] = data[idx-1]
        return data

    def __init__(self,
                 references: dict[RegionOfInterest, ReferenceSpectrum],
                 detector: TDetector,
                 culling_strategy: TCullingStrategy = None,
                 naive: bool = True,
                 model_thresh: float = 2.5e3):
        self._detector = detector
        self._naive = naive
        self._model_thresh = model_thresh
        self._const_ff = TopHatFilter(detector.calibration.model.fwhm_at_mn_ka, detector.calibration.channel_width)
        super().__init__(references, culling_strategy)

    def _assign_parameters(self) -> None:
        self._parameters = []
        for roi, reference in self.references.items():
            element = roi.first_element
            filtered = self.filter_reference(reference.spectrum, roi, element)
            self._parameters.append(FilterParameter(filtered, self.naive, self.model_thresh))

    def filter_reference(self, reference: BaseSpectrum, roi: RegionOfInterest, element: Element) -> FilteredSpectrum:
        bci = reference.background_corrected_integral(ToSI.ev(roi.low_energy), ToSI.ev(roi.high_energy))
        if (bci[0] / bci[1]) > 3.0:
            return FilteredSpectrum(reference, self._const_ff, element, roi)

    @property
    def detector(self) -> TDetector:
        """The detector associated with this filter fit."""
        return self._detector

    @property
    def naive(self) -> bool:
        """Flags whether to use the naive implementation of the background modelling."""
        return self._naive

    @property
    def model_thresh(self) -> float:
        """The threshold energy in eV for the modelling of the background."""
        return self._model_thresh

    def features_and_targets(self, unknown: BaseSpectrum, selected: list[
        FilterParameter]) -> tuple[npt.NDArray[np.floating], npt.NDArray[np.floating]]:
        unknown = FilteredSpectrum(unknown, self._const_ff)
        ivs = Interval.sortmerge([p.filtered.non_zero_interval for p in selected])
        idx = Interval.extract(len(unknown.data), ivs)
        features = np.vstack([self.fill_data(p.filtered.data[idx]) for p in selected]).T
        targets = self.fill_data(unknown.data[idx]).reshape(-1, 1)
        return features, targets
