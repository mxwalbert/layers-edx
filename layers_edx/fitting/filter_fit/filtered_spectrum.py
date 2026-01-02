from __future__ import annotations
import math
import numpy as np
import numpy.typing as npt
from layers_edx.fitting.filter_fit.filter import Filter
from layers_edx.fitting.filter_fit.interval import Interval, NonZeroInterval
from layers_edx.element import Element
from layers_edx.xrt import XRayTransitionSet
from layers_edx.roi import RegionOfInterest
from layers_edx.units import FromSI
from layers_edx.spectrum.base_spectrum import bound, BaseSpectrum
from layers_edx.spectrum.derived_spectrum import DerivedSpectrum


class FilteredSpectrum(DerivedSpectrum):
    """Creates a filtered spectrum from an unfiltered spectrum."""

    def __init__(
        self,
        source: BaseSpectrum,
        fitting_filter: Filter,
        element: Element = None,
        roi: RegionOfInterest = None,
    ):
        super().__init__(source)
        self._fitting_filter = fitting_filter
        self._element = element
        self._roi = roi
        self._normalization = 1.0 / self.source.properties.dose
        self._compute()

    def _compute(self):
        """Computes the filtered spectrum region."""
        lld = self.source.zero_peak_discriminator_channel
        data = np.copy(self.source.data)
        filtered_data = np.zeros(data.shape)
        error_data = np.zeros(data.shape)
        if self.roi is None:
            data[:lld] = data[lld]
            low_channel = 0
        else:
            low_channel = self.source.bound(
                max(
                    lld, self.source.channel_from_energy(FromSI.ev(self.roi.low_energy))
                )
            )
            high_channel = self.source.bound(
                self.source.channel_from_energy(FromSI.ev(self.roi.high_energy))
            )
            data = data[low_channel : high_channel + 1]
        filter_array = self.fitting_filter.filter
        half_length = len(filter_array) // 2
        other_length = len(filter_array) - half_length
        for i in range(-half_length, len(data) + other_length):
            channel = i + low_channel
            if 0 <= channel < self.source.channel_count:
                total = 0.0
                error = 0.0
                for j in range(len(filter_array)):
                    filter_result = (
                        filter_array[j] * data[bound(i - half_length + j, 0, len(data))]
                    )
                    total += filter_result
                    error += filter_array[j] * filter_result
                filtered_data[channel] = self.normalization * total
                error_data[channel] = (
                    self.normalization * math.sqrt(error) if error > 0.0 else np.inf
                )
        self._data = filtered_data
        self._error_data = error_data
        self._non_zero_interval = NonZeroInterval(self._data)

    @property
    def element(self) -> Element:
        """Returns the element associated with this ``FilteredSpectrum``."""
        return self._element

    @property
    def roi(self) -> RegionOfInterest:
        """The ``RegionOfInterest`` for which the filter is applied on the spectrum."""
        return self._roi

    @property
    def fitting_filter(self) -> Filter:
        """The ``Filter`` object used for computing the filtered spectrum."""
        return self._fitting_filter

    @property
    def xrt_set(self) -> XRayTransitionSet | None:
        """The ``XRayTransitionSet`` which was filtered for fitting."""
        if self.element is None:
            return None
        if self.roi is None:
            return XRayTransitionSet(self.element, populate=False)
        return self.roi.xrt_set(self.element)

    @property
    def non_zero_interval(self) -> Interval:
        """The ``Interval`` containing all non-zero channels in the `self.data`."""
        return self._non_zero_interval

    @property
    def data(self) -> npt.NDArray[np.floating]:
        """Returns the filtered data."""
        return self._data

    @property
    def error_data(self) -> npt.NDArray[np.floating]:
        """Returns an array of sqrt(n) estimated measurement errors."""
        return self._error_data

    @property
    def normalization(self) -> float:
        """The factor to normalize the spectrum based on its dose."""
        return self._normalization

    def counts(self, i) -> float:
        return self.data[i] if i < len(self.data) else 0.0
