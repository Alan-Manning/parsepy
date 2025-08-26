from returns.result import Success, Failure
from parsepy.basic_elements import TakeUntil

# --------------------------
# Tests for TakeUntil
# --------------------------


def test_TakeUntil_finds_single_char():
    input = "Hello, world"
    result = TakeUntil(",")(input)
    assert result == Success((", world", "Hello"))


def test_TakeUntil_fails_single_char_not_found():
    input = "Hello world"
    result = TakeUntil(",")(input)
    assert isinstance(result, Failure)
    assert "Could not find condition" in result.failure()


def test_TakeUntil_consumes_all_when_single_char_not_found_and_fail_on_no_match_false():
    input = "Hello world"
    result = TakeUntil(",", fail_on_no_match=False)(input)
    assert result == Success(("", "Hello world"))


def test_TakeUntil_finds_sequence_of_chars():
    input = "abc123xyz"
    result = TakeUntil("123")(input)
    assert result == Success(("123xyz", "abc"))


def test_TakeUntil_fails_sequence_not_found():
    input = "abcdef"
    result = TakeUntil("123")(input)
    assert isinstance(result, Failure)


def test_TakeUntil_consumes_all_when_sequence_not_found_and_fail_on_no_match_false():
    input = "abcdef"
    result = TakeUntil("123", fail_on_no_match=False)(input)
    assert result == Success(("", "abcdef"))


def test_TakeUntil_finds_int_element():
    input = [1, 2, 3, 4, 5]
    result = TakeUntil(3)(input)
    assert result == Success(([3, 4, 5], [1, 2]))


def test_TakeUntil_finds_sequence_of_ints():
    input = [1, 2, 99, 100, 5]
    result = TakeUntil([99, 100])(input)
    assert result == Success(([99, 100, 5], [1, 2]))


def test_TakeUntil_callable_single_arg_match():
    input = "Hello123"
    result = TakeUntil(lambda x: x.isnumeric())(input)
    assert result == Success(("123", "Hello"))


def test_TakeUntil_callable_single_int_arg_match():
    input = [1, 2, 3, 4, 5]
    result = TakeUntil(lambda x: x > 3)(input)
    assert result == Success(([4, 5], [1, 2, 3]))


def test_TakeUntil_callable_multi_arg_match():
    input = [1, 2, 3, 4, 5]
    result = TakeUntil(lambda x, y: x + y > 6)(input)
    assert result == Success(([3, 4, 5], [1, 2]))


def test_TakeUntil_callable_never_matches_and_fails():
    input = [1, 2, 3]
    result = TakeUntil(lambda x: x > 10)(input)
    assert isinstance(result, Failure)
    assert "Could not find where condition" in result.failure()


def test_TakeUntil_callable_never_matches_and_consumes_all_if_fail_on_no_match_false():
    input = [1, 2, 3]
    result = TakeUntil(lambda x: x > 10, fail_on_no_match=False)(input)
    assert result == Success(([], [1, 2, 3]))
