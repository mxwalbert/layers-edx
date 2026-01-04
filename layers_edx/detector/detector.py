from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from functools import cached_property
from typing import TypeVar
import math
import numpy as np
import numpy.typing as npt
from layers_edx.detector.lineshape_model import LineshapeModel, FanoSiLiLineshape
from layers_edx.units import ToSI
from layers_edx.xrt import XRayTransition
from layers_edx.element import Element, Material
from layers_edx.material_properties.mac import MassAbsorptionCoefficient


@dataclass(frozen=True)
class XRayWindowLayer:
    """
    Represents a layer of the window of an x-ray detector.

    Attributes:
        material (Material): The material of the layer.
        thickness (float): The thickness of the layer in nanometers (nm).
    """

    material: Material
    thickness: float

    def mac(self, energy: float) -> float:
        """
        Calculates the mass absorption coefficient of the layer at the specified energy.

        Args:
            energy (float): The energy of the x-ray beam in joules (J).

        Returns:
            float: The mass absorption coefficient of the layer at the given energy in
            square metre per kilogram (m²/kg).
        """
        result = MassAbsorptionCoefficient.compute_composition(
            self.material.composition, energy
        )
        return result * ToSI.gpcm3(self.material.density) * ToSI.nm(self.thickness)


@dataclass
class XRayWindow:
    """
    Represents the window of an x-ray detector.

    Attributes:
    - open_fraction (float): The fraction of the window that is not blocked.
    Default is 1.0.
    - layers (list[XRayWindowLayer]): The layers of materials which are stacked
    to form the x-ray window. Defaults to an empty list.
    """

    open_fraction: float = 1.0
    layers: list[XRayWindowLayer] = field(default_factory=list)

    def mac(self, energy: float) -> float:
        """
        Calculates the mass absorption coefficient of the x-ray window at the
        specified energy.

        Args:
            energy (float): The energy of the x-ray beam in joules (J).

        Returns:
            float: The mass absorption coefficient of the window at the given energy
            in square metre per kilogram (m²/kg).
        """
        return sum([layer.mac(energy) for layer in self.layers])

    def transmission(self, energy: float) -> float:
        """
        Computes the fraction of the incident beam which is transmitted
        through the window.

        Args:
            energy (float): The energy of the x-ray beam in joules (J).

        Returns:
            float: The fraction of the incident beam transmitted through the window.
        """
        return self.open_fraction * math.exp(-self.mac(energy))

    def absorption(self, energy: float) -> float:
        """
        Computes the fraction of the incident beam which is absorbed by the window.

        Args:
            energy (float): The energy of the x-ray beam in joules (J).

        Returns:
            float: The fraction of the incident beam absorbed by the window.
        """
        return 1.0 - self.transmission(energy)


class GridMountedWindow(XRayWindow):
    def __init__(
        self,
        grid_material: Material,
        grid_thickness: float,
        open_fraction: float = 1.0,
        layers: list[XRayWindowLayer] | None = None,
    ):
        super().__init__(open_fraction, layers)
        self._grid = XRayWindowLayer(grid_material, grid_thickness)

    @property
    def grid(self) -> XRayWindowLayer:
        """The grid material and thickness represented as ``XRayWindowLayer``."""
        return self._grid

    def transmission(self, energy: float) -> float:
        grid_transmission = self.open_fraction + (1.0 - self.open_fraction) * math.exp(
            -self.grid.mac(energy)
        )
        return super().transmission(energy) / self.open_fraction * grid_transmission


@dataclass(frozen=True)
class DetectorProperties:
    """
    A class to represent the properties of a detector.

    Attributes:
    - channel_count (int): The number of channels for binning the detected x-ray beams.
    - area (float): The active surface area of the detector (mm²).
    - thickness (float): The thickness of the active detector volume (mm).
    - dead_layer (float): The thickness of the non-active silicone layer coating the
    surface of the detector (µm). Default is 0.0.
    - gold_layer (float): The thickness of the gold layer coating the surface of the
    detector (nm). Default is 0.0.
    - aluminium_layer (float): The thickness of the aluminium layer coating the surface
    of the detector (nm). Default is 0.0.
    - nickel_layer (float): The thickness of the nickel layer coating the surface of the
    detector (nm). Default is 0.0.
    - window (XRayWindow): The `XRayWindow` which covers the detector. Defaults to
    a transparent window.
    """

    channel_count: int = 1000
    area: float = 100.0
    thickness: float = 1.0
    dead_layer: float = 0.0
    gold_layer: float = 0.0
    aluminium_layer: float = 0.0
    nickel_layer: float = 0.0
    window: XRayWindow = field(default_factory=XRayWindow)


@dataclass(frozen=True)
class DetectorPosition:
    """
    A class to represent the position of a detector.

    Attributes:
    - elevation (float): The elevation angle of the detector (deg). Default is 40.0.
    - azimuth (float): The azimuth angle of the detector (deg). Default is 0.0.
    - sample_distance (float): The distance from the detector to the sample at the
    optimal working distance (mm). Default is 60.0.
    - optimal_working_distance (float): The optimal working distance of
    the detector (mm). Default is 20.0.
    """

    elevation: float = 40.0
    azimuth: float = 0.0
    sample_distance: float = 60.0
    optimal_working_distance: float = 20.0

    @cached_property
    def orientation(self) -> npt.NDArray[np.floating]:
        el = np.deg2rad(self.elevation)
        az = np.deg2rad(self.azimuth)
        return np.array(
            [-np.cos(el) * np.cos(az), -np.cos(el) * np.sin(az), np.sin(el)]
        )

    @cached_property
    def coordinates(self) -> npt.NDArray[np.floating]:
        return (
            np.array([0, 0, self.optimal_working_distance])
            - self.sample_distance * self.orientation
        )


