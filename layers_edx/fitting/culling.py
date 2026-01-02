from abc import ABC, abstractmethod
from typing import TypeVar
import numpy as np
import numpy.typing as npt
from layers_edx.element import Element
from layers_edx.fitting.parameter import TParameter


class CullingStrategy(ABC):
    """
    A mechanism to determine which elements should be removed from the fit based on
    insufficient evidence.
    """

    @abstractmethod
    def compute(
        self, parameters: list[TParameter], fit_result: npt.NDArray[np.floating]
    ) -> set[Element]:
        """
        Takes the calculated fitting parameters and determines based on these whether
        an element is present. If the element is not likely to be present it is added to
        the returned set.
        """


TCullingStrategy = TypeVar("TCullingStrategy", bound=CullingStrategy)


class CullByVariance(CullingStrategy):
    """
    Considers all the evidence (k-ratios) associated with an element and keeps only
    those that exceed a user-specified level of statistical significance.
    """

    def __init__(self, significance: float):
        self._significance = significance

    @property
    def significance(self) -> float:
        """Elements with k-ratios below this value are removed."""
        return self._significance

    def compute(
        self, parameters: list[TParameter], fit_result: npt.NDArray[np.floating]
    ) -> set[Element]:
        remove = set()
        for element in set([p.element for p in parameters]):
            kratios = []
            for i, p in enumerate(parameters):
                if p.element == element:
                    kratios.append(fit_result[i])
            kratio_mean = np.mean(kratios)
            if not np.isnan(kratio_mean) and kratio_mean < self.significance * np.var(
                kratio_mean
            ):
                remove.add(element)
        return remove
