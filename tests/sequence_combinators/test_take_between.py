from returns.result import Failure, Success

from parsepy.sequence_combinators import TakeBetween

# -------------------------------------------------------------------
# Basic string cases (single-char delimiters)
# -------------------------------------------------------------------


def test_TakeBetween_str_simple_delimiters_default_discard():
    input = "Hello Bob (the best Bob). Welcome."
    result = TakeBetween("(", ")")(input)
    assert result == Success((". Welcome.", "the best Bob"))


def test_TakeBetween_str_simple_delimiters_keep_end_in_rest():
    input = "Hello Bob (the best Bob). Welcome."
    result = TakeBetween("(", ")", discard_end_delimiter=False)(input)
    assert result == Success(("). Welcome.", "the best Bob"))


def test_TakeBetween_str_adjacent_delimiters_yield_empty_taken():
    input = "prefix()suffix"
    result = TakeBetween("(", ")")(input)
    assert result == Success(("suffix", ""))


def test_TakeBetween_str_multiple_ends_uses_first_after_start():
    input = "a[b]c]d"
    # First '[' then stops at the first ']' after it (before the second ']')
    result = TakeBetween("[", "]")(input)
    assert result == Success(("c]d", "b"))

    result = TakeBetween("[", "]", discard_end_delimiter=False)(input)
    assert result == Success(("]c]d", "b"))


# -------------------------------------------------------------------
# String with multi-char (sequence) delimiters
# -------------------------------------------------------------------


def test_TakeBetween_str_sequence_delimiters_default_discard():
    input = "xx<<middle>>yy"
    result = TakeBetween("<<", ">>")(input)
    assert result == Success(("yy", "middle"))


def test_TakeBetween_str_sequence_delimiters_keep_end_in_rest():
    input = "xx<<middle>>yy"
    result = TakeBetween("<<", ">>", discard_end_delimiter=False)(input)
    assert result == Success((">>yy", "middle"))


# -------------------------------------------------------------------
# String with callable delimiters (1-arg and 2-arg)
# -------------------------------------------------------------------


def test_TakeBetween_str_callable_numeric_delims_default_discard():
    input = "1 apple 2 oranges 3 melons."
    result = TakeBetween(
        lambda x: x.isnumeric(),
        lambda x: x.isnumeric(),
    )(input)
    assert result == Success((" oranges 3 melons.", " apple "))

    result = TakeBetween(
        lambda x: x.isnumeric(),
        lambda x: x.isnumeric(),
        discard_end_delimiter=False,
    )(input)
    assert result == Success(("2 oranges 3 melons.", " apple "))


def test_TakeBetween_str_callable_two_char_delims_angle_brackets():
    input = "aa<<mid>>bb"
    result = TakeBetween(
        lambda a, b: a == "<" and b == "<",
        lambda a, b: a == ">" and b == ">",
    )(input)
    assert result == Success(("bb", "mid"))

    result = TakeBetween(
        lambda a, b: a == "<" and b == "<",
        lambda a, b: a == ">" and b == ">",
        discard_end_delimiter=False,
    )(input)
    assert result == Success((">>bb", "mid"))


# -------------------------------------------------------------------
# List[int] with single-element delimiters
# -------------------------------------------------------------------


def test_TakeBetween_ints_simple_delimiters_default_discard():
    input = [0, 1, 2, 3, 4, 5, 9, 10]
    result = TakeBetween(1, 9)(input)
    assert result == Success(([10], [2, 3, 4, 5]))


def test_TakeBetween_ints_simple_delimiters_keep_end_in_rest():
    input = [0, 1, 2, 3, 4, 5, 9, 10]
    result = TakeBetween(1, 9, discard_end_delimiter=False)(input)
    assert result == Success(([9, 10], [2, 3, 4, 5]))


def test_TakeBetween_ints_adjacent_delimiters_empty_taken():
    input = [7, 8, 9, 10]
    result = TakeBetween(8, 9)(input)
    assert result == Success(([10], []))


# -------------------------------------------------------------------
# List[int] with sequence delimiters
# -------------------------------------------------------------------


def test_TakeBetween_ints_sequence_delimiters_default_discard():
    input = [0, 7, 8, 9, 1, 2, 3, 9, 10, 11]
    result = TakeBetween([7, 8, 9], [9, 10])(input)
    assert result == Success(([11], [1, 2, 3]))


