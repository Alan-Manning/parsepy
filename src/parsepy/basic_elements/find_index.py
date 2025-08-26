from collections.abc import Callable, Sequence
from inspect import signature
from typing import Literal


def find_index[T](
    input: Sequence[T],
    condition: T | Sequence[T] | Callable[[*tuple[T, ...]], bool],
    index_position: Literal["start", "end"],
) -> int:
    if isinstance(condition, Callable):
        return find_index_condition_function(
            input,
            condition,
            index_position=index_position,
        )
    else:
        return find_index_condition_match(
            input,
            condition,
            index_position=index_position,
        )


def find_index_condition_match[T](
    input: Sequence[T],
    condition_match: T | Sequence[T],
    index_position: Literal["start", "end"],
) -> int:
    """."""
    try:
        chunk_size = len(condition_match)
    except TypeError:
        chunk_size = 1

    for i in range(len(input)):
        input_chunk = input[i] if chunk_size == 1 else input[i : i + chunk_size]
        if condition_match == input_chunk:
            if index_position == "end":
                return i + chunk_size
            else:
                return i
    return -1


def find_index_condition_function[T](
    input: Sequence[T],
    condition_function: Callable[[*tuple[T, ...]], bool],
    index_position: Literal["start", "end"],
) -> int:
    """."""
    chunk_size = len(signature(condition_function).parameters)
    range_stop = len(input) - chunk_size + 1
    for i in range(range_stop):
        if condition_function(*input[i : i + chunk_size]):
            if index_position == "end":
                return i + chunk_size
            else:
                return i
    return -1
