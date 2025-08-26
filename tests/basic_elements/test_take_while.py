from returns.result import Success
from parsepy.basic_elements import TakeWhile

# --------------------------
# Tests for TakeWhile
# --------------------------

# --- Single element condition ---


def test_TakeWhile_single_element_stops_on_mismatch():
    input = [1, 1, 1, 2, 3]
    result = TakeWhile(1)(input)
    assert result == Success(([2, 3], [1, 1, 1]))


def test_TakeWhile_single_element_consumes_all_matches():
    input = "aaaa"
    result = TakeWhile("a")(input)
    assert result == Success(("", "aaaa"))


def test_TakeWhile_single_element_immediate_fail():
    input = "abc"
    result = TakeWhile("x")(input)
    assert result == Success(("abc", ""))


def test_TakeWhile_single_element_empty_input():
    input = ""
    result = TakeWhile("a")(input)
    assert result == Success(("", ""))


# --- Sequence[T] condition (chunk mode) ---


def test_TakeWhile_sequence_condition_consumes_chunks():
    input = "aaabbb"
    result = TakeWhile("aa")(input)
    assert result == Success(("abbb", "aa"))


def test_TakeWhile_sequence_condition_consumes_full_input():
    input = "aaaa"
    result = TakeWhile("aa")(input)
    assert result == Success(("", "aaaa"))


def test_TakeWhile_sequence_condition_immediate_fail():
    input = "bbaa"
    result = TakeWhile("aa")(input)
    assert result == Success(("bbaa", ""))


def test_TakeWhile_sequence_condition_chunk_longer_than_input():
    input = "a"
    result = TakeWhile("aaa")(input)
    assert result == Success(("a", ""))


def test_TakeWhile_sequence_condition_empty_input():
    input = ""
    result = TakeWhile("aa")(input)
    assert result == Success(("", ""))


# --- Callable condition (sliding window) ---


def test_TakeWhile_callable_increasing_pairs():
    input = [1, 2, 3, 4, 5, 1, 2, 3]
    result = TakeWhile(lambda x, y: x < y)(input)
    assert result == Success(([1, 2, 3], [1, 2, 3, 4, 5]))


def test_TakeWhile_callable_pair_immediate_fail():
    input = [3, 2, 1, 0]
    result = TakeWhile(lambda x, y: x < y)(input)
    assert result == Success(([3, 2, 1, 0], []))


def test_TakeWhile_callable_triples_strictly_increasing():
    input = [1, 2, 3, 4, 5, 1, 2, 3]
    result = TakeWhile(lambda x, y, z: x < y < z)(input)
    assert result == Success(([1, 2, 3], [1, 2, 3, 4, 5]))


def test_TakeWhile_callable_always_true():
    input = [1, 2, 3]
    result = TakeWhile(lambda *_: True)(input)
    assert result == Success(([], [1, 2, 3]))


def test_TakeWhile_callable_always_false():
    input = [1, 2, 3]
    result = TakeWhile(lambda *_: False)(input)
    assert result == Success(([1, 2, 3], []))


def test_TakeWhile_callable_window_larger_than_input():
    input = [1]
    result = TakeWhile(lambda x, y: x < y)(input)
    assert result == Success(([], [1]))


# --- Edge cases / mixed ---


def test_TakeWhile_single_element_input_matches():
    input = ["x"]
    result = TakeWhile("x")(input)
    assert result == Success(([], ["x"]))


def test_TakeWhile_single_element_input_not_matching():
    input = ["y"]
    result = TakeWhile("x")(input)
    assert result == Success((["y"], []))
