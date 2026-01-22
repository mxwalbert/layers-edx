from dataclasses import dataclass
from typing import List, Tuple, Dict

DumpArgs = Tuple[Tuple[str, str], ...]


@dataclass(frozen=True)
class DumpRequest:
    module: str
    args: DumpArgs

    def __post_init__(self):
        # Sort arguments by key name so ('Z','26') vs ('trans','KA1')
        # always results in the same hash regardless of order in parametrize.
        sorted_args = tuple(sorted(self.args, key=lambda x: x[0]))
        object.__setattr__(self, "args", sorted_args)

    def to_batch_line(self) -> str:
        # Formats for Java TestDump: 'dump=XRayTransition Z=26 trans=KA1'
        arg_str = " ".join(f"{k}={v}" for k, v in self.args)
        return f"{self.module} {arg_str}"


CsvTable = List[Dict[str, str]]
