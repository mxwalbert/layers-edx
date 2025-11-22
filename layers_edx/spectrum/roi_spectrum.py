from __future__ import annotations
from typing import Callable
import numpy as np
from numpy import typing as npt
from layers_edx.bremsstrahlung import Castellano2004aBremsstrahlung
from layers_edx.roi import RegionOfInterest
from layers_edx.spectrum.base_spectrum import BaseSpectrum, linear_regression
from layers_edx.spectrum.derived_spectrum import DerivedSpectrum
from layers_edx.units import FromSI, ToSI
from layers_edx.xrt import XRayTransitionSet


class ROISpectrumNaive(DerivedSpectrum):
    """A mechanism for extracting the channel counts in a ROI from a spectrum, based on fitting the background."""

    def __init__(self, spectrum: BaseSpectrum, roi: RegionOfInterest, model_thresh: float = 1.0e3):
        """Initializes a ``DerivedSpectrum`` based on the provided `spectrum` for the specified `roi`."""
        super().__init__(spectrum)
        self._roi = roi
        self._low_channel = self.source.bound(spectrum.channel_from_energy(FromSI.ev(roi.low_energy)))
        self._high_channel = self.source.bound(spectrum.channel_from_energy(FromSI.ev(roi.high_energy)))
        self._model_thresh = model_thresh

    @property
    def roi(self) -> RegionOfInterest:
        """The `RegionOfInterest` for which this spectrum is derived."""
        return self._roi

    @property
    def low_channel(self) -> int:
        """The channel which represents the lower energy limit of the `self.roi`."""
        return self._low_channel

    @property
    def high_channel(self) -> int:
        """The channel which represents the upper energy limit of the `self.roi`."""
        return self._high_channel

    @property
    def model_thresh(self) -> float:
        """The threshold energy in eV below which the background will be modeled."""
        return self._model_thresh

    def counts(self, i: int) -> float:
        if self.data is None:
            self._compute_data()
        return self.data[i].item()

    def _fit_background(self, channel: int, bg_extent: int = 3) -> tuple[Callable, float]:
        x = [self.source.bound(channel + i) for i in range(-bg_extent, bg_extent + 1)]
        y = [self.source.counts(xi) for xi in x]
        return linear_regression(x, y)

    def _compute_data(self):
        data = np.zeros(self.high_channel - self.low_channel)
        if self.min_energy_from_channel(self.low_channel) >= self.model_thresh:
            self._compute_default(data)
            return
        low = self._fit_background(self.low_channel)[0]
        high = self._fit_background(self.high_channel)[0]
        edge = XRayTransitionSet.from_xrts(self.roi.xrts).weightiest_transition.destination
        edge_channel = self.source.channel_from_energy(FromSI.ev(edge.edge_energy))
        if not (self.low_channel < edge_channel < self.high_channel and low(edge_channel) > high(edge_channel)):
            self._compute_default(data)
            return
        width = int(round(self.roi.model.fwhm_at_mn_ka / self.source.channel_width)) // 2
        low_edge = max((self.low_channel, edge_channel - width))
        high_edge = min((self.high_channel, edge_channel + width))
        for i in range(self.low_channel, low_edge):
            data[i - self.low_channel] = self.source.counts(i) - low(i)
        line = linear_regression([low_edge, high_edge], [low(low_edge), high(high_edge)])[0]
        for i in range(low_edge, high_edge):
            data[i - self.low_channel] = self.source.counts(i) - line(i)
        for i in range(high_edge, self.high_channel):
            data[i] = self.source.counts(i) - high(i)
        self._data = data

    def _compute_default(self, data: npt.NDArray):
        low_bg = self.source.estimate_background('low', self.low_channel)[0]
        high_bg = self.source.estimate_background('high', self.high_channel)[0]
        for i in range(self.low_channel, self.high_channel):
            h = low_bg + (high_bg - low_bg) * (i - self.low_channel) / (self.high_channel - self.low_channel)
            data[i - self.low_channel] = self.source.counts(i) - h
        self._data = data


class ROISpectrum(ROISpectrumNaive):

    def _compute_data(self):
        data = np.zeros(self.high_channel - self.low_channel)
        if self.min_energy_from_channel(self.low_channel) >= self.model_thresh:
            self._compute_default(data)
            return
        composition = self.source.properties.standard_composition
        if composition is None:
            composition = self.source.properties.microanalytical_composition
        model = Castellano2004aBremsstrahlung(composition,
                                              ToSI.kev(self.source.properties.beam_energy),
                                              self.source.properties.take_off_angle)
        bg = model.fit_background_composition(self.source.properties.detector, self.source, composition)
        min_source = self.estimate_background('low', self.low_channel)[0]
        max_source = self.estimate_background('high', self.high_channel)[0]
        min_bg = self.estimate_background('low', bg.low_channel)[0]
        max_bg = self.estimate_background('high', bg.high_channel)[0]
        min_sc = min_source / min_bg if min_bg > 0.0 and min_source > 0.0 else float('inf')
        max_sc = max_source / max_bg if max_bg > 0.0 and max_source > 0.0 else float('inf')
        if 0.1 < min_sc < 10.0 and 0.1 < max_sc < 10.0:
            for i in range(self.low_channel, self.high_channel):
                k = (i - self.low_channel) / (self.high_channel - self.low_channel)
                data[i - self.low_channel] = \
                    (self.source.counts(i) - (min_sc + k * (max_sc - min_sc)) * bg.counts(i))
        self._data = data
