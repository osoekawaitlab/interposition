from collections.abc import Callable
from typing import TypeVar, overload

_F = TypeVar("_F")

def step(pattern: str) -> Callable[[_F], _F]: ...
@overload
def before_scenario(func: _F) -> _F: ...
@overload
def before_scenario(tag: str) -> Callable[[_F], _F]: ...
@overload
def after_scenario(func: _F) -> _F: ...
@overload
def after_scenario(tag: str) -> Callable[[_F], _F]: ...

class _DataStore:
    scenario: dict[str, object]

data_store: _DataStore
