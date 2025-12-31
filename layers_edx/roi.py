from __future__ import annotations
from layers_edx.xrt import transition_from_name, XRayTransition, XRayTransitionSet
from layers_edx.units import ToSI, FromSI
from layers_edx.detector.lineshape_model import LineshapeModel
from layers_edx.element import Element


class RegionOfInterest:
    def __init__(
        self,
        xrt: XRayTransition,
        model: LineshapeModel = None,
        min_intensity: float = 0.0,
        low_extra: float = 0.0,
        high_extra: float = 0.0,
    ):
        self._low_energy = float("inf")
        self._high_energy = -float("inf")
        self._xrts = set()
        self._model = model
        self._min_intensity = min_intensity
        self._low_extra = low_extra
        self._high_extra = high_extra
        self.add_xrt(xrt)

    def __lt__(self, other: RegionOfInterest) -> bool:
        return self.low_energy < other.low_energy

    def __eq__(self, other: RegionOfInterest) -> bool:
        return (
            self.low_energy == other.low_energy
            and self.high_energy == other.high_energy
            and self.xrts == other.xrts
        )

    def __hash__(self) -> int:
        return hash((self.low_energy, self.high_energy)) | hash(frozenset(self.xrts))

    def __str__(self) -> str:
        return f"[{self.low_energy}, {self.high_energy}]"

    @property
    def low_energy(self) -> float:
        """The low energy encompassed by this ``RegionOfInterest`` (J)."""
        return self._low_energy

    @property
    def high_energy(self) -> float:
        """The high energy encompassed by this ``RegionOfInterest`` (J)."""
        return self._high_energy

    @property
    def xrts(self) -> set[XRayTransition]:
        """
        Returns a set of the `XRayTransition` objects
        contained in this `RegionOfInterest`.
        """
        return self._xrts

    @property
    def model(self) -> LineshapeModel:
        """The detector ``LineShapeModel``."""
        return self._model

    @property
    def min_intensity(self) -> float:
        """The minimum weighted intensity for an X-ray transition to be considered."""
        return self._min_intensity

    @property
    def low_extra(self) -> float:
        """
        In increment subtracted from the low energy side of
        the `RegionOfInterest` (in J).
        """
        return self._low_extra

    @property
    def high_extra(self) -> float:
        """
        In increment added to the high energy side of the `RegionOfInterest` (in J).
        """
        return self._high_extra

    @property
    def elements(self) -> list[Element]:
        """
        Returns a sorted list of unique `Element` objects represented
        by this `RegionOfInterest`.
        """
        elements = set()
        for xrt in self.xrts:
            elements.add(xrt.element)
        return sorted(elements)

    @property
    def first_element(self) -> Element:
        """Returns the first entry in the set of the `elements`."""
        return self.elements[0]

    def xrt_set(self, element: Element) -> XRayTransitionSet:
        """
        Returns an `XRayTransitionSet` containing all `XRayTransition` objects
        from this `RegionOfInterest` which correspond to the specified `element`.
        """
        xrt_set = XRayTransitionSet(element, populate=False)
        for xrt in self.xrts:
            xrt_set.add(xrt)
        return xrt_set

    def add_xrt(self, xrt: XRayTransition):
        weight = xrt.weight(normalization="family")
        if weight <= self.min_intensity:
            return
        energy = xrt.energy
        low = energy
        high = energy
        if self.model is not None:
            energy_ev = FromSI.ev(xrt.energy)
            low -= (
                ToSI.ev(self.model.left_width(energy_ev, self.min_intensity / weight))
                + self.low_extra
            )
            high += (
                ToSI.ev(self.model.right_width(energy_ev, self.min_intensity / weight))
                + self.high_extra
            )
        if low < self.low_energy:
            self._low_energy = low
        if high > self.high_energy:
            self._high_energy = high
        self._xrts.add(xrt)

    def add_roi(self, roi: RegionOfInterest):
        self._low_energy = min(self.low_energy, roi.low_energy)
        self._high_energy = max(self.high_energy, roi.high_energy)
        self._xrts = self.xrts.union(roi.xrts)

    def contains(self, energy: float):
        return self.low_energy <= energy <= self.high_energy

    def intersects(self, roi: RegionOfInterest):
        return self.contains(roi.low_energy) or self.contains(roi.high_energy)

    def fully_contains(self, roi: RegionOfInterest):
        return self.contains(roi.low_energy) and self.contains(roi.high_energy)


