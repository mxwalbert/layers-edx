import copy
import math
from typing import Callable
import numpy as np
from numpy import typing as npt
from layers_edx.spectrum.spectrum_properties import SpectrumProperties


def bound(x: int, lower_inclusive: int, upper_exclusive: int) -> int:
    """
    Returns `x` bounded so that it exists on the interval
    [lower_inclusive, upper_exclusive).
    """
    if x < lower_inclusive:
        return lower_inclusive
    if x >= upper_exclusive:
        return upper_exclusive - 1
    return x


def linear_regression(x: npt.ArrayLike, y: npt.ArrayLike) -> tuple[Callable, float]:
    """
    Returns the least-squares solution of a 1-dimensional linear equation,
    i.e., (y_hat, chi2).
    """

    a = np.vstack([x, np.ones(len(x))]).T
    solution = np.linalg.lstsq(a, y, rcond=None)

    def y_hat(x_i):
        return solution[0][0] * x_i + solution[0][1]

    return y_hat, math.sqrt(solution[1][0]) / len(x)


def mean(data: npt.ArrayLike) -> float:
    """Computes the mean of the provided data."""
    return sum(data) / len(data)


def variance(data: npt.ArrayLike) -> float:
    """Computes the variance of the provided data."""
    return sum((x - mean(data)) ** 2 for x in data) / (len(data) - 1)


def standard_error(data: npt.ArrayLike) -> float:
    """Computes the standard error of the provided data."""
    return math.sqrt(variance(data) / len(data))


class BaseSpectrum:
    def __init__(
        self, properties: SpectrumProperties, data: npt.NDArray[np.floating] = None
    ):
        self._properties = properties
        self._data = data
        self._current_scale = 1.0

    @property
    def properties(self) -> SpectrumProperties:
        """Returns the ``SpectrumProperties`` object belonging to the spectrum."""
        return self._properties

    @property
    def data(self) -> npt.NDArray[np.floating]:
        """Returns the counts for each channel in an array."""
        if self._data is None:
            return np.array([self.counts(i) for i in range(self.channel_count)])
        return self._data

    @property
    def channel_count(self) -> int:
        """Returns the number of channels in the spectrum."""
        raise NotImplementedError

    @property
    def channel_width(self) -> float:
        """Returns the width of each channel (in eV)."""
        return self.properties.channel_width

    @property
    def zero_offset(self) -> float:
        """Returns the energy of the first channel."""
        return self.properties.zero_offset

    @property
    def zero_peak_discriminator_channel(self):
        """Returns the channel index of the zero strobe peak."""
        return self.channel_from_energy(self.properties.zero_peak_discriminator)

    @property
    def smallest_nonzero_channel(self) -> int:
        """Returns the index of the smallest channel containing non-zero counts."""
        lld = self.zero_peak_discriminator_channel
        return lld + int(np.argmax(self.data[lld:] != 0))

    def __copy__(self) -> "BaseSpectrum":
        return BaseSpectrum(copy.copy(self.properties), self.data.copy())

    def copy(self) -> "BaseSpectrum":
        """
        Generates a new instance with a shallow copy of the `properties` and
        a deep copy of the `data`.
        """
        return self.__copy__()

    def apply_zero_peak_discriminator(self):
        """Sets the channels below the zero peak discriminator channel to 0."""
        self.data[: self.zero_peak_discriminator_channel] = 0

    def scale(self, factor: float):
        """Scales the spectrum `data` by the specified factor."""
        self._data *= factor
        self._current_scale /= factor

    def reset_scale(self):
        """Resets the spectrum `data` to its original scale."""
        self.scale(self._current_scale)

    def counts(self, i: int) -> float:
        """Returns the counts in the `i`-th channel"""
        if self._data is None:
            return 0.0
        return self._data[i].item()

    def bound(self, channel: int) -> int:
        """
        Returns `channel` bounded so that it exists on the interval 0 to
        `self.channel_count`-1.
        """
        return bound(channel, 0, self.channel_count)

    def channel_from_energy(self, energy: float) -> int:
        """
        Returns the index of the channel which contains the specified `energy` (eV).
        """
        return int((energy - self.zero_offset) / self.channel_width)

    def min_energy_from_channel(self, channel: int) -> float:
        """Returns the energy on the lower side of the `channel` bin in eV."""
        return self.zero_offset + (channel * self.channel_width)

    def max_energy_from_channel(self, channel: int) -> float:
        """Returns the energy on the upper side of the `channel` bin in eV."""
        return self.min_energy_from_channel(channel + 1)

    def average_energy_from_channel(self, channel: int) -> float:
        return self.zero_offset + (channel + 0.5) * self.channel_width

    def estimate_background(
        self, mode: str, start: int, min_bins: int = 5, max_bins: int = 50
    ) -> tuple[float, float, int]:
        """
        Estimate the background starting at the channel `start` heading towards the
        channel limit, specified by `mode` ("low" or "high"). Uses at least `min_bins`
        but as many as `max_bins` channels to minimize the error estimate in the
        background level.
        """
        direction = None
        limit = 0
        if mode == "low":
            direction = -1
        elif mode == "high":
            direction = 1
            limit = self.channel_count - 1
        if direction is None or not (0 < start < self.channel_count - 1):
            return self.counts(limit), self.counts(limit), limit
        end = self.bound(start + direction * min_bins)
        x, y = zip(
            *[
                (channel, self.counts(channel))
                for channel in range(start, end + direction, direction)
            ]
        )
        y_hat, best_error = linear_regression(x, y)
        best_channel = end
        best_result = y_hat(start)
        if best_error < 2.0:
            end = self.bound(start + direction * max_bins)
            for channel in range(
                start + direction * (min_bins + 1), end + direction, direction
            ):
                x.append(channel)
                y.append(self.counts(channel))
                y_hat, error = linear_regression(x, y)
                if error < best_error:
                    best_error = error
                    best_channel = channel
                    best_result = y_hat(start)
            best_error = math.sqrt(best_result) * best_error
        else:
            best_channel = start
            best_result = self.counts(best_channel)
            y = [best_result]
            best_error = math.sqrt(best_result)
            for channel in range(start + direction, end + direction, direction):
                y.append(self.counts(channel))
                error = standard_error(y)
                if error < best_error:
                    best_error = error
                    best_result = mean(y)
        return (
            best_result,
            max((1.0, best_error)),
            1 + direction * (best_channel - start),
        )

    def background_corrected_integral(self, e_low: float, e_high: float):
        """
        Computes the background corrected integral over the specified range of energies
        (e_low, e_high). The width of the regions above and below the peak that is used
        to estimate the background is adapted dynamically to reduce the standard
        deviation in the background estimate.
        """
        min_channel = self.bound(self.channel_from_energy(e_low))
        max_channel = self.bound(self.channel_from_energy(e_high))
        low = self.estimate_background("low", min_channel - 1)
        high = self.estimate_background("high", max_channel + 1)
        above = 0.5 * (low[0] + high[0]) * ((max_channel - min_channel) + 1)
        if (low[0] + high[0]) != 0.0:
            dev_above = (
                math.sqrt((low[1] * low[1]) + (high[1] * high[1])) / (low[0] + high[0])
            ) * above
        else:
            dev_above = 1.0
        integral = 0.0
        for channel in range(min_channel, max_channel + 1):
            integral += self.counts(channel)
        return (
            integral - above,
            math.sqrt(dev_above * dev_above + integral),
            integral,
            above,
        )
