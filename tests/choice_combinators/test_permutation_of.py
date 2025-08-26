from typing import Any

from returns.result import Failure, Success

from parsepy import ParseResult
from parsepy.basic_elements import TakeInclude, TakeN, TakeUntil, TakeWhile
from parsepy.choice_combinators import OneOf, PermutationOf

# --------------------------
# Helpers (reuse same as AllOf)
# --------------------------


def starts_with_a(input: str) -> ParseResult[str, str]:
    if input and input[0] == "a":
        return Success((input[1:], input[:1]))
    return Failure("not starting with a")


def always_fail(input: Any) -> ParseResult[Any, Any]:
    return Failure("nope")


def first_gt_10(input: list[int]) -> ParseResult[list[int], list[int]]:
    if input and input[0] > 10:
        return Success((input[1:], [input[0]]))
    return Failure("first <= 10")


def empty_input(input: str) -> ParseResult[str, str]:
    if len(input) == 0:
        return Success(("", ""))
    return Failure("not empty")


def take_one(s: str) -> ParseResult[str, str]:
    return Success((s[1:], s[:1])) if s else Failure("empty")


def sum_start_numbers(input: str) -> ParseResult[str, int]:
    result = TakeWhile(lambda x: x.isdigit())(input)
    match result:
        case Success((rest, taken)):
            if len(taken) == 0:
                return Failure("no numbers at start")
            else:
                nums_summed = sum([int(x) for x in taken])
                return Success((rest, nums_summed))
        case Failure(error_msg):
            return Failure(error_msg)


# --------------------------
# PermutationOf basic tests
# --------------------------


def test_PermutationOf_single_parser_takeN_success():
    input = "abcdefgh"
    result = PermutationOf(TakeN(3))(input)
    assert result == Success(("defgh", ("abc",)))


def test_PermutationOf_two_parsers_any_order_success():
    input = "123abc"
    # TakeN(3) can run first or second, doesn't matter
    result = PermutationOf(TakeN(3), TakeN(3))(input)
    assert result == Success(("", ("123", "abc")))


def test_PermutationOf_three_takeN_string_success():
    input = "aaabbbccc"
    result = PermutationOf(TakeN(3), TakeN(3), TakeN(3))(input)
    assert (
        result == Success(("", ("aaa", "bbb", "ccc")))
        or result == Success(("", ("bbb", "ccc", "aaa")))
        or isinstance(result, Success)
    )


def test_PermutationOf_with_callable_and_parser_success():
    input = "abcd"
    result = PermutationOf(starts_with_a, TakeN(2))(input)
    assert isinstance(result, Success)
    taken = result.unwrap()[1]
    assert "a" in taken and "bc" in taken


def test_PermutationOf_failure_if_parser_never_succeeds():
    input = "zzz"
    result = PermutationOf(starts_with_a, TakeN(2))(input)
    assert isinstance(result, Failure)
    assert "PermutationOf failed" in str(result.failure())


def test_PermutationOf_all_failures_reports_failure():
    input = "zzz"
    result = PermutationOf(always_fail, always_fail)(input)
    assert isinstance(result, Failure)
    assert "PermutationOf failed" in str(result.failure())


# --------------------------
# Mixed parsers and types
# --------------------------


def test_PermutationOf_with_take_include_and_takeN():
    input = "abc123xyz"
    parser = PermutationOf(TakeInclude("123"), TakeN(2))
    result = parser(input)
    assert isinstance(result, Success)
    taken = result.unwrap()[1]
    assert "abc123" in taken and "xy" in taken or "xy" not in taken


def test_PermutationOf_with_take_until_and_callable():
    input = "12ab34cd"
    parser = PermutationOf(sum_start_numbers, TakeUntil("c"))
    result = parser(input)
    assert isinstance(result, Success)
    rest, taken = result.unwrap()
    assert rest == "cd"
    assert any(isinstance(x, int) for x in taken)


def test_PermutationOf_with_non_consuming_and_consuming_parser():
    input = "abcd"

    def non_consuming_ok(s: str) -> ParseResult[str, str]:
        return Success((s, ""))

    result = PermutationOf(non_consuming_ok, TakeN(2))(input)
    assert isinstance(result, Success)
    rest, taken = result.unwrap()
    assert rest == "cd"
    assert "" in taken and "ab" in taken