def test_TakeBetween_ints_sequence_delimiters_keep_end_in_rest():
    input = [0, 7, 8, 9, 1, 2, 3, 9, 10, 11]
    result = TakeBetween([7, 8, 9], [9, 10], discard_end_delimiter=False)(input)
    assert result == Success(([9, 10, 11], [1, 2, 3]))


# -------------------------------------------------------------------
# List[int] with callable delimiters (1-arg and 2-arg)
# -------------------------------------------------------------------


def test_TakeBetween_ints_callable_delims_default_discard():
    input = [5, 6, 7, 8, 9, 12, 13]
    result = TakeBetween(
        lambda x: x % 2 == 0,
        lambda x: x > 10,
    )(input)
    assert result == Success(([13], [7, 8, 9]))


def test_TakeBetween_ints_callable_two_arg_delims_default_discard():
    input = [0, 7, 8, 1, 2, 9, 10, 11]
    result = TakeBetween(
        lambda a, b: a == 7 and b == 8,
        lambda a, b: a == 9 and b == 10,
    )(input)
    assert result == Success(([11], [1, 2]))


def test_TakeBetween_ints_callable_two_arg_keep_end_in_rest():
    input = [0, 7, 8, 1, 2, 9, 10, 11]
    result = TakeBetween(
        lambda a, b: a == 7 and b == 8,
        lambda a, b: a == 9 and b == 10,
        discard_end_delimiter=False,
    )(input)
    assert result == Success(([9, 10, 11], [1, 2]))


# -------------------------------------------------------------------
# Failure cases
# -------------------------------------------------------------------


def test_TakeBetween_failure_start_not_found_str():
    input = "abcdef"
    result = TakeBetween("x", "f")(input)
    assert isinstance(result, Failure)
    assert "Could not find start_delimiter" in str(result.failure())


def test_TakeBetween_failure_end_not_found_after_start_str():
    input = "abcdef"
    result = TakeBetween("a", "z")(input)
    assert isinstance(result, Failure)
    assert "Could not find end_delimiter" in str(result.failure())


def test_TakeBetween_failure_start_not_found_ints():
    input = [1, 2, 3, 4]
    result = TakeBetween(9, 4)(input)
    assert isinstance(result, Failure)
    assert "Could not find start_delimiter" in str(result.failure())


def test_TakeBetween_failure_end_not_found_after_start_ints():
    input = [1, 2, 3, 4]
    result = TakeBetween(1, 9)(input)
    assert isinstance(result, Failure)
    assert "Could not find end_delimiter" in str(result.failure())


# -------------------------------------------------------------------
# Edge cases and sanity checks
# -------------------------------------------------------------------


def test_TakeBetween_str_same_char_for_both_delims():
    input = "a|middle|b"
    result = TakeBetween("|", "|")(input)
    # between the first and the next '|'
    assert result == Success(("b", "middle"))


def test_TakeBetween_str_end_immediately_after_start_callable():
    input = "x()y"
    start = lambda c: c == "("
    end = lambda c: c == ")"
    result = TakeBetween(start, end)(input)
    assert result == Success(("y", ""))


def test_TakeBetween_str_multiple_pairs_picks_first_pair_only():
    input = "pre (one) mid (two) post"
    result = TakeBetween("(", ")")(input)
    assert result == Success((" mid (two) post", "one"))


