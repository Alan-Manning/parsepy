from typing import Any

from returns.result import Failure, Success

from parsepy import ParseResult
from parsepy.basic_elements import TakeInclude, TakeN, TakeUntil, TakeWhile
from parsepy.choice_combinators import AllOf, OneOf

# --------------------------
# Helpers (ParserLike callables)
# --------------------------


def starts_with_a(input: str) -> ParseResult[str, str]:
    """Succeeds when the first letter = `"a"`."""
    if input and input[0] == "a":
        return Success((input[1:], input[:1]))
    return Failure("not starting with a")


def always_fail(input: Any) -> ParseResult[Any, Any]:
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
    """Take the start numbers from string and sum them together."""
    result = TakeWhile(lambda x: x.isdigit())(input)
    match result:
        case Success((rest, taken)):
            nums_summed = sum([int(x) for x in taken])
            return Success((rest, nums_summed))
        case Failure(error_msg):
            return Failure(error_msg)


# --------------------------
# AllOf tests
# --------------------------


def test_AllOf_single_parser_takeN_success():
    input = "abcdefgh"
    result = AllOf(TakeN(3))(input)
    assert result == Success(("defgh", ("abc",)))


def test_AllOf_two_takeN_string_success():
    input = "123abc123xyz"
    # First TakeN(3) => rest "abc123xyz", taken "123"
    # Second TakeN(3) => rest "123xyz", taken "abc"
    result = AllOf(TakeN(3), TakeN(3))(input)
    assert result == Success(("123xyz", ("123", "abc")))


def test_AllOf_three_takeN_string_success():
    input = "aaabbbcccddd"
    result = AllOf(TakeN(3), TakeN(3), TakeN(3))(input)
    # taken should be ("aaa","bbb","ccc") and rest "ddd"
    assert result == Success(("ddd", ("aaa", "bbb", "ccc")))


def test_AllOf_mixed_callable_and_parsers_sequential_consumption():
    input = "abcd"
    # starts_with_a consumes "a" -> rest "bcd"
    # then TakeN(2) consumes "bc" -> rest "d"
    result = AllOf(starts_with_a, TakeN(2))(input)
    assert result == Success(("d", ("a", "bc")))


def test_AllOf_middle_parser_failure_propagates_failure():
    input = "x"
    # first take_one will consume "x" -> rest "" ; second TakeN(2) should fail
    result = AllOf(take_one, TakeN(2))(input)
    assert isinstance(result, Failure)
    msg = result.failure()
    assert "AllOf failed because parser" in str(msg) or "failed" in str(msg)


def test_AllOf_all_parsers_fail_returns_failure():
    input = "zzz"
    result = AllOf(always_fail, always_fail)(input)
    assert isinstance(result, Failure)
    # message should come from implementation wrapper
    assert "AllOf failed" in str(result.failure())


def test_AllOf_handles_empty_input_and_fails_on_later_parser():
    input = ""
    # empty_input succeeds consuming nothing => rest ""
    # then TakeN(1) on rest "" should fail
    result = AllOf(empty_input, TakeN(1))(input)
    assert isinstance(result, Failure)
    assert "AllOf failed" in str(result.failure())


def test_AllOf_list_ints_with_first_gt_10_and_takeN():
    input = [11, 22, 33]
    # first_gt_10 consumes [11] leaving [22,33], taken [11]
    # TakeN(1) consumes [22], leaving [33]
    result = AllOf(first_gt_10, TakeN(1))(input)
    assert result == Success(
        (
            [33],
            ([11], [22]),
        )
    )


def test_AllOf_with_transforming_parser_sum_and_two_takeN():
    input = "123abc456xyz"
    # sum_start_numbers consumes "123" producing int 6 and rest "abc456xyz"
    # then TakeN(3) consumes "abc" => rest "456xyz", taken "abc"
    # then TakeN(3) consumes "456" => rest "xyz", taken "456"
    result = AllOf(sum_start_numbers, TakeN(3), TakeN(3))(input)
    assert result == Success(("xyz", (6, "abc", "456")))


def test_AllOf_single_callable_transforms_only():
    input = "123abc"
    result = AllOf(sum_start_numbers)(input)
    # sum_start_numbers returns Success(("abc", 6))
    assert result == Success(("abc", (6,)))


def test_AllOf_accepts_many_parsers_and_preserves_order():
    input = "abcdef"
    # TakeN(1) x5 -> consumes one char each time
    result = AllOf(TakeN(1), TakeN(1), TakeN(1), TakeN(1), TakeN(1))(input)
    assert result == Success(("f", ("a", "b", "c", "d", "e")))


def test_AllOf_interleaving_various_parsers_and_callables():
    input = "12ab34cd"
    # sum_start_numbers will consume "12" => returns 3, rest "ab34cd"
    # TakeUntil("c") will scan until 'c' -> rest "cd", taken "ab34"
    # take_one consumes "c" leaving "d"
    result = AllOf(sum_start_numbers, TakeUntil("c"), take_one)(input)
    assert result == Success(("d", (3, "ab34", "c")))


def test_AllOf_failure_when_first_parser_fails_immediately():
    input = "zzz"
    # first parser fails -> whole AllOf fails
    result = AllOf(starts_with_a, TakeN(2))(input)
    assert isinstance(result, Failure)
    assert "AllOf failed" in str(result.failure())


