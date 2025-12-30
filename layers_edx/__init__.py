from __future__ import annotations
import os
import csv
from typing import TypeVar, Callable, Type, Any

BASE_PATH = os.path.dirname(__file__)

IntOrFloat = TypeVar("IntOrFloat", int, float)

llf = list[list[float]]
lli = list[list[int]]


def read_csv(
    filename: str,
    value_offset: int = 0,
    row_offset: int = 0,
    column_offset: int = 0,
    nan: float | int | str = 0,
    conversion: Callable[[IntOrFloat], IntOrFloat] = lambda x: x,
    dtype: Type[IntOrFloat] = float,
    fill_value: Any = None,
) -> list[list[IntOrFloat]]:
    fill_value = [] if fill_value is None else [fill_value]
    values = [fill_value for _ in range(value_offset)]
    with open(f"{BASE_PATH}/resources/{filename}.csv") as file:
        current = -1
        for row in csv.reader(file):
            current += 1
            if row_offset > current:
                continue
            values.append(
                [
                    dtype(nan) if value == "" else conversion(dtype(value))
                    for value in row[column_offset:]
                ]
            )
    return values