# def test_between_with_string_delimiters_excludes_delimiters():
#     input = "Hello Bob (the best Bob). Welcome."
#     parser = TakeBetween("(", ")")
#     result = parser(input)
#     # Should capture inside the parentheses, without the delimiters
#     assert result == Success((". Welcome.", "the best Bob"))
#
#
# def test_between_with_string_delimiters_includes_delimiters():
#     input = "Hello Bob (the best Bob). Welcome."
#     parser = TakeBetween("(", ")", include_delimiters=True)
#     result = parser(input)
#     # Should capture including the parentheses
#     assert result == Success((". Welcome.", "(the best Bob)"))
#
#
# def test_between_with_sequence_delimiters():
#     input = list("xxSTARTmiddleENDyy")
#     parser = TakeBetween(list("START"), list("END"))
#     result = parser(input)
#     # Should capture "middle"
#     assert result == Success((list("yy"), list("middle")))
#
#
# def test_between_with_callable_delimiters():
#     input = "1 apple 2 oranges 3 melons."
#     parser = TakeBetween(lambda x: x.isnumeric(), lambda x: x.isnumeric())
#     result = parser(input)
#     # The first numeric char "1" starts, "4" is first numeric after "abc"
#     # So we capture "23abc"
#     assert result == Success((" oranges 3 melons.", " apple "))
#
#
# def test_between_with_callable_delimiters_with_delimiters():
#     input = "1 apple 2 oranges 3 melons."
#     result = TakeBetween(
#         lambda x: x.isnumeric(),
#         lambda x: x.isnumeric(),
#         include_delimiters=True,
#     )(input)
#     assert result == Success((" apple 2 oranges 3 melons.", "1"))
#
#     result = TakeBetween(
#         lambda x: x.isnumeric(),
#         lambda x: x.isnumeric() and x != 1,
#         include_delimiters=True,
#     )(input)
#
#
# def test_between_fails_if_start_delimiter_missing():
#     input = "abcdef"
#     parser = TakeBetween("(", ")")
#     result = parser(input)
#     assert isinstance(result, Failure)
#     assert "Could not find start_delimiter" in str(result.failure())
#
#
# def test_between_fails_if_end_delimiter_missing():
#     input = "Hello (world"
#     parser = TakeBetween("(", ")")
#     result = parser(input)
#     assert isinstance(result, Failure)
#     assert "Could not find end_delimiter" in str(result.failure())
#
#
# def test_between_with_int_delimiters_in_list():
#     input = [9, 1, 2, 3, 4, 5, 9, 10]
#     parser = TakeBetween(1, 9)
#     result = parser(input)
#     # Should capture [2,3,4,5]
#     assert result == Success(([10], [2, 3, 4, 5]))
#
#
# def test_between_with_int_delimiters_in_list_includes():
#     input = [0, 1, 2, 3, 4, 5, 9, 10]
#     parser = TakeBetween(1, 9, include_delimiters=True)
#     result = parser(input)
#     # Should capture [1,2,3,4,5,9]
#     assert result == Success(([10], [1, 2, 3, 4, 5, 9]))
#
#
# def test_between_with_sequence_int_delimiters():
#     input = [0, 7, 8, 9, 1, 2, 3, 9, 10, 11]
#     parser = TakeBetween([7, 8, 9], [9, 10])
#     result = parser(input)
#     # Should capture [1,2,3]
#     assert result == Success(([11], [1, 2, 3]))
#
#
# def test_between_with_lambda_start_ints():
#     input = [5, 6, 7, 8, 9, 10, 11]
#     # Start delimiter is first even number, end delimiter is first >9
#     parser = TakeBetween(lambda x: x % 2 == 0, lambda x: x > 9)
#     result = parser(input)
#     # Captures [7,8,9] (start delimiter is 6, stop delimiter is 10)
#     assert result == Success(([11], [7, 8, 9]))
#
#     parser = TakeBetween(lambda x: x % 2 == 0, lambda x: x > 9, include_delimiters=True)
#     result = parser(input)
#     # Captures [6, 7, 8, 9, 10] (start delimiter is 6, stop delimiter is 10)
#     assert result == Success(([11], [6, 7, 8, 9, 10]))
#
#
# def test_between_with_lambda_end_ints_includes():
#     input = [1, 2, 3, 4, 5, 6]
#     # Start at first odd (1), end at first even > 4 (6)
#     parser = TakeBetween(
#         lambda x: x % 2 == 1,
#         lambda x: x > 4 and x % 2 == 0,
#         include_delimiters=True,
#     )
#     result = parser(input)
#     # Should include [1,2,3,4,5,6]
#     assert result == Success(([], [1, 2, 3, 4, 5, 6]))
#
#
# def test_between_with_lambda_no_match_fails():
#     input = [1, 2, 3, 4, 5]
#     parser = TakeBetween(lambda x: x > 10, lambda x: x < 0)
#     result = parser(input)
#     assert isinstance(result, Failure)
#     assert "Could not find start_delimiter" in str(result.failure())
