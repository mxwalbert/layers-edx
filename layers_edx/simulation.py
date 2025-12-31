import math
from abc import ABC, abstractmethod
from typing import Type
from layers_edx.atomic_shell import AtomicShell
from layers_edx.correction import Correction
from layers_edx.correction.xpp import XPP
from layers_edx.detector.eds_detector import EDSDetector
from layers_edx.element import Composition
from layers_edx.material_properties.ics import AbsoluteIonizationCrossSection
from layers_edx.material_properties.tp import TransitionProbabilities
from layers_edx.spectrum.spectrum_properties import SpectrumProperties
from layers_edx.units import FromSI, ToSI, PhysicalConstants
from layers_edx.xrt import XRayTransition


class SpectrumSimulator(ABC):
    def __init__(
        self,
        composition: Composition,
        properties: SpectrumProperties,
        shells: set[AtomicShell] | None = None,
    ):
        self._composition = composition
        self._properties = properties
        if shells is None:
            self._shells: set[AtomicShell] = set()
            self.create_shell_set()
        else:
            self._shells = shells

    def create_shell_set(self):
        e0 = ToSI.kev(self.properties.beam_energy)
        for element, fraction in self.composition.raw_weight_fractions.items():
            if fraction <= 0.0:
                continue
            for name in AtomicShell.NAME[:9]:
                shell = AtomicShell(element, name)
                if shell.edge_energy < e0:
                    self.shells.add(shell)

    @property
    def composition(self) -> Composition:
        return self._composition

    @property
    def properties(self) -> SpectrumProperties:
        return self._properties

    @property
    def shells(self) -> set[AtomicShell]:
        return self._shells

    @property
    @abstractmethod
    def emitted_intensities(self) -> dict[XRayTransition, float]:
        pass

    @property
    def measured_intensities(self) -> dict[XRayTransition, float]:
        detector: EDSDetector = self.properties.detector
        scale = 1.0 / (4.0 * math.pi * self.properties.sample_distance**2)
        result: dict[XRayTransition, float] = {}
        for xrt, intensity in self.emitted_intensities.items():
            channel = int(
                (FromSI.ev(xrt.energy) - detector.calibration.zero_offset)
                / detector.calibration.channel_width
            )
            if 0 <= channel < detector.efficiency.shape[0]:
                result[xrt] = intensity * scale * float(detector.efficiency[channel])
        return result


class BasicSimulator(SpectrumSimulator):
    def __init__(
        self,
        composition: Composition,
        properties: SpectrumProperties,
        shells: set[AtomicShell] | None = None,
        ca: Type[Correction] = XPP,
        tp: Type[TransitionProbabilities] = TransitionProbabilities,
        aics: Type[AbsoluteIonizationCrossSection] = AbsoluteIonizationCrossSection,
    ):
        super().__init__(composition, properties, shells)
        self.ca = ca
        self.tp = tp
        self.aics = aics

    @property
    def emitted_intensities(self) -> dict[XRayTransition, float]:
        result: dict[XRayTransition, float] = {}
        e0 = ToSI.kev(self.properties.beam_energy)
        dose = self.properties.dose * 1e-9 / PhysicalConstants.ElementaryCharge
        for shell in self.shells:
            if shell.exists and shell.energy < e0:
                ca = self.ca(self.composition, shell, self.properties)
                ics = (
                    self.aics.compute_shell(shell, e0)
                    * dose
                    * self.composition.atoms_per_kg[shell.element]
                )
                for xrt, w in self.tp.transitions(shell, 0.0).items():
                    if w >= 1e-5:
                        s = result[xrt] if xrt in result else 0.0
                        s += w * ics * ca.compute_zaf_correction(xrt)
                        if not math.isnan(s):
                            result[xrt] = s
        return result
