from returns.result import Success, Failure
from parsepy.basic_elements import TakeInclude


# --------------------------
# Tests for TakeInclude
# --------------------------


def test_TakeInclude_finds_single_char():
    input = "Hello, world"
    result = TakeInclude(",")(input)
    assert result == Success((" world", "Hello,"))


def test_TakeInclude_fails_when_char_not_found():
    input = "Hello world"
    result = TakeInclude(",")(input)
    assert isinstance(result, Failure)


def test_TakeInclude_finds_integer_in_list():
    input = [1, 2, 3, 4, 5]
    result = TakeInclude(3)(input)
    assert result == Success(([4, 5], [1, 2, 3]))


def test_TakeInclude_finds_subsequence_in_string():
    input = "abc123xyz"
    result = TakeInclude("123")(input)
    assert result == Success(("xyz", "abc123"))


def test_TakeInclude_with_callable_on_single_element():
    input = "Hello123"
    result = TakeInclude(lambda x: x.isnumeric())(input)
    assert result == Success(("23", "Hello1"))


def test_TakeInclude_with_callable_on_list_elements():
    input = [1, 2, 3, 4, 5]
    result = TakeInclude(lambda x: x > 3)(input)
    assert result == Success(([5], [1, 2, 3, 4]))


def test_TakeInclude_with_callable_multi_arg():
    input = [1, 2, 3, 4, 5]
    result = TakeInclude(lambda x, y: x + y > 6)(input)
    # First match: (2, 3) -> 5 (not > 6), (3, 4) -> 7, so match at index 2
    assert result == Success(([5], [1, 2, 3, 4]))


def test_TakeInclude_fails_on_callable_no_match():
    input = [1, 2, 3]
    result = TakeInclude(lambda x, y: x + y > 10)(input)
    assert isinstance(result, Failure)


def test_TakeInclude_with_single_char_str_edgecase():
    input = "aabb"
    result = TakeInclude("a")(input)
    assert result == Success(("abb", "a"))

def test_TakeInclude_with_escape_char_str_edgecase():
    input = "This is one line of text.\nThis is another line."
    result = TakeInclude("\n")(input)
    assert result == Success(("This is another line.", "This is one line of text.\n"))


def test_TakeInclude_with_bytes_subsequence():
    input = b"abc123"
    result = TakeInclude(b"123")(input)
    assert result == Success((b"", b"abc123"))
