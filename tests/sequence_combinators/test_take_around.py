from returns.result import Failure, Success

from parsepy.sequence_combinators import TakeAround


###############################################################################
# String inputs
###############################################################################
def test_TakeAround_str_simple_delimiters():
    input = "Hello Bob (the best Bob). Welcome."
    result = TakeAround("(", ")")(input)
    assert result == Success((". Welcome.", "(the best Bob)"))


def test_TakeAround_str_sequence_delimiters():
    input = "BEGIN some text END here"
    result = TakeAround("BEGIN", "END")(input)
    assert result == Success((" here", "BEGIN some text END"))


def test_TakeAround_str_callable_delimiters():
    input = "1 apple 2 oranges 3 melons."
    result = TakeAround(
        lambda x: x.isnumeric(),
        lambda x: x.isnumeric(),
    )(input)
    assert result == Success((" oranges 3 melons.", "1 apple 2"))


###############################################################################
# Failures
###############################################################################
def test_TakeAround_fail_missing_start():
    input = "Hello Bob the best Bob). Welcome."
    result = TakeAround("(", ")")(input)
    assert isinstance(result, Failure)


def test_TakeAround_fail_missing_end():
    input = "Hello Bob (the best Bob. Welcome."
    result = TakeAround("(", ")")(input)
    assert isinstance(result, Failure)


###############################################################################
# List[int] inputs
###############################################################################
def test_TakeAround_list_int_simple_delimiters():
    input = [0, 1, 2, 3, 4, 5, 6]
    result = TakeAround(1, 5)(input)
    assert result == Success(([6], [1, 2, 3, 4, 5]))


def test_TakeAround_list_int_sequence_delimiters():
    input = [10, 20, 30, 40, 50, 60]
    result = TakeAround([20, 30], [50, 60])(input)
    assert result == Success(([], [20, 30, 40, 50, 60]))


def test_TakeAround_list_int_callable_delimiters():
    input = [10, 11, 12, 13, 14, 15]
    result = TakeAround(lambda x: x % 2 == 0, lambda x: x % 5 == 0)(input)
    # Start at 10 (even), end at 15 (divisible by 5)
    assert result == Success(([], [10, 11, 12, 13, 14, 15]))


###############################################################################
# Edge cases
###############################################################################
def test_TakeAround_start_and_end_same_nothing_between():
    input = "prefix()suffix"
    result = TakeAround("(", ")")(input)
    assert result == Success(("suffix", "()"))

def test_TakeAround_start_and_end_same_delimiter():
    input = "aaa"
    result = TakeAround("a", "a")(input)
    # Matches first "a" as start and second "a" as end
    assert result == Success(("a", "aa"))


def test_TakeAround_start_at_beginning():
    input = "(abc) trailing"
    result = TakeAround("(", ")")(input)
    assert result == Success((" trailing", "(abc)"))


def test_TakeAround_end_at_end():
    input = "prefix [middle]"
    result = TakeAround("[", "]")(input)
    assert result == Success(("", "[middle]"))
