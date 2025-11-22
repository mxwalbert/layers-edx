import math
from typing import Protocol
from layers_edx.element import Composition


class BackscatterCoefficient:
    """
    Provides methods to compute the electron backscatter coefficient for a given material composition
    and incident electron energy using empirical or theoretical algorithms.

    The backscatter coefficient quantifies the fraction of incident electrons that are elastically
    scattered back out of the material.
    """

    class Algorithm(Protocol):
        """
        Protocol that defines the interface for backscatter coefficient algorithms.
        """

        @classmethod
        def compute(cls, composition: Composition, energy: float) -> float:
            """
            Method for computing the electron backscatter coefficient.

            Args:
                composition (Composition): The elemental composition of the target material.
                energy (float): The incident electron energy (J).

            Returns:
                float: The backscatter coefficient (dimensionless).
            """
            ...

    class PouchouAndPichoir1991(Algorithm):

        @classmethod
        def compute(cls, composition: Composition, energy: float) -> float:
            total = composition.sum_weight_fractions if composition.sum_weight_fractions < 1.1 else 1.1
            zb = sum([f / total * math.sqrt(e.atomic_number) for e, f in composition.raw_weight_fractions.items()])
            zb *= zb
            return (1.75e-3 * zb) + (0.37 * (1.0 - math.exp(-0.015 * math.pow(zb, 1.3))))

    @classmethod
    def compute(cls, composition: Composition, energy: float) -> float:
        """
        Computes the backscatter coefficient for the given composition and incident energy.

        Currently uses the Pouchou and Pichoir (1991) model.

        Args:
            composition (Composition): The elemental composition of the target material.
            energy (float): The incident electron energy (J).

        Returns:
            float: The computed backscatter coefficient (dimensionless).
        """
        return cls.PouchouAndPichoir1991.compute(composition, energy)
