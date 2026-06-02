from __future__ import annotations

from dataclasses import fields, is_dataclass
from numbers import Real
from typing import Any


class HistoryBuffer:
    """Bounded multi-resolution history for example charts."""

    def __init__(
        self,
        raw_limit: int = 2000,
        level_limit: int = 2000,
        chunk_size: int = 10,
        max_levels: int = 5,
    ) -> None:
        if raw_limit <= 0:
            raise ValueError("raw_limit must be greater than zero")
        if level_limit <= 0:
            raise ValueError("level_limit must be greater than zero")
        if chunk_size < 2:
            raise ValueError("chunk_size must be at least two")
        if max_levels <= 0:
            raise ValueError("max_levels must be greater than zero")

        self.raw_limit = raw_limit
        self.level_limit = level_limit
        self.chunk_size = chunk_size
        self._raw: list[Any] = []
        self._levels: list[list[Any]] = [[] for _ in range(max_levels)]

    def add(self, sample: Any) -> None:
        if not is_dataclass(sample):
            raise TypeError("sample must be a dataclass instance")

        self._raw.append(sample)
        while len(self._raw) > self.raw_limit:
            chunk = self._raw[: self.chunk_size]
            del self._raw[: self.chunk_size]
            self._promote(0, self._aggregate(chunk))

    def clear(self) -> None:
        self._raw = []
        self._levels = [[] for _ in self._levels]

    def visible_points(self, max_points: int = 1600) -> list[Any]:
        samples = self._all_samples()
        if max_points <= 0:
            return []
        if len(samples) <= max_points:
            return samples
        if max_points == 1:
            return [samples[-1]]

        step = (len(samples) - 1) / (max_points - 1)
        return [samples[round(index * step)] for index in range(max_points)]

    def _promote(self, level_index: int, sample: Any) -> None:
        level = self._levels[level_index]
        level.append(sample)

        while len(level) > self.level_limit:
            chunk = level[: self.chunk_size]
            del level[: self.chunk_size]
            aggregate = self._aggregate(chunk)
            if level_index + 1 < len(self._levels):
                self._promote(level_index + 1, aggregate)
            else:
                level.insert(0, aggregate)

    def _all_samples(self) -> list[Any]:
        samples: list[Any] = []
        for level in reversed(self._levels):
            samples.extend(level)
        samples.extend(self._raw)
        return samples

    @staticmethod
    def _aggregate(samples: list[Any]) -> Any:
        sample_type = type(samples[-1])
        values = {}

        for field in fields(samples[-1]):
            field_values = [getattr(sample, field.name) for sample in samples]
            if all(isinstance(value, Real) for value in field_values):
                values[field.name] = sum(field_values) / len(field_values)
            else:
                values[field.name] = field_values[-1]

        return sample_type(**values)
