import math
from abc import ABC, abstractmethod
from layers_edx import read_csv
from layers_edx.atomic_shell import AtomicShell
from layers_edx.units import FromSI, PhysicalConstants, ToSI


class IonizationCrossSection(ABC):
    """
    Abstract base class for computing the ionization cross-section of an atomic shell
    by an incident electron beam.

    The ionization cross-section (m^2) quantifies the probability of ionizing a specific
    electron shell in an atom as a function of the beam energy.
    """

    @staticmethod
    def shell_dependence(shell: AtomicShell) -> float:
        """
        Computes a shell-dependent weighting factor used in proportional models.

        Args:
            shell (AtomicShell): The atomic shell of interest.

        Returns:
            float: Dimensionless weighting factor.
        """
        n = shell.family - shell.family_from_name("K") + 1
        return shell.capacity / (2.0 * n * n)

    @classmethod
    @abstractmethod
    def compute_shell(cls, shell: AtomicShell, beam_energy: float) -> float:
        """
        Computes the ionization cross-section for a specific shell and beam energy.

        Args:
            shell (AtomicShell): The atomic shell to ionize.
            beam_energy (float): The energy of the electron beam (J).

        Returns:
            float: Ionization cross-section (m^2).
        """
        pass


class ProportionalIonizationCrossSection(IonizationCrossSection):
    """
    Computes ionization cross-sections using a proportional model.

    This model scales the shell-dependent factor with a functional form depending
    on beam energy, following the semi-empirical approach of Pouchou & Pichoir (1986).
    """

    class Algorithm(ABC):
        """
        Abstract base class for algorithms defining the beam-energy dependence
        in proportional cross-section models.
        """

        @classmethod
        def compute_family(cls, shell: AtomicShell, beam_energy: float) -> float:
            """
            Computes the family-wise ionization cross-section, excluding shell
            dependence.

            Args:
                shell (AtomicShell): The atomic shell of interest.
                beam_energy (float): The energy of the incident beam (J).

            Returns:
                float: Unscaled cross-section (m^2).
            """
            e_crit = FromSI.kev(shell.edge_energy)
            u = FromSI.kev(beam_energy) / e_crit
            if u <= 1.0:
                return 0.0
            return math.log(u) / (
                (e_crit * e_crit) * math.pow(u, cls.compute_exponent(shell))
            )

        @classmethod
        @abstractmethod
        def compute_exponent(cls, shell: AtomicShell) -> float:
            """
            Returns the exponent used in the beam-energy dependence formula.

            Args:
                shell (AtomicShell): The atomic shell of interest.

            Returns:
                float: Dimensionless empirical exponent.
            """
            pass

    class Pouchou1986(Algorithm):
        @classmethod
        def compute_exponent(cls, shell: AtomicShell) -> float:
            za = shell.element.atomic_number
            if shell.family == shell.family_from_name("K"):
                return 0.86 + (0.12 * math.exp((-za * za) / 25.0))
            elif shell.family == shell.family_from_name("L"):
                return 0.82
            elif shell.family == shell.family_from_name("M"):
                return 0.78
            else:
                return float("nan")

    @classmethod
    def compute_shell(cls, shell: AtomicShell, beam_energy: float) -> float:
        return cls.shell_dependence(shell) * cls.compute_family(shell, beam_energy)

    @classmethod
    def compute_family(cls, shell: AtomicShell, beam_energy: float) -> float:
        """
        Computes the unscaled ionization cross-section for the shell family.

        Args:
            shell (AtomicShell): The atomic shell to ionize.
            beam_energy (float): Beam energy (J).

        Returns:
            float: Scaled cross-section (m^2).
        """
        return cls.Pouchou1986.compute_family(shell, beam_energy)

    @classmethod
    def compute_exponent(cls, shell: AtomicShell) -> float:
        """
        Returns the exponent used in the proportional model.

        Args:
            shell (AtomicShell): The atomic shell of interest.

        Returns:
            float: Dimensionless empirical exponent.
        """
        return cls.Pouchou1986.compute_exponent(shell)


