#  This file is part of Pynguin.
#
#  SPDX-FileCopyrightText: 2019–2026 Pynguin Contributors
#
#  SPDX-License-Identifier: MIT
#
import typing
from typing import overload


@overload
def combine(value: int) -> int: ...


@overload
def combine(value: str) -> str: ...


def combine(value: int | str) -> int | str:
    if value == "minimal":
        raise ValueError("invalid value")
    return value


class Container:
    @typing.overload
    def get(self, key: int) -> int: ...

    @typing.overload
    def get(self, key: str) -> str: ...

    def get(self, key: int | str) -> int | str:
        if key == "missing":
            raise KeyError(key)
        return key