class DetectorCalibration(ABC):
    def __init__(self, channel_width: float = 1.0, zero_offset: float = 0.0):
        self._channel_width = channel_width
        self._zero_offset = zero_offset

    @property
    def channel_width(self) -> float:
        """The energy width of a single channel (eV)."""
        return self._channel_width

    @property
    def zero_offset(self) -> float:
        """The energy offset of the first channel from zero (eV)."""
        return self._zero_offset

    @abstractmethod
    def get_efficiency(
        self, properties: DetectorProperties
    ) -> npt.NDArray[np.floating]:
        """Computes the detector efficiency given the detector's properties."""

    @abstractmethod
    def is_visible(self, xrt: XRayTransition, energy: float) -> bool:
        """Checks if the provided `xrt` is visible at the specified beam `energy."""


TDetectorCalibration = TypeVar("TDetectorCalibration", bound=DetectorCalibration)


class EDSCalibration(DetectorCalibration):
    MIN_OVERVOLTAGE = 1.1
    FIRST_ELEMENT = [Element("Ca"), Element("B"), Element("La"), Element("Am")]

    def __init__(
        self,
        channel_width: float = 1.0,
        zero_offset: float = 0.0,
        fwhm_at_mn_ka: float = 1.0,
        fano: float = 1.0,
        noise: float = 1.0,
        model: LineshapeModel | None = None,
    ):
        super().__init__(channel_width, zero_offset)
        self._fudge_factor = 1.0
        self._model = (
            FanoSiLiLineshape(fwhm_at_mn_ka, fano, noise) if model is None else model
        )

    @property
    def fudge_factor(self) -> float:
        """A factor to deal with global intensity (scale) errors."""
        return self._fudge_factor

    @property
    def model(self) -> LineshapeModel:
        """The lineshape model of this calibration."""
        return self._model

    def get_efficiency(
        self, properties: DetectorProperties
    ) -> npt.NDArray[np.floating]:
        """
        Computes the detector efficiency given the detector properties `properties`.
        """

        mac = MassAbsorptionCoefficient.compute

        si, au, al, ni = [Element(element) for element in ["Si", "Au", "Al", "Ni"]]
        active_mt = ToSI.gpcm3(Material(si).density) * ToSI.mm(properties.thickness)
        dead_mt = ToSI.gpcm3(Material(si).density) * ToSI.um(properties.dead_layer)
        au_mt = ToSI.gpcm3(Material(au).density) * ToSI.nm(properties.gold_layer)
        al_mt = ToSI.gpcm3(Material(al).density) * ToSI.nm(properties.aluminium_layer)
        ni_mt = ToSI.gpcm3(Material(ni).density) * ToSI.nm(properties.nickel_layer)

        data = np.array(
            [
                ToSI.ev(self.channel_width * (i + 0.5) + self.zero_offset)
                for i in range(properties.channel_count)
            ]
        )

        def func(e: float) -> float:
            result = 1.0
            result *= properties.window.transmission(e)
            result *= 1 - math.exp(-mac(si, e) * active_mt)
            result *= math.exp(-mac(si, e) * dead_mt)
            result *= math.exp(-mac(au, e) * au_mt)
            result *= math.exp(-mac(al, e) * al_mt)
            result *= math.exp(-mac(ni, e) * ni_mt)
            return result

        return (
            np.vectorize(func)(data)
            * ToSI.mm2(properties.area)
            * (1.0 / (4.0 * math.pi))
        )

    def is_visible(self, xrt: XRayTransition, energy: float) -> bool:
        """Checks if the specified `xrt` is visible at this beam `energy`."""
        if xrt.edge_energy > (energy / self.MIN_OVERVOLTAGE):
            return False
        for family, element in enumerate(self.FIRST_ELEMENT):
            if xrt.family == family:
                return xrt.element.atomic_number >= element.atomic_number
        return False


class Detector(ABC):
    def __init__(
        self,
        properties: DetectorProperties,
        position: DetectorPosition,
        calibration: DetectorCalibration,
    ):
        self._properties = properties
        self._position = position
        self._calibration = calibration

    @property
    def properties(self) -> DetectorProperties:
        """The detector's ``DetectorProperties`` object."""
        return self._properties

    @property
    def position(self) -> DetectorPosition:
        """The detector's ``DetectorPosition`` object."""
        return self._position

    @property
    def calibration(self) -> DetectorCalibration:
        """The detector's ``DetectorCalibration`` object."""
        return self._calibration

    @abstractmethod
    def reset(self):
        """Clear the internal data object to prepare for collecting a new spectrum."""

    @abstractmethod
    def add_event(self, energy: float, intensity: float):
        """
        Add an x-ray of the specified energy and intensity
        (1.0 for a full, single x-ray) to the internal data
        object. The intensity is scaled to account for distance from the point of
        generation to the detector.
        """


TDetector = TypeVar("TDetector", bound=Detector)
