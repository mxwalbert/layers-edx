import math
from typing import Protocol
from layers_edx.xrt import XRayTransition


class IonizationDepthRatio:
    """
    Computes the ionization depth ratio between two X-ray transitions for a given beam energy.

    This ratio describes the relative depth from which characteristic X-rays of two transitions
    are excited.
    """

    class Algorithm(Protocol):
        """
        Protocol for algorithms that compute the ionization depth ratio.
        """

        @classmethod
        def compute(cls, primary: XRayTransition, secondary: XRayTransition, beam_energy: float) -> float:
            """
            Method for computing the ionization depth ratio between two transitions.

            Args:
                primary (XRayTransition): The primary X-ray transition.
                secondary (XRayTransition): The secondary X-ray transition.
                beam_energy (float): The incident electron beam energy (J).

            Returns:
                float: Ionization depth ratio (dimensionless).
            """
            ...

    class Reed1990(Algorithm):

        @classmethod
        def compute(cls, primary: XRayTransition, secondary: XRayTransition, beam_energy: float) -> float:
            return math.pow((beam_energy / primary.edge_energy - 1.0) / (beam_energy / secondary.edge_energy - 1.0), 1.67)

    @classmethod
    def compute(cls, primary: XRayTransition, secondary: XRayTransition, beam_energy: float) -> float:
        """
        Computes the ionization depth ratio using the default algorithm (Reed1990).

        Args:
            primary (XRayTransition): The primary X-ray transition.
            secondary (XRayTransition): The secondary X-ray transition.
            beam_energy (float): The incident electron beam energy (J).

        Returns:
            float: Ionization depth ratio (dimensionless).
        """
        return cls.Reed1990.compute(primary, secondary, beam_energy)
