from collections.abc import Sequence
from typing import Any, Never

import pytest
from returns.result import Failure, Success

from parsepy import ParseResult
from parsepy.basic_elements import TakeN, TakeUntil
from parsepy.choice_combinators import OneOf

# --------------------------
# Helpers (ParserLike callables)
# --------------------------


def starts_with_a(input: str) -> ParseResult[str, str]:
    """Succeeds when the first letter = `"a"`."""
    if input and input[0] == "a":
        return Success((input[1:], input[:1]))
    return Failure("not starting with a")


def always_fail(input: Sequence[Any]) -> ParseResult[Never, Never]:
    """Will always fail with err msg `nope`."""
    return Failure("nope")


def first_gt_10(input: list[int]) -> ParseResult[list[int], list[int]]:
    """Succeeds when the first number is greater than 10."""
    if input and input[0] > 10:
        return Success((input[1:], [input[0]]))
    return Failure("first <= 10")


def empty_input(input: str) -> ParseResult[str, str]:
    """Succeeds on empty input, consumes nothing."""
    if len(input) == 0:
        return Success(("", ""))
    return Failure("not empty")


def take_one(s: str) -> ParseResult[str, str]:
    """Takes exactly 1 char if possible, else fails."""
    return Success((s[1:], s[:1])) if s else Failure("empty")


def sum_start_numbers(input: str) -> ParseResult[str, int]:
    result = TakeUntil(lambda x: not x.isdigit())(input)
    match result:
        case Success((rest, taken)):
            nums_summed = sum([int(x) for x in taken])
            return Success((rest, nums_summed))
        case Failure(error_msg):
            return Failure(error_msg)


# --------------------------
# Tests
# --------------------------


def test_OneOf_first_parser_succeeds_returns_its_result():
    input = "abcd"
    result = OneOf(starts_with_a, TakeN(2))(input)
    assert result == Success(("bcd", "a"))


def test_OneOf_second_parser_succeeds_when_first_fails():
    input = "zzzz"
    result = OneOf(starts_with_a, TakeN(2))(input)
    assert result == Success(("zz", "zz"))


def test_OneOf_all_parsers_fail_returns_failure():
    input = "zzz"
    result = OneOf(always_fail, always_fail)(input)
    assert isinstance(result, Failure)
    assert "None or the parsers succeeded" in str(result.failure())


def test_OneOf_returns_first_success_even_if_later_also_succeeds():
    input = "abcd"
    result = OneOf(starts_with_a, TakeN(2))(input)
    assert result == Success(("bcd", "a"))


def test_OneOf_when_both_succeed_picks_first_even_if_second_consumes_more():
    input = "aaaa"
    result = OneOf(take_one, TakeN(2))(input)
    assert result == Success(("aaa", "a"))


def test_OneOf_accepts_baseparser_instances():
    input = "wxyz"
    result = OneOf(TakeN(2), TakeN(3))(input)
    assert result == Success(("yz", "wx"))


def test_OneOf_mixed_callable_and_baseparser():
    input = "abcd"
    result = OneOf(lambda s: Failure("nope"), TakeN(2))(input)
    assert result == Success(("cd", "ab"))


def test_OneOf_handles_empty_input_by_falling_through_to_success():
    input = ""
    result = OneOf(TakeN(1), empty_input)(input)
    assert result == Success(("", ""))


def test_OneOf_with_int_parsers_first_fails_second_succeeds():
    input = [5, 6, 7]
    result = OneOf(first_gt_10, TakeN(1))(input)
    assert result == Success(([6, 7], [5]))


def test_OneOf_with_numeric_sequence_input_parser_wins():
    input = [1, 2, 3, 4]
    result = OneOf(TakeN(2), TakeUntil(3))(input)
    # TakeN(2) matches first
    assert result == Success(([3, 4], [1, 2]))


def test_OneOf_accepts_only_callables_as_parsers():
    input = [5, 11, 12]
    result = OneOf(first_gt_10, first_gt_10)(input)
    assert isinstance(result, Failure)
    assert "None or the parsers succeeded." in result.failure()


def test_OneOf_fails_if_all_parsers_fail():
    input = ""
    result = OneOf(TakeUntil("a"), TakeN(2))(input)
    assert isinstance(result, Failure)
    assert "None or the parsers succeeded." in result.failure()


def test_OneOf_raises_if_no_parsers_given():
    with pytest.raises(ValueError):
        OneOf()


def test_OneOf_accepts_differing_taken_types() -> None:
    input = "123abc123xyz"
    # input = [1,3,32,4,2,4]
    result = OneOf(sum_start_numbers, TakeN(3))(input)
    assert result == Success(("abc123xyz", 6))