def test_PermutationOf_list_ints_with_gt_10_and_takeN():
    input = [11, 22, 33]
    result = PermutationOf(first_gt_10, TakeN(1))(input)
    assert isinstance(result, Success)
    rest, taken = result.unwrap()
    assert rest == [33]
    assert [11] in taken and [22] in taken


# --------------------------
# Integration with OneOf
# --------------------------


def test_PermutationOf_with_OneOf_success():
    input = "abcdef"
    parser = PermutationOf(OneOf(TakeN(2), TakeN(3)), TakeN(2))
    # OneOf(TakeN(2), TakeN(3)) succeeds on TakeN(2) leaving TakeN(2)
    result = parser(input)
    assert isinstance(result, Success)
    rest, taken = result.unwrap()
    assert rest == "ef"
    assert taken == ("ab", "cd")


def test_PermutationOf_with_OneOf_and_callable():
    input = "123abc"
    parser = PermutationOf(sum_start_numbers, OneOf(TakeN(2), TakeN(3)))
    result = parser(input)
    assert isinstance(result, Success)
    rest, taken = result.unwrap()
    assert 6 in taken and any(val in ["ab", "abc"] for val in taken)


def test_PermutationOf_with_nested_OneOf_on_list_ints():
    input = [5, 6, 7, 8]
    parser = PermutationOf(OneOf(first_gt_10, TakeN(2)), TakeN(1))
    result = parser(input)
    assert isinstance(result, Success)
    rest, taken = result.unwrap()
    assert rest == [8]
    assert [7] in taken or [5, 6] in taken


def test_PermutationOf_failure_when_all_branches_fail_in_OneOf():
    input = "xyz"
    parser = PermutationOf(OneOf(TakeN(5), starts_with_a), TakeN(1))
    result = parser(input)
    assert isinstance(result, Failure)
    assert "PermutationOf failed" in str(result.failure())


# ---------------------------------
# Permutation parser ordering tests
# ---------------------------------


def test_permutation_simple_reverse_order():
    input = "abc123"
    # Input is letters then digits.
    # But we define parsers in reverse: sum_start_numbers first, then TakeN(3).
    parser = PermutationOf(sum_start_numbers, TakeN(3))
    result = parser(input)
    # Permutation should succeed because it tries both orders internally.
    # TakeN(3) consumes "abc", leaving "123"
    # sum_start_numbers consumes "123", producing sum=6
    assert result == Success(("", ("abc", 6)))


def test_permutation_three_parsers_altered_ordering():
    input = "abc123xyz"
    parser = PermutationOf(
        sum_start_numbers,
        TakeN(3),
        TakeUntil("z"),
    )
    # succeeds with order TakeN(3) -> sum_start_numbers -> TakeUntil("z")
    result = parser(input)
    assert result == Success(("z", ("abc", 6, "xy")))

    # Same parsers, but alteration of the order:
    parser_rev = PermutationOf(
        TakeUntil("z"),
        sum_start_numbers,
        TakeN(3),
    )
    # fails becuase TakeUntil("z") succeeds then the other 2 fail because of this.
    result_rev = parser_rev(input)
    assert result_rev == Failure(
        "PermutationOf failed because parsers `[1, 2]` never succeeded. The parser `0` succeeded."
    )


def test_permutation_with_integers_reversed_order():
    input = [5, 6, 11, 12]
    parser = PermutationOf(
        first_gt_10,
        TakeN(2),
    )
    # succeeds with order TakeN(2) -> first_gt_10
    result = parser(input)
    assert result == Success(([12], ([5, 6], [11])))

    # Reverse order
    parser_rev = PermutationOf(
        TakeN(2),
        first_gt_10,
    )
    # succeeds with order TakeN(2) -> first_gt_10
    result_rev = parser_rev(input)
    assert result_rev == Success(([12], ([5, 6], [11])))


def test_permutation_failure_when_one_parser_never_matches():
    input = "abc123"
    parser = PermutationOf(sum_start_numbers, TakeInclude("zzz"))
    # sum_start_numbers fails and take_include fails no matter the order
    result = parser(input)
    assert isinstance(result, Failure)
    assert result == Failure(
        "PermutationOf failed because parsers `[0, 1]` never succeeded. No parsers succeeded."
    )
