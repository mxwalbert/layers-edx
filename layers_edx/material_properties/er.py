import numpy as np
from typing import Protocol
from layers_edx.material_properties.mip import MeanIonizationPotential
from layers_edx.atomic_shell import AtomicShell
from layers_edx.element import Composition
from layers_edx.units import FromSI, ToSI


class ElectronRange:
    """
    Provides methods to compute the range of electrons in a material, based on its
    composition and the incident electron energy.

    The electron range is used for estimating the depth of interaction and X-ray
    generation, and its unit is length * density (m * kg/m^3).
    """

    class Algorithm(Protocol):
        """
        Protocol defining the interface for electron range computation algorithms.
        """

        mip = MeanIonizationPotential

        @classmethod
        def compute(cls, composition: Composition, energy: float) -> float:
            """
            Method for computing the effective electron range.

            Args:
                composition (Composition): The elemental composition of the target
                    material.
                shell (AtomicShell): The atomic shell for which the electron range is
                    calculated.
                energy (float): The incident electron energy (J).

            Returns:
                float: The electron range, representing the penetration depth of
                    electrons (m * kg/m^3).
            """
            ...

    class PouchouAndPichoir1991(Algorithm):
        @classmethod
        def compute(cls, composition: Composition, energy: float) -> float:
            big_m = sum(
                [
                    f * e.atomic_number / e.atomic_weight
                    for e, f in composition.weight_fractions.items()
                ]
            )
            j = FromSI.kev(cls.mip.compute_composition(composition))
            d = np.array([6.6e-6, 1.12e-5 * (1.35 - (0.45 * j * j)), 2.2e-6 / j])
            p = np.array([0.78, 0.1, -(0.5 - 0.25 * j)])
            tmp = (
                np.power(j, 1.0 - p)
                * d
                * np.power(FromSI.kev(energy), 1.0 + p)
                / (1.0 + p)
            )
            return ToSI.gpcm2(tmp.sum() / big_m)

    @classmethod
    def compute(
        cls, composition: Composition, shell: AtomicShell, energy: float
    ) -> float:
        """
        Computes the effective electron range between the incident energy and the
        ionization energy of a given atomic shell.

        Currently uses the Pouchou and Pichoir (1991) model.

        Args:
            composition (Composition): The elemental composition of the target material.
            shell (AtomicShell): The atomic shell for which the electron range is
                calculated.
            energy (float): The incident electron energy (J).

        Returns:
            float: The difference in electron range between the two
                energies (m * kg/m^3).
        """
        algorithm = cls.PouchouAndPichoir1991
        return algorithm.compute(composition, energy) - algorithm.compute(
            composition, shell.edge_energy
        )