class RegionOfInterestSet:
    def __init__(
        self,
        model: LineshapeModel = None,
        min_intensity: float = 0.0,
        low_extra: float = 0.0,
        high_extra: float = 0.0,
    ):
        self._rois = set()
        self._model = model
        self._min_intensity = min_intensity
        self._low_extra = low_extra
        self._high_extra = high_extra

    @property
    def rois(self) -> set[RegionOfInterest]:
        """The set of ``RegionOfInterest`` objects."""
        return self._rois

    @property
    def model(self) -> LineshapeModel:
        """The detector ``LineShapeModel``."""
        return self._model

    @property
    def min_intensity(self) -> float:
        """The minimum weighted intensity for an X-ray transition to be considered."""
        return self._min_intensity

    @property
    def low_extra(self) -> float:
        """
        In increment subtracted from the low energy side of
        the `RegionOfInterest` (in J).
        """
        return self._low_extra

    @property
    def high_extra(self) -> float:
        """
        In increment added to the high energy side of the `RegionOfInterest` (in J).
        """
        return self._high_extra

    @property
    def xrts(self) -> set[XRayTransition]:
        """
        Returns a set of the `XRayTransition` objects contained in
        this `RegionOfInterestSet`.
        """
        result = set()
        for roi in self.rois:
            result.update(roi.xrts)
        return result

    @property
    def elements(self) -> set[Element]:
        """
        Returns a set of the `Element` objects represented by
        this `RegionOfInterestSet`.
        """
        result = set()
        for roi in self.rois:
            result.update(roi.elements)
        return result

    def add_xrt(self, xrt: XRayTransition):
        """
        Constructs a new `RegionOfInterest` object and adds it to the
        existing `RegionOfInterestSet`.
        """
        roi = RegionOfInterest(
            xrt, self.model, self.min_intensity, self.low_extra, self.high_extra
        )
        if len(roi.xrts) > 0:
            self.add_roi(roi)

    def add_xrt_set(self, xrt_set: XRayTransitionSet):
        """
        Constructs and adds new `RegionOfInterest` objects for all x-ray transitions
        in the `xrt_set`.
        """
        for xrt in xrt_set.xrts:
            self.add_xrt(xrt)

    def add_roi(self, new_roi: RegionOfInterest):
        """
        Adds a new `RegionOfInterest` to the `RegionOfInterestSet`.
        If the `RegionOfInterest` overlaps with an existing one, they will be merged.
        """
        matches = set()
        for roi in self.rois:
            if roi.intersects(new_roi):
                matches.add(roi)
                new_roi.add_roi(roi)
        self._rois = self.rois - matches
        self._rois.add(new_roi)

    def add_element(self, element: Element, max_energy: float, min_weight: float):
        """
        Add all available `XRayTransition` objects with energy below the specified
        `max_energy` to the `RegionOfInterestSet`.
        """
        for transition in range(transition_from_name("MZ1") + 1):
            xrt = XRayTransition(element, transition)
            if (
                xrt.exists
                and xrt.edge_energy < max_energy
                and xrt.weight(normalization="family") >= min_weight
            ):
                self.add_xrt(xrt)

    def intersects(self, other: RegionOfInterest or RegionOfInterestSet):
        """
        Tests whether any of the `other` `RegionOfInterest` items overlap with
        any of the `self.rois`.
        """
        if isinstance(other, RegionOfInterest):
            other_rois = [other]
        else:
            other_rois = other.rois
        for other_roi in other_rois:
            for roi in self.rois:
                if roi.intersects(other_roi):
                    return True
        return False

    def contains(self, energy: float):
        """Tests whether one of the `self.rois` contains the specified `energy`."""
        for roi in self.rois:
            if roi.contains(energy):
                return True
        return False

    def fully_contains(self, other: RegionOfInterest):
        """
        Tests whether this `other` `RegionOfInterest` is fully contained
        within one of the `self.rois`.
        """
        for roi in self.rois:
            if roi.fully_contains(other):
                return True
        return False
