from layers_edx.fitting.filter_fit.filtered_spectrum import FilteredSpectrum
from layers_edx.fitting.parameter import Parameter


class FilterParameter(Parameter):
    """A packet of data associated with each filtered spectrum."""

    def __init__(
        self,
        filtered: FilteredSpectrum,
        naive: bool = True,
        model_thresh: float = 1.0e3,
    ):
        super().__init__(filtered.element, filtered.xrt_set)
        self._filtered = filtered
        self._naive = naive
        self._model_thresh = model_thresh

    @property
    def filtered(self) -> FilteredSpectrum:
        """Returns the associated ``FilteredSpectrum`` object."""
        return self._filtered

    @property
    def naive(self) -> bool:
        """
        Flags whether to use the naive (default) implementation of the
        background modelling.
        """
        return self._naive

    @property
    def model_thresh(self) -> float:
        """The threshold energy in eV for the modelling of the background."""
        return self._model_thresh
