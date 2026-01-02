from typing import Protocol
from layers_edx.material_properties.mac import MassAbsorptionCoefficient
from layers_edx.atomic_shell import AtomicShell
from layers_edx.units import ToSI


class JumpRatio:
    """
    Provides algorithms to compute the jump ratio of a given atomic shell,
    which quantifies the discontinuity in the mass absorption coefficient at the shell's
    ionization energy.
    """

    class Algorithm(Protocol):
        """
        Protocol defining the interface for jump ratio computation algorithms.
        """

        @classmethod
        def compute(cls, shell: AtomicShell) -> float:
            """
            Method for computing the jump ratio for a given atomic shell.

            Args:
                shell (AtomicShell): The atomic shell of interest.

            Returns:
                float: The jump ratio at the shell's edge energy.
            """
            ...

    class Heinrich1986(Algorithm):
        mac = MassAbsorptionCoefficient
        DELTA = ToSI.ev(0.001)

        @classmethod
        def compute(cls, shell: AtomicShell) -> float:
            edge_energy = shell.edge_energy
            return cls.mac.compute(
                shell.element, edge_energy + cls.DELTA
            ) / cls.mac.compute(shell.element, edge_energy - cls.DELTA)

    @classmethod
    def compute(cls, shell: AtomicShell) -> float:
        """
        Computes the jump ratio for a given atomic shell using the default algorithm
        (Heinrich 1986).

        Args:
            shell (AtomicShell): The atomic shell of interest.

        Returns:
            float: The computed jump ratio (dimensionless).
        """
        return cls.Heinrich1986.compute(shell)

    @classmethod
    def ionization_fraction(cls, shell: AtomicShell) -> float:
        """
        Computes the fraction of ionizations occurring in a specific shell
        based on the jump ratio.

        Args:
            shell (AtomicShell): The atomic shell of interest.

        Returns:
            float: The dimensionless ionization fraction, defined as (r - 1) / r
                for r ≥ 1, otherwise 0.
        """
        r = cls.compute(shell)
        return (r - 1.0) / r if r >= 1.0 else 0.0
