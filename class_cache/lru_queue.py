from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, Iterator

from .types import KeyType


@dataclass(slots=True, eq=False)
class Link(Generic[KeyType]):
    prev: Link
    next: Link
    key: KeyType

    def __str__(self) -> str:
        prev = self.prev.key if self.prev is not None and self.prev.key is not None else None
        next_ = self.next.key if self.next is not None and self.next.key is not None else None
        return f"Link(prev={prev}, next={next_}, key={self.key})"


# Adapted from https://github.com/python/cpython/blob/5592399313c963c110280a7c98de974889e1d353/Lib/functools.py#L542
class LRUQueue(Generic[KeyType]):
    class _Root:
        def __str__(self) -> str:
            return "__ROOT__"

    def __init__(self):
        self._links = {}
        self._root = Link(None, None, self._Root())  # type: ignore
        self._root.prev = self._root
        self._root.next = self._root
        # TODO: Add a lock

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

    def _cut(self, first: Link, last: Link = None, *, delete=True) -> None:
        """
        Cut from first, up to link before last, last will remain.
        """
        last = last or first.next
        if first == last:
            raise ValueError("Invalid arguments, first and last must be different")

        first.prev.next = last
        last.prev = first.prev

        if not delete:
            return

        current = first
        while current != last:
            del self._links[current.key]
            current = current.next

    def _check_empty(self, *, no_raise=False) -> None | bool:
        if self._root.prev == self._root:
            if no_raise:
                return True
            raise IndexError("pop from an empty queue")

    def update(self, key: KeyType) -> None:
        if key in self._links:
            link = self._links[key]
            self._cut(link, delete=False)
        else:
            link = Link(None, None, key)  # type: ignore
            self._links[key] = link
        self._move_to_front(link)

    def peek(self) -> KeyType:
        self._check_empty()

        return self._root.prev.key

    def pop(self) -> KeyType:
        self._check_empty()

        last = self._root.prev
        self._cut(last)
        return last.key

    def pop_many(self, count: int) -> list[KeyType]:
        if self._check_empty(no_raise=True):
            return []

        first = self._root.prev
        keys = []
        for _ in range(count):
            keys.append(first.key)
            first = first.prev

            if first == self._root:
                break
        first = first.next

        self._cut(first, self._root)

        return keys

    def __delitem__(self, key: KeyType) -> None:
        link = self._links[key]
        self._cut(link)

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
