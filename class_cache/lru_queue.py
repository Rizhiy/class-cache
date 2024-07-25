from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, Iterator

from .types import KeyType


@dataclass(slots=True, eq=False)
class Link(Generic[KeyType]):
    prev: Link
    next: Link
    key: KeyType


# Adapted from https://github.com/python/cpython/blob/5592399313c963c110280a7c98de974889e1d353/Lib/functools.py#L542
class LRUQueue(Generic[KeyType]):
    def __init__(self):
        self._links = {}
        self._root = Link(None, None, None)  # type: ignore
        self._root.prev = self._root
        self._root.next = self._root

    def __contains__(self, key: KeyType) -> bool:
        if result := key in self._links:
            self.update(key)
        return result

    def _move_to_front(self, link: Link) -> None:
        next_ = self._root.next

        next_.prev = link
        link.next = next_

        self._root.next = link
        link.prev = self._root

    @staticmethod
    def _connect_neighbours(link: Link) -> None:
        link.prev.next = link.next
        link.next.prev = link.prev

    def update(self, key: KeyType) -> None:
        if key in self._links:
            link = self._links[key]
            # Connect neighbouring keys
            self._connect_neighbours(link)
        else:
            link = Link(None, None, key)  # type: ignore
            self._links[key] = link
        self._move_to_front(link)

    def peek(self) -> KeyType:
        if self._root.prev == self._root:
            raise IndexError("peeking into an empty queue")

        return self._root.prev.key

    def pop(self) -> KeyType:
        if self._root.prev == self._root:
            raise IndexError("pop from an empty queue")

        last = self._root.prev
        self._connect_neighbours(last)
        key = last.key
        del self._links[key]
        return key

    def __delitem__(self, key: KeyType) -> None:
        link = self._links[key]
        del self._links[key]
        self._connect_neighbours(link)

    def __len__(self) -> int:
        return len(self._links)

    def __iter__(self) -> Iterator[KeyType]:
        current = self._root
        while current.next != self._root:
            yield current.next.key
            current = current.next

    def __str__(self) -> str:
        result = ""
        for key in self:
            result += f"{key} -> "
        return result[:-4]


__all__ = ["LRUQueue"]
