from __future__ import annotations

from abc import ABC, abstractmethod

from crypto_pulse.models import ContentItem


class CollectorError(RuntimeError):
    """A recoverable external-source failure."""


class BaseCollector(ABC):
    name: str

    @abstractmethod
    def collect(self, query: str, days: int, limit: int) -> list[ContentItem]:
        raise NotImplementedError

