import math
from typing import Protocol
from layers_edx.material_properties.bc import BackscatterCoefficient
from layers_edx.atomic_shell import AtomicShell
from layers_edx.element import Composition


class SurfaceIonization:
    """
    Computes the surface ionization correction factor for x-ray generation in
    electron-excited materials.

    The surface ionization factor accounts for the enhancement of x-ray emission due to
    backscattered electrons near the sample surface.
    """

    class Algorithm(Protocol):
        """
        Protocol interface for surface ionization algorithms.
        """

        bc = BackscatterCoefficient

        @classmethod
        def compute(
            cls, composition: Composition, shell: AtomicShell, energy: float
        ) -> float:
            """
            Method for computing the surface ionization correction factor.

            Args:
                composition (Composition): The sample composition.
                shell (AtomicShell): The atomic shell of interest.
                energy (float): The excitation energy (J).

            Returns:
                float: The surface ionization factor (dimensionless).
            """
            ...

    class Pouchou1991(Algorithm):
        @classmethod
        def compute(
            cls, composition: Composition, shell: AtomicShell, energy: float
        ) -> float:
            u0 = energy / shell.edge_energy
            eta = cls.bc.compute(composition, energy)
            r = 2.0 - (2.3 * eta)
            return 1.0 + (3.3 * (1.0 - (1.0 / math.pow(u0, r))) * math.pow(eta, 1.2))

    @classmethod
    def compute(
        cls, composition: Composition, shell: AtomicShell, energy: float
    ) -> float:
        """
        Computes the surface ionization correction factor using the default algorithm
        (Pouchou1991).

        Args:
            composition (Composition): The sample composition.
            shell (AtomicShell): The atomic shell of interest.
            energy (float): The excitation energy (J).

        Returns:
            float: The surface ionization factor (dimensionless).
        """
        return cls.Pouchou1991.compute(composition, shell, energy)
