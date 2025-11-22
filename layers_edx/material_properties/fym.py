from typing import Protocol
from layers_edx import read_csv, llf
from layers_edx.atomic_shell import AtomicShell
from layers_edx.element import Element


class FluorescenceYieldMean:
    """
    Provides methods to compute the mean fluorescence yield for a given atomic shell.

    The fluorescence yield represents the probability that an atom, upon ionization
    of a particular shell, will emit an X-ray photon rather than undergoing
    an Auger or Coster–Kronig transition.
    """

    class Algorithm(Protocol):
        """
        Protocol defining the interface for computing mean fluorescence yield.
        """

        @classmethod
        def compute(cls, shell: AtomicShell) -> float:
            """
            Method for computing the mean fluorescence yield for a given shell.

            Args:
                shell (AtomicShell): The atomic shell of interest.

            Returns:
                float: The mean fluorescence yield (dimensionless).
            """
            ...

    class Bambynek1972(Algorithm):

        DATA: llf = read_csv('FluorescenceYield', value_offset=1, row_offset=2)

        @classmethod
        def compute(cls, shell: AtomicShell) -> float:
            return cls.DATA[shell.element.atomic_number][shell.family] if shell.family <= 2 else 0.0

    class Oz1999(Algorithm):

        DATA: list[float] = [v[0] for v in read_csv('Oz1999', value_offset=Element.from_name('Cu'), row_offset=2, fill_value=0)]

        @classmethod
        def compute(cls, shell: AtomicShell) -> float:
            return cls.DATA[shell.element.atomic_number]

    @classmethod
    def compute(cls, shell: AtomicShell) -> float:
        """
        Computes the mean fluorescence yield for a given atomic shell.

        Currently, the method automatically selects the appropriate algorithm based on shell family:
        - Bambynek1972 for K and L shells (families 0–1),
        - Oz1999 for M shells (family 2).

        Args:
            shell (AtomicShell): The atomic shell of interest.

        Returns:
            float: The mean fluorescence yield (dimensionless).
        """
        algorithm = cls.Oz1999 if shell.family == 2 else cls.Bambynek1972
        return algorithm.compute(shell)
