import math
from typing import Protocol
from layers_edx.units import FromSI
from layers_edx.xrt import XRayTransition


class LeonardCoefficient:
    """
    The Leonard coefficient describes the relative generation of secondary X-rays
    due to primary beam excitation.

    The coefficient depends on the primary electron beam energy and the absorption edge
    energy of the characteristic X-ray transition of interest.
    """

    class Algorithm(Protocol):
        """
        Protocol defining the interface for Leonard coefficient computation algorithms.
        """

        @classmethod
        def compute(cls, beam_energy: float, xrt: XRayTransition) -> float:
            """
            Method for computing the Leonard coefficient for a given beam energy and
            X-ray transition.

            Args:
                beam_energy (float): The energy of the primary electron beam (J).
                xrt (XRayTransition): The X-ray transition for which the coefficient is
                    calculated.

            Returns:
                float: The Leonard coefficient (dimensionless).
            """
            ...

    class Heinrich1967(Algorithm):
        @classmethod
        def compute(cls, beam_energy: float, xrt: XRayTransition) -> float:
            return 4.5e5 / (
                math.pow(FromSI.kev(beam_energy), 1.65)
                - math.pow(FromSI.kev(xrt.edge_energy), 1.65)
            )

    @classmethod
    def compute(cls, beam_energy: float, xrt: XRayTransition) -> float:
        """
        Computes the Leonard coefficient using the default algorithm (Heinrich 1967).

        Args:
            beam_energy (float): The primary beam energy (J).
            xrt (XRayTransition): The X-ray transition for which the coefficient is
                calculated.

        Returns:
            float: The Leonard coefficient (dimensionless).
        """
        return cls.Heinrich1967.compute(beam_energy, xrt)
