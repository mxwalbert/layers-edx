from abc import ABC, abstractmethod
import copy
import numpy.typing as npt


class Filter(ABC):
    """An abstract base class defining the structure for filters for filter fitting spectra."""

    @staticmethod
    def default_variance_correction_factor(lw: float, uw: float) -> float:
        return (2.0 * uw * lw) / (uw + (2.0 * lw))

    def __init__(self, width: float, channel_width: float):
        self._filter = None
        self._variance_correction_factor = None
        self._width = width
        self._channel_width = channel_width
        self._initialize_filter()

    @property
    def filter(self) -> npt.NDArray[float]:
        return copy.copy(self._filter)

    @property
    def variance_correction_factor(self) -> float:
        return self._variance_correction_factor

    @property
    def width(self) -> float:
        return self._width

    @property
    def channel_width(self) -> float:
        return self._channel_width

    @property
    def filter_width(self) -> float:
        """Returns the width of the filter in eV."""
        if self.filter is None:
            return float('nan')
        return self.channel_width * len(self.filter)

    @abstractmethod
    def _initialize_filter(self):
        """Implements the actual filter logic. Populates the `self._filter` and `self._variance_correction_factor`."""


class TopHatFilter(Filter):
    """StandardROIs top-hat style filter (as per Schamber)"""

    def _initialize_filter(self):
        # (2*m+1)*self.channel_width ~ self.filter_width
        m = max(int(round(self.width / self.channel_width)) - 1 // 2, 2)
        n = m
        filter_len = (2 * n) + (2 * m) + 1
        new_filter = [-1.0 if i < n or i >= n + (2 * m) + 1 else 0 for i in range(filter_len)]
        k = (2.0 * n) / ((2.0 * m) + 1.0)
        for i in range((2 * m) + 1):
            new_filter[i + n] = k
        self._filter = new_filter
        self._variance_correction_factor = self.default_variance_correction_factor(m, 2 * m + 1)
