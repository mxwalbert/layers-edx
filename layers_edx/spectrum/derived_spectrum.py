import copy
from layers_edx.spectrum.base_spectrum import BaseSpectrum


class DerivedSpectrum(BaseSpectrum):

    def __init__(self, source: BaseSpectrum):
        self._source = source
        self._properties = copy.copy(source.properties)
        super().__init__(self._properties)

    @property
    def source(self) -> BaseSpectrum:
        return self._source

    @property
    def channel_count(self) -> int:
        return self.source.channel_count