class AbsoluteIonizationCrossSection(IonizationCrossSection):
    """
    Computes absolute ionization cross-sections based on physical models and tabulated
    fits.

    This implementation uses the model of Bote & Salvat (2008) which includes detailed
    parameterizations for both low- and high-energy regimes and atomic shells.
    """

    class Algorithm(ABC):
        """
        Abstract base class for algorithms computing absolute ionization cross-sections.
        """

        @classmethod
        @abstractmethod
        def compute_shell(cls, shell: AtomicShell, beam_energy: float) -> float:
            """
            Computes the shell-specific ionization cross-section.

            Args:
                shell (AtomicShell): The atomic shell to ionize.
                beam_energy (float): Beam energy (J).

            Returns:
                float: Ionization cross-section (m^2).
            """
            pass

    class BoteSalvat2008(Algorithm):
        FPIAB2 = 4.0 * math.pi * FromSI.cm(PhysicalConstants.BohrRadius) ** 2
        REV = FromSI.ev(PhysicalConstants.ElectronRestMass)

        A = [
            [line[i : i + 5] for i in range(0, len(line), 5)]
            for line in read_csv("SalvatXionA", value_offset=1, column_offset=1)
        ]

        BE = []
        ANLJ = []
        G = []
        for data in [
            [line[i : i + 6] for i in range(0, len(line), 6)]
            for line in read_csv("SalvatXionB", value_offset=1, column_offset=1)
        ]:
            be = [block[0] for block in data]
            anlj = [block[1] for block in data]
            g = [block[2:] for block in data]
            BE.append(be)
            ANLJ.append(anlj)
            G.append(g)

        @classmethod
        def compute_shell(cls, shell: AtomicShell, beam_energy: float) -> float:
            eev = FromSI.ev(beam_energy)
            uev = FromSI.ev(shell.edge_energy)
            if 1e-35 > uev > eev:
                return 0.0
            over_v = eev / uev
            iz = shell.element.atomic_number
            ish = shell.shell
            if over_v <= 16.0:
                if ish >= len(cls.A[iz]):
                    return 0.0
                a = cls.A[iz][ish]
                opu = 1.0 / (1.0 + over_v)
                opu2 = opu**2
                ffitlo = (
                    a[0] + a[1] * over_v + opu * (a[2] + opu2 * (a[3] + opu2 * a[4]))
                )
                xione = (over_v - 1.0) * math.pow(ffitlo / over_v, 2.0)
            else:
                if ish >= len(cls.BE[iz]):
                    return 0.0
                beta2 = (eev * (eev + (2.0 * cls.REV))) / (
                    (eev + cls.REV) * (eev + cls.REV)
                )
                x = math.sqrt(eev * (eev + (2.0 * cls.REV))) / cls.REV
                g = cls.G[iz][ish]
                ffitup = (
                    (((2.0 * math.log(x)) - beta2) * (1.0 + (g[0] / x)))
                    + g[1]
                    + (
                        g[2]
                        * math.pow(
                            (cls.REV * cls.REV) / ((eev + cls.REV) * (eev + cls.REV)),
                            0.25,
                        )
                    )
                    + (g[3] / x)
                )
                factor = cls.ANLJ[iz][ish] / beta2
                xione = ((factor * over_v) / (over_v + cls.BE[iz][ish])) * ffitup
            return ToSI.cm(1) ** 2 * cls.FPIAB2 * xione

    @classmethod
    def compute_shell(cls, shell: AtomicShell, beam_energy: float) -> float:
        return cls.BoteSalvat2008.compute_shell(shell, beam_energy)

    @classmethod
    def compute_family(cls, shell: AtomicShell, beam_energy: float) -> float:
        """
        Computes a family-averaged ionization cross-section based on shell-level data.

        Args:
            shell (AtomicShell): The atomic shell of interest.
            beam_energy (float): Beam energy (J)

        Returns:
            float: Family-averaged ionization cross-section (m^2).
        """
        return cls.compute_shell(shell, beam_energy) / cls.shell_dependence(shell)
