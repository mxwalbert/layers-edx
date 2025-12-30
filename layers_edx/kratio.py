from layers_edx.xrt import XRayTransitionSet, XRayTransition
from layers_edx.element import Element


class KRatioSet:
    def __init__(self):
        self._data: dict[XRayTransitionSet, float] = {}

    @property
    def xrt_sets(self) -> list[XRayTransitionSet]:
        """An ordered list of `XRayTransitionSet`s which correspond to the `kratios`."""
        return list(self._data.keys())

    @property
    def kratios(self) -> list[float]:
        """
        An ordered list of float values which represent the k-ratios of the `xrt_sets`.
        """
        return list(self._data.values())

    @property
    def kratio_sum(self) -> float:
        """The sum of non-negative k-ratios."""
        return sum([kratio for kratio in self.kratios if kratio > 0.0])

    @property
    def elements(self) -> set[Element]:
        """The set of elements which are represented by the `xrt_sets`."""
        return set([xrt_set.element for xrt_set in self.xrt_sets])

    def add(self, xrt_set: XRayTransitionSet, kratio: float):
        """
        Adds the `kratio` to the data dictionary. Overwrites an existing value
        if the `xrt_set` is already in the data dictionary.
        """
        self._data[xrt_set] = kratio

    def remove(self, xrt_set):
        """
        Removes the `xrt_set` and the associated k-ratio value from the data dictionary.
        """
        if xrt_set in self.xrt_sets:
            del self._data[xrt_set]

    def find(self, xrt_set: XRayTransitionSet) -> float:
        """
        Checks if the `xrt_set` already has an associated k-ratio. Otherwise, checks
        for a similar `XRayTransitionSet` to return its value.
        """
        if xrt_set in self._data:
            return self._data[xrt_set]
        score = 0.0
        kratio = None
        xrt = xrt_set.weightiest_transition
        for data_xrt_set, data_kratio in self._data.items():
            if xrt in data_xrt_set.xrts:
                similarity = xrt_set.similarity(data_xrt_set)
                if similarity > 0.8 and similarity > score:
                    score = similarity
                    kratio = data_kratio
        return kratio

    def kratio_from_xrt_set_raw(self, xrt_set: XRayTransitionSet) -> float:
        """Returns the raw k-ratio value. Might be negative."""
        kratio = self.find(xrt_set)
        return kratio if kratio is not None else 0.0

    def kratio_from_xrt_set(self, xrt_set: XRayTransitionSet) -> float:
        """Returns the non-negative k-ratio value associated with an `xrt_set`."""
        kratio = self.find(xrt_set)
        return kratio if kratio > 0.0 else 0.0

    def kratio_from_xrt(self, xrt: XRayTransition) -> float:
        """
        Returns the k-ratio value associated with an `XRayTransitionSet`
        which contains the `xrt`.
        """
        for xrt_set in self.xrt_sets:
            if xrt in xrt_set.xrts:
                return self.kratio_from_xrt_set(xrt_set)
        return 0.0
