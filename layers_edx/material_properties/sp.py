import numpy as np
from typing import Protocol
from layers_edx.material_properties.mip import MeanIonizationPotential
from layers_edx.material_properties.ics import ProportionalIonizationCrossSection
from layers_edx.atomic_shell import AtomicShell
from layers_edx.element import Composition
from layers_edx.units import FromSI, ToSI


class StoppingPower:
    """
    Computes the electronic stopping power of electrons in matter, based on material composition,
    atomic shell, and beam energy. The stopping power is a measure of energy loss per unit path length.
    """

    class Algorithm(Protocol):
        """
        Protocol interface for stopping power algorithms.
        """

        mip = MeanIonizationPotential
        pics = ProportionalIonizationCrossSection

        @classmethod
        def compute_inv(cls, composition: Composition, shell: AtomicShell, energy: float) -> float:
            """
            Method for computing the inverse stopping power for a given composition, atomic shell, and beam energy.

            Args:
                composition (Composition): Material composition.
                shell (AtomicShell): The atomic shell under consideration.
                energy (float): Beam energy (J).

            Returns:
                float: Inverse stopping power (kg/(m^3*J)).
            """
            ...

    class PouchouAndPichoir1991(Algorithm):

        @classmethod
        def compute_inv(cls, composition: Composition, shell: AtomicShell, energy: float) -> float:
            big_m = sum([f * e.atomic_number / e.atomic_weight for e, f in composition.weight_fractions.items()])
            j = FromSI.kev(cls.mip.compute_composition(composition))
            v0 = FromSI.kev(energy) / j
            d = np.array([6.6e-6, 1.12e-5 * (1.35 - (0.45 * j * j)), 2.2e-6 / j])
            p = np.array([0.78, 0.1, 0.25 * (j - 2.0)])
            m = cls.pics.compute_exponent(shell)
            u0 = energy / shell.edge_energy
            t = 1.0 + p - m
            tmp = (d * np.power(v0 / u0, p) * (((t * np.power(u0, t) * np.log(u0)) - np.power(u0, t)) + 1)) / (t * t)
            return ToSI.gpcm2kev((u0 / (v0 * big_m)) * tmp.sum())

    @classmethod
    def compute_inv(cls, composition: Composition, shell: AtomicShell, energy: float) -> float:
        """
        Calculates the inverse stopping power using the selected algorithm.

        Currently uses the Pouchou and Pichoir (1991) model.

        Args:
            composition (Composition): Material composition.
            shell (AtomicShell): The atomic shell under consideration.
            energy (float): Beam energy (J).

        Returns:
            float: Inverse stopping power (kg/(m^3*J)).
        """
        return cls.PouchouAndPichoir1991.compute_inv(composition, shell, energy)

    @classmethod
    def compute(cls, composition: Composition, shell: AtomicShell, energy: float) -> float:
        """
        Calculates the stopping power as the reciprocal of the inverse stopping power.

        Args:
            composition (Composition): Material composition.
            shell (AtomicShell): Atomic shell.
            energy (float): Beam energy (J).

        Returns:
            float: Stopping power (J*m^3/kg).
        """
        return 1 / cls.compute_inv(composition, shell, energy)
