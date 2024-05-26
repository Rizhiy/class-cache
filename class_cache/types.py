from typing import TypeAlias, TypeVar

KeyType = TypeVar("KeyType")
ValueType = TypeVar("ValueType")
JsonType: TypeAlias = dict[str, "JsonType"] | list["JsonType"] | str | int | float | bool | None
MetaType = dict[str, JsonType]
