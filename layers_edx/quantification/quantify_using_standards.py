from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Type
from layers_edx.fitting.culling import TCullingStrategy, CullByVariance
from layers_edx.fitting.linear_fit import TLinearFit
from layers_edx.quantification.reference_material import TReferenceMaterial
from layers_edx.quantification.standard_material import TStandardMaterial
from layers_edx.element import Element
from layers_edx.kratio import KRatioSet
from layers_edx.roi import RegionOfInterest


class QuantifyUsingStandards(ABC):

    def __init__(self,
                 beam_energy: float,
                 standards: dict[Element, TStandardMaterial],
                 user_references: dict[RegionOfInterest, TReferenceMaterial] = None,
                 culling_strategy: TCullingStrategy = None):
        self._beam_energy = beam_energy
        self._standards = standards
        self._measured_elements = set(standards.keys())
        self._stripped_elements = set.union(*[standard.stripped_elements for standard in standards.values()])
        self._user_references = {} if user_references is None else user_references
        self._culling_strategy = CullByVariance(0.0) if culling_strategy is None else culling_strategy
        self._assign_references()
        self._compute_reference_scales()

    def _assign_references(self) -> None:
        self._references = {}
        for standard in self.standards.values():
            for roi in standard.roi_set.rois:
                rm = self.assign_reference(roi)
                if rm is not None:
                    self._references[roi] = rm

    def assign_reference(self, roi: RegionOfInterest) -> TReferenceMaterial:
        if roi in self.user_references:
            return self.user_references[roi]
        element = roi.first_element
        if element in self.standards and self.standards[element].is_suitable_as_reference(roi):
            return self.create_reference(self.standards[element])
        rm = None
        best_sn = 0.0
        for standard in self.standards.values():
            if element in standard.composition.elements and standard.is_suitable_as_reference(roi):
                sn = standard.nominal_signal_to_noise(roi)
                if sn > best_sn:
                    rm = self.create_reference(standard)
                    best_sn = sn
        return rm

    @staticmethod
    @abstractmethod
    def create_reference(standard: TStandardMaterial) -> TReferenceMaterial:
        pass

    def _compute_reference_scales(self) -> None:
        self._reference_scales = {}
        for roi in self.references:
            self._reference_scales[roi] = self.compute_reference_scale(roi)

    def compute_reference_scale(self, roi: RegionOfInterest) -> float:
        """Computes the scaling factor between the reference and the standard associated with this roi."""
        element = roi.first_element
        reference = self.references[roi]
        standard = self.standards[element]
        reference_requirements = standard.required_references[roi] if roi in standard.required_references else set()
        if reference.model != standard.model:
            reference_requirements.add(reference)
        if len(reference_requirements) == 0:
            return 1.0
        model_fit = self.fitting_class(reference_requirements)
        kratio_set = model_fit.get_k_ratios(standard.model)
        return kratio_set.kratio_from_xrt_set(roi.xrt_set(element))

    @property
    def beam_energy(self) -> float:
        return self._beam_energy

    @property
    def standards(self) -> dict[Element, TStandardMaterial]:
        return self._standards

    @property
    def user_references(self) -> dict[RegionOfInterest, TReferenceMaterial]:
        return self._user_references

    @property
    def culling_strategy(self) -> TCullingStrategy:
        """A mechanism for removing elements with zero or near zero presence."""
        return self._culling_strategy

    @property
    def measured_elements(self) -> set[Element]:
        return self._measured_elements

    @property
    def stripped_elements(self) -> set[Element]:
        return self._stripped_elements

    @property
    def references(self) -> dict[RegionOfInterest, TReferenceMaterial]:
        """Returns a map of ROI to the ReferenceMaterial which is available to act as a reference for this ROI. Does
        not return ROIs for which a ReferenceMaterial has not been defined. If there is a user specified reference,
        then this will be used. If a standard can act as a reference then this standard is suggested so long as the
        estimated signal-to-noise is adequate."""
        return self._references

    @property
    def reference_scales(self) -> dict[RegionOfInterest, float]:
        """Returns the scale of the reference relative to the standard by fitting the standard with the appropriate
        reference (and any other required references) to extract the k-ratio of references relative to the standard."""
        return self._reference_scales

    @property
    @abstractmethod
    def fitting_class(self) -> Type[TLinearFit]:
        """Returns the fitting class which is used in this quantification."""

    @property
    @abstractmethod
    def linear_fit(self) -> TLinearFit:
        """Returns the linear fit instance which is used by this quantification."""

    @abstractmethod
    def compute(self, unknown: Any) -> KRatioSet:
        krs_against_refs = self.linear_fit.get_k_ratios(unknown)
        full_krs = KRatioSet()
        for element in self.measured_elements:
            for roi in self.standards[element].roi_set.rois:
                if roi in self.references:
                    sc = self.reference_scales[roi]
                    if sc is not None and sc > 0.0:
                        xrt_set = roi.xrt_set(element)
                        kr = krs_against_refs.kratio_from_xrt_set_raw(xrt_set)
                        k_std = kr / sc
                        full_krs.add(xrt_set, k_std)
        with_stripped = KRatioSet()
        for xrt_set in krs_against_refs.xrt_sets:
            if full_krs.find(xrt_set) is not None:
                with_stripped.add(xrt_set, full_krs.kratio_from_xrt_set(xrt_set))
            else:
                with_stripped.add(xrt_set, krs_against_refs.kratio_from_xrt_set(xrt_set))
        return with_stripped
