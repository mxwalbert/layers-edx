from __future__ import annotations
import numpy as np
import numpy.typing as npt


class Interval:
    """A continuous range of integers [lower, upper)."""

    @staticmethod
    def merge(interval1: Interval, interval2: Interval) -> Interval:
        """Returns a new interval over the minimum of the lower values to the maximum of the upper values."""
        return Interval(min(interval1.lower, interval2.lower), max(interval1.upper, interval2.upper))

    @staticmethod
    def overlaps(interval1: Interval, interval2: Interval) -> bool:
        """Checks if the two intervals overlap."""
        return interval1.lower <= interval2.upper and interval2.lower <= interval1.upper

    @classmethod
    def sortmerge(cls, intervals: list[Interval]) -> list[Interval]:
        """Inplace sorts the provided list of `intervals` and merges overlapping intervals."""
        intervals.sort(key=lambda x: x.lower)
        i = 0
        while i < len(intervals) - 1:
            if cls.overlaps(intervals[i], intervals[i+1]):
                intervals[i] = cls.merge(intervals[i], intervals[i+1])
                intervals.pop(i+1)
                i = 0
            else:
                i += 1
        return intervals

    @classmethod
    def extract(cls, length: int, intervals: list[Interval]) -> npt.NDArray[bool]:
        """Generates a boolean array with the provided `length` and fills the `intervals` with ``True``."""
        bool_arr = np.zeros(length, dtype=bool)
        for interval in intervals:
            bool_arr[interval.lower:interval.upper] = True
        return bool_arr

    def __init__(self, lower: int, upper: int):
        self.lower = lower
        self.upper = upper


class NonZeroInterval(Interval):
    """An interval containing all non-zero channels in the array `data`."""

    def __init__(self, data: npt.NDArray[np.floating]):
        lower = int(np.argmax(data != 0))
        upper = int(len(data) - 1 - np.argmax(data[::-1] != 0).item())
        super().__init__(lower, upper)
