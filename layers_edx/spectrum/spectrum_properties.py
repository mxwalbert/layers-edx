import math
import numpy as np
from dataclasses import dataclass
from functools import cached_property
from typing import Optional
from numpy import typing as npt
from layers_edx.detector.detector import TDetector
from layers_edx.element import Composition


def unit_vector(vector: npt.NDArray[float]):
    """ Returns the unit vector of the provided vector."""
    return vector / np.linalg.norm(vector)


def angle_between(v1: npt.NDArray[float], v2: npt.NDArray[float]) -> float:
    """ Returns the angle in radians between vectors `v1` and `v2` in radians (rad)."""
    v1_u = unit_vector(v1)
    v2_u = unit_vector(v2)
    return np.arccos(np.clip(np.dot(v1_u, v2_u), -1.0, 1.0))


@dataclass(frozen=True)
class SpectrumProperties:
    """
    Represents the properties of a spectrum collected using a detector.

    Attributes:
        detector (TDetector): The detector object on which this spectrum was collected. Default is None.
        beam_energy (float): The energy of the electron probe in keV. Default is 20.0.
        probe_current (float): A measurement of the probe current in nanoamperes (nA). Default is 1.0.
        live_time (float): The amount of time during which the detector was available to process x-ray events in seconds (s). Default is 60.0.
        working_distance (float): The distance between the beam exit and the sample surface in millimeters (mm). Default is NaN.
        zero_peak_discriminator (float): The energy of the zero stabilization peak in electronvolt (eV). Default is 0.0.
        standard_composition (Optional[Composition]): The composition of the sample as determined by an independent method.
        microanalytical_composition (Optional[Composition]): The best microanalytically derived understanding of composition of the sample.
    """

    detector: TDetector = None
    beam_energy: float = 20.0
    probe_current: float = 1.0
    live_time: float = 60.0
    working_distance: float = 10.0 if detector is None else detector.position.optimal_working_distance
    zero_peak_discriminator: float = 0.0
    standard_composition: Optional[Composition] = None
    microanalytical_composition: Optional[Composition] = None

    @cached_property
    def dose(self) -> float:
        """
        The probe dose derived from the probe current and live time.

        Returns:
            float: The probe dose in nanoampere-seconds (nA.s).
        """
        return self.probe_current * self.live_time

    @cached_property
    def sample_position(self) -> npt.NDArray [float]:
        """
        The coordinates of the sample derived from the working distance.

        Returns:
            float: The sample position in millimeter (mm).
        """
        return np.array([0.0, 0.0, self.working_distance])

    @cached_property
    def take_off_angle(self) -> float:
        """
        The angle at which the beam comes off of the sample.

        Returns:
            float: The take-off angle in radians.
        """
        if self.detector is None:
            return math.radians(45.0)
        vec = self.detector.position.coordinates - self.sample_position
        return np.pi / 2.0 - angle_between(vec, np.array([0.0, 0.0, -1.0]))

    @cached_property
    def sample_distance(self) -> float:
        """
        Returns the sample to detector distance in meters.

        Raises:
            NotImplementedError: This method is not implemented.
        """
        return float(np.linalg.norm(self.detector.position.coordinates - self.sample_position))

    @property
    def channel_width(self) -> float:
        """
        Gets the detector's energy width of a single channel.

        Returns:
            float: The channel width in electron volts (eV).
        """
        return self.detector.calibration.channel_width

    @property
    def zero_offset(self) -> float:
        """
        Gets the detector's energy offset of the first channel from zero.

        Returns:
            float: The zero offset in electron volts (eV).
        """
        return self.detector.calibration.zero_offset
