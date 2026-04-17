from __future__ import annotations

from typing import Any, Iterator


class SimpleArray:
    def __init__(self, data: Any):
        self._data = _normalize_data(data)

    @property
    def shape(self) -> tuple[int, ...]:
        return _shape_of(self._data)

    def tolist(self) -> Any:
        return _clone(self._data)

    def copy(self) -> "SimpleArray":
        return SimpleArray(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def __iter__(self) -> Iterator[Any]:
        for item in self._data:
            if isinstance(item, list):
                yield SimpleArray(item)
            else:
                yield item

    def __getitem__(self, item: Any) -> Any:
        value = self._data[item]
        if isinstance(value, list):
            return SimpleArray(value)
        return value


def asarray(data: Any, dtype: Any | None = None) -> SimpleArray:
    return SimpleArray(data)


float32 = "float32"
int32 = "int32"
ndarray = SimpleArray


def _normalize_data(data: Any) -> Any:
    if isinstance(data, SimpleArray):
        return data.tolist()
    if isinstance(data, tuple):
        return [_normalize_data(item) for item in data]
    if isinstance(data, list):
        return [_normalize_data(item) for item in data]
    return data


def _clone(data: Any) -> Any:
    if isinstance(data, list):
        return [_clone(item) for item in data]
    return data


def _shape_of(data: Any) -> tuple[int, ...]:
    if not isinstance(data, list):
        return ()
    if not data:
        return (0,)
    return (len(data), *_shape_of(data[0]))
