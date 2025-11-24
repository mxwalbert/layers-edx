from typing import Protocol
from layers_edx import read_csv
from layers_edx.atomic_shell import AtomicShell
from layers_edx.element import Element
from layers_edx.xrt import XRayTransition


class TransitionProbabilities:
    """
    Provides calculation of x-ray transition probabilities resulting from inner-shell ionization.

    The transition probabilities describe the likelihood of various radiative (and possibly
    non-radiative) de-excitation pathways following ionization of a specific atomic shell.
    """

    class Algorithm(Protocol):
        """
        Protocol for different algorithms that compute transition probabilities.
        """

        @classmethod
        def transitions(cls, ionized: AtomicShell, min_weight: float) -> dict[XRayTransition, float]:
            """
            Method for computing a dictionary of X-ray transitions and their corresponding probabilities
            for a given ionized shell.

            Args:
                ionized (AtomicShell): The shell that was ionized.
                min_weight (float): Minimum relative threshold for filtering transition probabilities.

            Returns:
                dict[XRayTransition, float]: A dictionary mapping each transition to its probability.
            """
            ...

    class Endlib1997(Algorithm):

        COSTER_KRONIG: dict[Element, list[tuple[XRayTransition, int, float]]] = {}
        RADIATIVE: dict[Element, list[tuple[XRayTransition, int, float]]] = {}
        for line in read_csv('relax', row_offset=3):
            element = Element(int(round(line[0])))
            xrt = XRayTransition(
                element=element,
                source=int(round(line[3])),
                destination=int(round(line[2])))
            result_dict = COSTER_KRONIG if xrt.destination.family == xrt.source.family else RADIATIVE
            if element not in result_dict:
                result_dict[element] = []
            result_dict[element].append((xrt, int(round(line[1])), line[4]))

        @classmethod
        def transitions(cls, ionized: AtomicShell, min_weight: float) -> dict[XRayTransition, float]:
            min_weight = 1e-10 if min_weight < 1e-10 else min_weight
            all_xrt: dict[XRayTransition, float] = {data[0]: data[2] for data in cls.RADIATIVE[ionized.element] if data[1] == ionized.shell}
            if not all_xrt:
                return {}
            max_probability = max(all_xrt.values())
            return {xrt: probability for xrt, probability in all_xrt.items() if probability >= (min_weight * max_probability)}

    class Endlib1997Tweaked(Endlib1997):

        TWEAKED = False

        @classmethod
        def tweak(cls):
            if cls.TWEAKED:
                return
            cls.TWEAKED = True
            for element, data in cls.RADIATIVE.items():
                for i, (xrt, ionized, probability) in enumerate(data):
                    if xrt.source.shell == AtomicShell.from_name('MI') and xrt.destination.shell in [AtomicShell.from_name('LIII'), AtomicShell.from_name('LII')]:
                        z = xrt.element.atomic_number
                        z_cu = Element.from_name('Cu')
                        z_au = Element.from_name('Au')
                        z_ti = Element.from_name('Ti')
                        if z > z_cu:
                            probability *= max(0.1, 0.1 + ((0.9 * (z - z_cu)) / (z_au - z_cu)))
                        else:
                            probability *= max(0.1, 0.2 - ((0.1 * (z - z_ti)) / (z_cu - z_ti)))
                        cls.RADIATIVE[element][i] = (xrt, ionized, probability)

        @classmethod
        def transitions(cls, ionized: AtomicShell, min_weight: float) -> dict[XRayTransition, float]:
            cls.tweak()
            return super().transitions(ionized, min_weight)

    @classmethod
    def transitions(cls, ionized: AtomicShell, min_weight: float) -> dict[XRayTransition, float]:
        """
        Computes transition probabilities using the tweaked ENDLIB 1997 data.

        Args:
            ionized (AtomicShell): The shell that was ionized.
            min_weight (float): Minimum relative threshold for filtering transition probabilities.

        Returns:
            dict[XRayTransition, float]:  A dictionary mapping each transition to its probability.
        """
        return cls.Endlib1997Tweaked.transitions(ionized, min_weight)
