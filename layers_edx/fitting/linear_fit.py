from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TypeVar, Any
import numpy as np
import numpy.typing as npt
from layers_edx.fitting.culling import TCullingStrategy
from layers_edx.element import Element
from layers_edx.fitting.parameter import TParameter
from layers_edx.quantification.reference_material import TReferenceMaterial
from layers_edx.roi import RegionOfInterest
from layers_edx.kratio import KRatioSet
from layers_edx.xrt import XRayTransition


class LinearFit(ABC):
    def __init__(
        self,
        references: dict[RegionOfInterest, TReferenceMaterial],
        culling_strategy: TCullingStrategy = None,
    ):
        self._references = references
        self._culling_strategy = culling_strategy
        self._assign_parameters()

    @abstractmethod
    def _assign_parameters(self):
        self._parameters = []

    @property
    def references(self) -> dict[RegionOfInterest, TReferenceMaterial]:
        return self._references

    @property
    def culling_strategy(self) -> TCullingStrategy:
        """
        The implemented strategy based on which elements are removed from the fitting.
        """
        return self._culling_strategy

    @property
    def parameters(self) -> list[TParameter]:
        return self._parameters

    @property
    def elements(self) -> set[Element]:
        """The set of elements which are present in the parameters."""
        return set([p.element for p in self.parameters])

    @property
    def num_fit_params(self) -> int:
        """
        The number of fitting parameters which corresponds to the number of references.
        """
        return len(self.parameters)

    @abstractmethod
    def features_and_targets(
        self, unknown: Any, selected: list[TParameter]
    ) -> tuple[npt.NDArray[np.floating], npt.NDArray[np.floating]]:
        """Returns a tuple of features and targets to be used fpr the fitting."""

    def get_k_ratios(self, unknown: dict[XRayTransition, float]) -> KRatioSet:
        """Computes the k-ratios between the references and the provided data."""
        zero_fit_params = np.zeros(self.num_fit_params, dtype=bool)
        remove, removed = set(), set()
        for p in self.parameters:
            p.kratio = 0.0
        repeat = True
        while repeat:
            repeat = False
            selected = []
            removed.update(remove)
            remove.clear()
            for i, p in enumerate(self.parameters):
                if p.element in removed:
                    zero_fit_params[i] = True
                if not zero_fit_params[i]:
                    selected.append(p)
            features, targets = self.features_and_targets(unknown, selected)
            fit = np.linalg.lstsq(features, targets, rcond=1.0e-12)
            fit_params = np.zeros(self.num_fit_params)
            fit_params[~zero_fit_params] = fit[0].flatten()
            for i, p in enumerate(self.parameters):
                if not zero_fit_params[i]:
                    p.kratio = fit_params[i]
                    if p.kratio < 0.0:
                        p.kratio = 0.0
                        zero_fit_params[i] = True
                        repeat = True
            if self.culling_strategy is not None:
                cull_these = self.culling_strategy.compute(self.parameters, fit_params)
                remove.update(cull_these)
            for p in self.parameters:
                if p.element in remove | removed:
                    p.kratio = 0.0
            repeat = repeat or len(remove - removed) > 0
        result = KRatioSet()
        for p in self.parameters:
            result.add(p.xrt_set, p.kratio)
        return result


TLinearFit = TypeVar("TLinearFit", bound=LinearFit)
