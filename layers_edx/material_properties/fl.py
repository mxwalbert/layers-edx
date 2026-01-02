from __future__ import annotations
import math
from typing import Protocol
from layers_edx.material_properties.fym import FluorescenceYieldMean
from layers_edx.material_properties.idr import IonizationDepthRatio
from layers_edx.material_properties.jr import JumpRatio
from layers_edx.material_properties.lc import LeonardCoefficient
from layers_edx.material_properties.mac import MassAbsorptionCoefficient
from layers_edx.atomic_shell import AtomicShell
from layers_edx.element import Composition, Element
from layers_edx.units import FromSI
from layers_edx.xrt import XRayTransition, NAME


class Fluorescence:
    """
    Provides methods to compute the enhancement of X-ray emission due to fluorescence
    from primary X-ray lines in a material.

    X-ray fluorescence occurs when a primary characteristic X-ray emitted from one
    element excites another element in the sample, potentially enhancing its X-ray
    emission.
    """

    @classmethod
    def primary_exciting_line(
        cls, element: Element, shell: AtomicShell
    ) -> XRayTransition | None:
        """
        Determines the most effective X-ray transition in an element that can excite the
        given atomic shell.

        Args:
            element (Element): The element from which the primary X-ray emission
                originates.
            shell (AtomicShell): The atomic shell of interest in the target material.

        Returns:
            (XRayTransition | None): The most suitable exciting X-ray transition, or
                None if no valid transition is found.
        """
        edge_energy = shell.edge_energy
        best_transition = None
        best_weight = 0.0
        best_family = -1
        for transition in range(len(NAME)):
            xrt = XRayTransition(element, transition)
            if xrt.exists and xrt.energy > edge_energy and xrt.family >= best_family:
                weight = xrt.weight()
                if xrt.family > best_family or weight > best_weight:
                    best_transition = xrt
                    best_weight = weight
                    best_family = xrt.family
        return best_transition

    class Algorithm(Protocol):
        """
        Protocol defining the interface for computing secondary fluorescence
        enhancement.
        """

        mac = MassAbsorptionCoefficient
        jr = JumpRatio
        fym = FluorescenceYieldMean
        lc = LeonardCoefficient
        idr = IonizationDepthRatio

        @classmethod
        def compute(
            cls,
            composition: Composition,
            primary: XRayTransition,
            secondary: XRayTransition,
            beam_energy: float,
            take_off_angle: float,
        ) -> float:
            """
            Method for computing the contribution of a primary X-ray line to the
            enhancement of a secondary X-ray line through fluorescence.

            Args:
                composition (Composition): The sample's elemental composition.
                primary (XRayTransition): The primary exciting X-ray transition.
                secondary (XRayTransition): The secondary X-ray transition being
                    enhanced.
                beam_energy (float): The incident electron beam energy (J).
                take_off_angle (float): The detector take-off angle (rad).

            Returns:
                float: The fluorescence enhancement factor (dimensionless).
            """
            ...

    class Reed1993(Algorithm):
        @staticmethod
        def family_factor(secondary_family: int, primary_family: int) -> float:
            if secondary_family == primary_family:
                return 1.0
            if secondary_family == 0 and primary_family == 1:
                return 1.0 / 0.24
            if secondary_family == 1 and primary_family == 0:
                return 0.24
            if secondary_family == 2:
                return 0.02
            return 0.0

        @classmethod
        def compute(
            cls,
            composition: Composition,
            primary: XRayTransition,
            secondary: XRayTransition,
            beam_energy: float,
            take_off_angle: float,
        ) -> float:
            edge_energy = secondary.edge_energy
            if primary.energy < edge_energy:
                return 0.0
            if (
                primary.element not in composition.elements
                or secondary.element not in composition.elements
            ):
                return 0.0
            c_p = composition.weight_fractions[primary.element]
            mac_ps = FromSI.cm2pg(cls.mac.compute(secondary.element, primary.energy))
            mac_p = FromSI.cm2pg(
                cls.mac.compute_composition(composition, primary.energy)
            )
            ionize_f = cls.jr.ionization_fraction(secondary.destination)
            fluor_p = cls.fym.compute(primary.destination)
            a_p = primary.element.atomic_weight
            a_s = secondary.element.atomic_weight
            u = FromSI.cm2pg(
                cls.mac.compute_composition(composition, secondary.energy)
            ) / (math.sin(take_off_angle) * mac_p)
            v = cls.lc.compute(beam_energy, secondary) / mac_p
            ss = cls.idr.compute(primary, secondary, beam_energy)
            f = cls.family_factor(secondary.family, primary.family)
            return (
                f
                * 0.5
                * c_p
                * (mac_ps / mac_p)
                * ionize_f
                * fluor_p
                * (a_s / a_p)
                * ss
                * ((math.log(1.0 + u) / u) + (math.log(1.0 + v) / v))
            )

    @classmethod
    def compute(
        cls,
        composition: Composition,
        secondary: XRayTransition,
        beam_energy: float,
        take_off_angle: float,
    ) -> float:
        """
        Computes the total fluorescence enhancement for a given secondary
        X-ray transition across all elements in the target material.

        The method sums over all primary transitions in the sample that can excite the
        given secondary line, applying weighting based on family and energy filtering
        as per Reed (1993).

        Args:
            composition (Composition): The sample's elemental composition.
            secondary (XRayTransition): The X-ray line for which enhancement is
                calculated.
            beam_energy (float): The electron beam energy (J).
            take_off_angle (float): The detector take-off angle (rad).

        Returns:
            float: The total fluorescence enhancement factor (dimensionless). A return
                value of 1.0 indicates no fluorescence enhancement.
        """
        total = 0.0
        for element in composition.elements:
            primary = cls.primary_exciting_line(element, secondary.destination)
            if primary is None or primary.edge_energy >= beam_energy:
                continue
            primary_ee = primary.edge_energy
            secondary_ee = secondary.edge_energy
            delta = 5.0 if secondary.family == 0 else 3.5
            if primary_ee >= (secondary_ee + delta):
                continue
            primary_family = primary.family
            weight = 0.0
            for transition in range(len(NAME)):
                xrt = XRayTransition(element, transition)
                if (
                    xrt.exists
                    and xrt.family == primary_family
                    and xrt.energy >= secondary_ee
                    and xrt.edge_energy < beam_energy
                ):
                    weight += xrt.weight("family")
            if weight > 0.0:
                total += (
                    cls.Reed1993.compute(
                        composition, primary, secondary, beam_energy, take_off_angle
                    )
                    * weight
                )
        return 1.0 + total
