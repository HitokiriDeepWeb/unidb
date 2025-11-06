from abc import abstractmethod
from collections.abc import Iterable
from typing import Any, Protocol


class StringKeyMapping(Protocol):
    """Any dict like object."""

    @abstractmethod
    def keys(self) -> Iterable[str]:
        pass

    @abstractmethod
    def __getitem__(self, key: str, /) -> Any:
        pass
