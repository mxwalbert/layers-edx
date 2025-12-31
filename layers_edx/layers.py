from __future__ import annotations
import math
import scipy
from typing import Type
from layers_edx.atomic_shell import AtomicShell
from layers_edx.correction import NoCorrection, PhiRhoZ
from layers_edx.correction.pap import PAP
from layers_edx.element import Composition
from layers_edx.simulation import BasicSimulator
from layers_edx.spectrum.spectrum_properties import SpectrumProperties
from layers_edx.xrt import XRayTransition


def corrected_intensities(
    layers: list[Layer], xrts: set[XRayTransition] = None
) -> dict[XRayTransition, float]:
    intensities = {}
    for layer in layers:
        for xrt, ideal_intensity in layer.ideal_intensities.items():
            if xrts is not None and xrt not in xrts:
                continue
            result = intensities[xrt] if xrt in intensities else 0.0
            result += (
                ideal_intensity
                * layer.upper_layer_absorption(xrt, layers)
                * layer.emitted_intensity(xrt, layers)
            )
            intensities[xrt] = result
    return intensities


class Layer:
    def __init__(
        self,
        composition: Composition,
        mass_thickness: float,
        properties: SpectrumProperties,
        fixed_composition: bool = False,
        fixed_thickness: bool = False,
        algorithm_class: Type[PhiRhoZ] = PAP,
    ):
        self._composition: Composition = composition
        self._mass_thickness: float = mass_thickness
        self.composition_history: list[Composition] = []
        self.mass_thickness_history: list[float] = []
        self.properties = properties
        self.fixed_composition = fixed_composition
        self.fixed_thickness = fixed_thickness
        self.algorithm_class = algorithm_class
        self._algorithms: dict[AtomicShell, algorithm_class] = {}
        self._intensities = None

    @property
    def composition(self) -> Composition:
        return self._composition

    @composition.setter
    def composition(self, new: Composition):
        self._algorithms = {}
        self._intensities = None
        self.composition_history.append(self.composition.copy())
        self._composition = new

    @property
    def mass_thickness(self) -> float:
        return self._mass_thickness

    @mass_thickness.setter
    def mass_thickness(self, new: float):
        self.mass_thickness_history.append(self.mass_thickness)
        self._mass_thickness = new

    def rho_z(self, layers: list[Layer]) -> float:
        return sum([layer.mass_thickness for layer in layers[: layers.index(self)]])

    def algorithm(self, shell: AtomicShell) -> PhiRhoZ:
        if shell not in self._algorithms:
            self._algorithms[shell] = self.algorithm_class(
                self.composition, shell, self.properties
            )
        return self._algorithms[shell]

    @property
    def ideal_intensities(self) -> dict[XRayTransition, float]:
        """
        The non-corrected intensities which are emitted by the atoms in this layer.
        """
        if self._intensities is None:
            bss = BasicSimulator(self.composition, self.properties, ca=NoCorrection)
            self._intensities = bss.emitted_intensities
        return self._intensities

    def upper_layer_absorption(self, xrt: XRayTransition, layers: list[Layer]) -> float:
        """Calculates the absorption of the layer's radiation by the layers above it."""
        result = 1.0
        for i, layer in enumerate(layers[1 : layers.index(self)]):
            delta_chi = self.algorithm(xrt.destination).chi(xrt) - layer.algorithm(
                xrt.destination
            ).chi(xrt)
            result *= math.exp(layer.mass_thickness * delta_chi)
        return result

    def intensity_distribution(self, xrt: XRayTransition, rho_z: float) -> float:
        """The right part under the integral of equation (6) in PouchouPichoir1993."""
        algorithm = self.algorithm(xrt.destination)
        return algorithm.compute_curve(rho_z) * math.exp(-algorithm.chi(xrt) * rho_z)

    def emitted_intensity(self, xrt: XRayTransition, layers: list[Layer]) -> float:
        """
        The integration of the intensity distribution from the top to
        the bottom of the layer.
        """
        top = self.rho_z(layers)
        bottom = top + self.mass_thickness
        return scipy.integrate.quad(
            lambda x: self.intensity_distribution(xrt, x), top, bottom
        )[0]