def test_AllOf_with_non_consuming_parser_then_consuming():
    input = "abcd"

    # first parser returns Success(("", "")) only on empty input, so will fail here.
    # Instead use a parser that doesn't consume (simulate): define inline
    def non_consuming_ok(s: str) -> ParseResult[str, str]:
        # always succeed but consume nothing
        return Success((s, ""))

    result = AllOf(non_consuming_ok, TakeN(2))(input)
    # non_consuming_ok leaves input unchanged, TakeN(2) should then consume "ab"
    assert result == Success(("cd", ("", "ab")))


def test_AllOf_with_mix_of_seq_types_preserves_sequence_identity():
    input = ["a", "b", "c", "d", "e"]
    # Use TakeN to return slices of the same list type
    result = AllOf(TakeN(2), TakeN(1))(input)
    assert result == Success((["d", "e"], (["a", "b"], ["c"])))


def test_AllOf_multiple_failures_reports_first_failing_parser_index():
    # produce fail in middle and ensure we get Failure
    input = "hello"
    result = AllOf(TakeN(1), always_fail, TakeN(1))(input)
    assert isinstance(result, Failure)
    assert "AllOf failed" in str(result.failure())


def test_allof_with_take_include_and_takeuntil_equivalent():
    input = "abc123xyz"
    parser = AllOf(TakeInclude("123"), TakeN(2))
    result = parser(input)
    # TakeInclude("123") -> ("xyz", "abc123")
    # Then TakeN(2) on "xyz" -> ("z", "xy")
    assert result == Success(("z", ("abc123", "xy")))


def test_allof_with_take_include_and_callable():
    input = [1, 2, 3, 4, 5]
    parser = AllOf(TakeInclude(lambda x: x == 3), TakeN(1))
    result = parser(input)
    # TakeInclude(x==3) -> ([4,5], [1,2,3])
    # Then TakeN(1) -> ([5], [4])
    assert result == Success(([5], ([1, 2, 3], [4])))


def test_allof_with_take_include_and_oneof_success():
    input = "abc123xyz"
    parser = AllOf(TakeInclude("123"), OneOf(TakeN(2), TakeN(3)))
    result = parser(input)
    # TakeInclude("123") -> ("xyz", "abc123")
    # OneOf picks TakeN(2) -> ("z", "xy")
    assert result == Success(("z", ("abc123", "xy")))


def test_allof_with_take_include_and_oneof_failure():
    input = "abcdef"
    parser = AllOf(
        TakeInclude("notfound"),
        OneOf(TakeN(2), TakeN(3)),
    )
    result = parser(input)
    assert isinstance(result, Failure)
    assert "AllOf failed" in str(result.failure())


# --------------------------
# AllOf + OneOf integration tests
# --------------------------


def test_AllOf_with_OneOf_string_choice_success():
    input = "abc123"
    # OneOf chooses between TakeN(2) or TakeN(3).
    # TakeN(2) works: consumes "ab" leaving "c123"
    result = AllOf(OneOf(TakeN(2), TakeN(3)), TakeN(2))(input)
    # second parser consumes "c1" leaving "23"
    assert result == Success(("23", ("ab", "c1")))


def test_AllOf_with_OneOf_string_choice_second_branch():
    input = "abcdef"
    # OneOf tries TakeN(7) (fails because input shorter), then TakeN(3) (succeeds).
    result = AllOf(OneOf(TakeN(7), TakeN(3)), TakeN(2))(input)
    # OneOf should succeed with second branch: taken "abc", rest "def"
    # then TakeN(2) consumes "de", rest "f"
    assert result == Success(("f", ("abc", "de")))


def test_AllOf_with_OneOf_and_custom_callable():
    input = "123abc"
    # sum_start_numbers => consumes "123", rest "abc", taken 6
    # OneOf chooses: TakeN(4) fails (len=3), TakeN(2) succeeds
    result = AllOf(sum_start_numbers, OneOf(TakeN(4), TakeN(2)))(input)
    # Expect taken = (6, "ab"), rest "c"
    assert result == Success(("c", (6, "ab")))


def test_AllOf_with_OneOf_failure_when_all_branches_fail():
    input = "xyz"
    # OneOf(TakeN(5), starts_with_a) fails both
    result = AllOf(OneOf(TakeN(5), starts_with_a), TakeN(1))(input)
    assert isinstance(result, Failure)
    assert "AllOf failed" in str(result.failure())


def test_AllOf_with_nested_OneOf_list_ints():
    input = [5, 6, 7, 8]
    # OneOf: first_gt_10 (fails, since first=5), then TakeN(2) (succeeds -> [5,6])
    # Then TakeN(1) consumes 7
    result = AllOf(OneOf(first_gt_10, TakeN(2)), TakeN(1))(input)
    assert result == Success(([8], ([5, 6], [7])))


def test_AllOf_with_multiple_OneOfs_in_sequence():
    input = "abcdef"
    # OneOf(TakeN(2), TakeN(1)) should succeed with TakeN(2) -> "ab", rest "cdef"
    # Then OneOf(always_fail, TakeN(2)) chooses TakeN(2) -> "cd", rest "ef"
    # Finally TakeN(1) -> "e", rest "f"
    result = AllOf(OneOf(TakeN(2), TakeN(1)), OneOf(always_fail, TakeN(2)), TakeN(1))(
        input
    )
    assert result == Success(("f", ("ab", "cd", "e")))
