import numpy as np
from numpy import typing as npt
from layers_edx.detector.detector import Detector, DetectorProperties, DetectorPosition, EDSCalibration
from layers_edx.element import Element
from layers_edx.spectrum.base_spectrum import BaseSpectrum
from layers_edx.units import FromSI
from layers_edx.xrt import XRayTransition, XRayTransitionSet


class EDSDetector(Detector):

    def __init__(self, properties: DetectorProperties, position: DetectorPosition, calibration: EDSCalibration):
        super().__init__(properties, position, calibration)
        self._dirty = True
        self._accumulator = None
        self._spectrum = None
        self._efficiency = self.calibration.get_efficiency(self.properties)

    @property
    def calibration(self) -> EDSCalibration:
        return self._calibration

    @property
    def dirty(self) -> bool:
        """Flags if the `spectrum` needs recalculation."""
        return self._dirty

    @dirty.setter
    def dirty(self, value: bool):
        self._dirty = value

    @property
    def accumulator(self) -> npt.NDArray[int]:
        if self._accumulator is None:
            self._accumulator = np.zeros(self.properties.channel_count)
        return self._accumulator

    @property
    def spectrum(self) -> BaseSpectrum:
        """The current spectrum representing the detected x-rays."""
        return self._spectrum

    @property
    def efficiency(self) -> npt.NDArray[float]:
        """Returns the detector efficiency from the calibration."""
        return self._efficiency

    def reset(self):
        self.dirty = True
        self._accumulator = None
        self._spectrum = None

    def add_event(self, energy: float, intensity: float):
        channel = self.spectrum.channel_from_energy(FromSI.ev(energy))
        if 0 <= channel < len(self.accumulator):
            self.accumulator[channel] += intensity
            self.dirty = True

    def convolve(self, min_i=1e-4):
        """Takes the events in the `accumulator` and convolves them into the existing `spectrum`. Should be called
        after new events are recorded by the detector."""
        dlm = self.calibration.model
        spec = self.spectrum
        ch_width = self.calibration.channel_width
        fs = ch_width * self.calibration.fudge_factor * self.efficiency * self.accumulator
        spec.data.fill(0.0)
        for i in range(fs.shape[0]):
            if fs[i] > 0.0:
                e = spec.min_energy_from_channel(i)
                high_bin = spec.bound(spec.channel_from_energy(e + dlm.right_width(e, min_i)))
                low_bin = spec.bound(spec.channel_from_energy(e - dlm.left_width(e, min_i)))
                ee = spec.min_energy_from_channel(low_bin)
                prev = dlm.compute(ee, e)
                for ch in range(low_bin, high_bin):
                    curr = dlm.compute(ee + ch_width, e)
                    spec.data[ch + 1] += 0.5 * fs[i] * (prev + curr)
                    prev = curr
                    ee += ch_width
        self.dirty = False

    def scaled_spectrum(self, scale: float) -> BaseSpectrum:
        if self.dirty:
            self.convolve()
            self.dirty = False
        return self.spectrum.scale(scale)

    def is_visible(self, xrt: XRayTransition, energy: float) -> bool:
        """Checks if the provided `xrt` is visible at the specified beam energy."""
        return self.calibration.is_visible(xrt, energy)

    def visible_xrts(self, element: Element, max_energy: float) -> XRayTransitionSet:
        """Constructs the full set of ``XRayTransitions`` of edge energy less than `max_energy` which can reasonably be
        expected to be visible with this detector."""
        xrt_set = XRayTransitionSet.all_xrts(element, max_energy)
        for xrt in xrt_set.xrts.copy():
            if not self.is_visible(xrt, max_energy):
                xrt_set.remove(xrt)
        return xrt_set
