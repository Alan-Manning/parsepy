from returns.result import Success, Failure
from parsepy.basic_elements import TakeN

# --------------------------
# Tests for TakeN
# --------------------------


def test_TakeN_takes_first_n_chars_positive():
    input = "Hello, world"
    result = TakeN(5)(input)
    assert result == Success((", world", "Hello"))


def test_TakeN_takes_first_n_chars_full_length():
    input = "abc"
    result = TakeN(3)(input)
    assert result == Success(("", "abc"))


def test_TakeN_fails_when_n_too_large_for_string():
    input = "Hi"
    result = TakeN(5)(input)
    assert isinstance(result, Failure)
    assert "Can't take N=" in str(result.failure())


def test_TakeN_takes_first_n_elements_list():
    input = [1, 2, 3, 4, 5]
    result = TakeN(3)(input)
    assert result == Success(([4, 5], [1, 2, 3]))


def test_TakeN_takes_all_elements_list():
    input = [1, 2, 3]
    result = TakeN(3)(input)
    assert result == Success(([], [1, 2, 3]))


def test_TakeN_fails_when_n_too_large_for_list():
    input = [1, 2]
    result = TakeN(5)(input)
    assert isinstance(result, Failure)
    assert "Can't take N=" in str(result.failure())


def test_TakeN_takes_last_n_chars_negative():
    input = "abcdef"
    result = TakeN(-3)(input)
    assert result == Success(("def", "abc"))


def test_TakeN_takes_last_n_elements_negative_list():
    input = [1, 2, 3, 4, 5]
    result = TakeN(-2)(input)
    assert result == Success(([4, 5], [1, 2, 3]))


def test_TakeN_takes_zero_elements_string():
    input = "abc"
    result = TakeN(0)(input)
    assert result == Success(("abc", ""))


def test_TakeN_takes_zero_elements_list():
    input = [1, 2, 3]
    result = TakeN(0)(input)
    assert result == Success(([1, 2, 3], []))
