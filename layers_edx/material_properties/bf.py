import math
from typing import Protocol
from layers_edx.material_properties.bc import BackscatterCoefficient
from layers_edx.atomic_shell import AtomicShell
from layers_edx.element import Composition


class BackscatterFactor:
    """
    Provides methods to compute the X-ray backscatter factor, which corrects for electron
    backscattering effects in quantitative X-ray microanalysis.

    The backscatter factor adjusts the detected X-ray intensity to account for the fact that
    some electrons are reflected back out of the material, reducing the effective ionization volume.
    """

    class Algorithm(Protocol):
        """
        Protocol defining the interface for backscatter factor computation algorithms.
        """

        bc = BackscatterCoefficient

        @classmethod
        def compute(cls, composition: Composition, shell: AtomicShell, energy: float) -> float:
            """
            Method for computing the electron backscatter factor.

            Args:
                composition (Composition): The elemental composition of the target material.
                shell (AtomicShell): The atomic shell for which the factor is calculated.
                energy (float): The incident electron energy (J).

            Returns:
                float: The backscatter coefficient (dimensionless).
            """
            ...

    class PouchouAndPichoir1991(Algorithm):

        @classmethod
        def compute(cls, composition: Composition, shell: AtomicShell, energy: float) -> float:
            eta = cls.bc.compute(composition, energy)
            w = 0.595 + (eta / 3.7) + math.pow(eta, 4.55)
            u0 = energy / shell.edge_energy
            ju = 1.0 + (u0 * (math.log(u0) - 1.0))
            q = ((2.0 * w) - 1.0) / (1.0 - w)
            gu = (u0 - 1.0 - ((1.0 - (1.0 / math.pow(u0, 1.0 + q))) / (1.0 + q))) / ((2.0 + q) * ju)
            return 1.0 - (eta * w * (1.0 - gu))

    @classmethod
    def compute(cls, composition: Composition, shell: AtomicShell, energy: float) -> float:
        """
        Computes the backscatter factor for the given composition, atomic shell and incident energy.

        Currently uses the Pouchou and Pichoir (1991) model.

        Args:
            composition (Composition): The elemental composition of the target material.
            shell (AtomicShell): The atomic shell for which the factor is calculated.
            energy (float): The incident electron energy (J).

        Returns:
            float: The computed backscatter factor (dimensionless).
        """
        return cls.PouchouAndPichoir1991.compute(composition, shell, energy)
