# parsepy

A **Python parser combinator library** inspired by Rust’s excellent [nom](https://github.com/rust-bakery/nom).

It provides a composable way to build parsers for structured data in a **functional style**, with a strong focus on clarity, testability, and reuse.

---

## Features

- Small, composable building blocks for parsing (`take_until`, `take_while`, etc.)
- Combinators for sequencing and branching (`all_of`, `one_of`, `permutation_of`)
- Sequence-based parsers (`take_between`, `take_around`) for extracting delimited text
- Extensible: build your own parsers easily by writing a `ParserLike` Callable or by subclassing `Parser`
- Typed, with results returned as [`Success`](https://returns.readthedocs.io/en/latest/pages/result.html#success) or [`Failure`](https://returns.readthedocs.io/en/latest/pages/result.html#failure) from [`returns.result`](https://github.com/dry-python/returns)

---

### Use of the [returns](https://github.com/dry-python/returns) package?

`parsepy` builds on top of the [`returns`](https://github.com/dry-python/returns) package to model parser results in a safe and expressive way.  
Every parser returns a `ParseResult`, which is just an alias around `returns.result.Result`:

- **`Success((rest, taken))`** → the parser consumed part of the input and produced a `taken` value, leaving the remaining `rest`.
- **`Failure(error_msg)`** → the parser failed with a human-readable error message.

This eliminates the need for `None` checks or exceptions during parsing and provides usefull error messages during failures. Results are also more composable in parsers like `OneOf`.

---

## Installation

```bash
not on pip yet. But it would be:
pip install parsepy
```

---

## Issues

I have tested a lot but errors probably exists so just create an issue and i can have a look.
or im very open to PRs.

---

## Project Layout

```
parsepy
│  basic_elements
│ │ │ TakeInclude
│ │ │ TakeN
│ │ │ TakeUntil
│ │ └ TakeWhile
│ choice_combinators
│ │ │ AllOf
│ │ │ OneOf
│ │ └ PermutationOf
│ sequence_combinators
│ │ │ TakeAround
│ │ └ TakeBetween
```

---

## Docs

I havent yet made any docs but everyting that could be described in docs is in docstring of these parsers. This includes some tests showing how the parser works by example. If you need more clarification hop into the tests folder and there are more examples of how to use a specific parser.

---

## License

This project is licensed under the **GNU General Public License v3.0 (GPLv3)**.

## Quick Examples

### Parse between delimiters

```python
from returns.result import Success
from parsepy.sequence_combinators import TakeBetween

input = "Hello Bob (the best Bob). Welcome."
result = TakeAround("(", ")")(input)

assert result == Success((". Welcome.", "(the best Bob)"))

rest, taken = result.unwrap()

# rest is the rest of the input not comsumed
# taken is the part of the input comsumed

assert rest = ". Welcome."
assert taken = "(the best Bob)"


```

### Choose between parsers

```python
from returns.result import Success
from parsepy.choice_combinators import OneOf
from parsepy.basic_elements import TakeWhile

digits = TakeWhile(lambda x: x.isdigit())
letters = TakeWhile(lambda x: x.isalpha())

parser = OneOf(digits, letters)

assert parser("123abc") == Success(("abc", "123"))
assert parser("abc123") == Success(("123", "abc"))
```

### Combining parsers

```python
from returns.result import Success
from parsepy.choice_combinators import PermutationOf
from parsepy.basic_elements import TakeWhile

digits = TakeWhile(lambda x: x.isdigit())
letters = TakeWhile(lambda x: x.isalpha())

parser = PermutationOf(digits, letters)

assert parser("123abc") == Success(("", ("123", "abc")))
assert parser("abc123") == Success(("", ("abc", "123")))
```

---

## Custom Parsers

In addition to using the built-in parsers and combinators, you can also define your own **custom parsers**.  
A parser is simply a callable that accepts an input sequence and returns a `ParseResult`.

Custom parsers can be defined as **classes** (subclassing `Parser`) or just as **plain functions**.

### Example: Parser as a Function

```python
from returns.result import Failure, Success
from parsepy import ParseResult

def starts_with_a(input: str) -> ParseResult[str, str]:
    """Succeeds when the first letter = `"a"`."""
    if input and input[0] == "a":
        return Success((input[1:], input[:1]))
    return Failure("not starting with a")
```

#### Usage:

```python
assert starts_with_a("apple") == Success(("pple", "a"))
assert starts_with_a("banana").failure() == "not starting with a"
```

### Example: Combining Built-in Parsers into a Function

```python
from returns.result import Failure, Success
from parsepy.basic_elements import TakeWhile
from parsepy import ParseResult

def sum_start_numbers(input: str) -> ParseResult[str, int]:
    """Take the start numbers from string and sum them together."""
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
```

#### Usage:

```python
assert sum_start_numbers("123abc") == Success(("abc", 6))
assert sum_start_numbers("no-digits").failure() == "no numbers at start"
```

### Example: Parser as a class

```python
class TakeNumbersfromStr(Parser[str]):
    """Take the numbers from the start of a string."""

    def parse(input: str) -> ParseResult[str, str]:
        for i in range(len(input)):
            if condition_match != input[i]:
                rest = input[i:]
                taken = input[:i]

        if len(taken) > 0:
            return Success((rest, taken))
        else:
            return Failure("no numbers at start")
```

#### Usage:

```python
assert TakeNumbersfromStr()("123abc") == Success(("abc", 6))
assert TakeNumbersfromStr()("no-digits") == Failure("no numbers at start")
```

### Example: Another parser as a class

```python
from returns.result import Success, Failure
from parsepy import Parser, ParseResult

class TakeUppercase(Parser[str]):
    """Take uppercase letters from start of string."""
    def __init__(
        allow_number_for_some_reason: bool = False,
    ) -> None:
        self.allow_number_for_some_reason = allow_number_for_some_reason

    def parse(self, input: str) -> ParseResult[str, str]:
        if input[0].isupper():
            return Success((input[1:], input[0]))
        elif self.allow_number_for_some_reason:
            return Success((input[1:], input[0]))

        return Failure("Expected uppercase letter")
```

#### Usage:

```python

assert TakeUppercase()("Bob") == Success(("ob", "B"))
assert TakeUppercase()("1bob") == Failure("Expected uppercase letter")
assert TakeUppercase(allow_number_for_some_reason=True)("1bob") == Success(("bob", "1")
```

## Fuller Example: [Advent of Code 2024 Day 1](https://adventofcode.com/2024/day/1)

```python

from parsepy import ParseResult
from parsepy.basic_elements import TakeWhile, TakeUntil, TakeInclude
from returns.result import Success, Failure


###############################################################################
# Advent of code 2024 day 1 part 1 test input
###############################################################################
TEST_INPUT = """3   4
4   3
2   5
1   3
3   9
3   3
"""
# This is equivilant to: test_input = '3   4\n4   3\n2   5\n1   3\n3   9\n3   3\n'

PART_1_CORRECT_ANSWER = 11
PART_2_CORRECT_ANSWER = 31

###############################################################################
# Line parsing
###############################################################################


def get_line(input: str) -> ParseResult[str, str]:
    """Get the left number chars, space chars, and right number chars untill a
    new line escape char.

    The line does not include this new line escape char.
    """
    match TakeInclude("\n")(input):
        case Success((rest, taken)):
            _, taken = TakeUntil("\n")(taken).unwrap()
            return Success((rest, taken))
        case Failure(err_msg):
            return Failure(err_msg)


def get_lines(input: str) -> ParseResult[str, list[str]]:
    """Get all the lines from the input."""
    more_lines = True

    lines: list[str] = []
    rest = input

    while more_lines:
        result = get_line(rest)
        match result:
            case Success((rest, line)):
                lines.append(line)
            case Failure(_):
                more_lines = False
                break

    return Success((rest, lines))


###############################################################################
# Nubmers parsing
###############################################################################


def get_number(input: str) -> ParseResult[str, int]:
    """Get the number from input."""
    match TakeWhile(lambda x: x.isnumeric())(input):
        case Success((rest, left_num_str)):
            return Success((rest, int(left_num_str)))
        case Failure(_):
            return Failure("Couldn't find number!")


def get_left_right_list_nos_from_line(line: str) -> ParseResult[str, tuple[int, int]]:
    """Get the left number and right number from a line."""
    match get_number(line):
        case Success((rest, left_num)):
            pass
        case Failure(_):
            return Failure(f"Couldn't find left number in line: `{line}` ")

    match TakeUntil(lambda x: x.isnumeric())(rest):
        case Success((rest, _)):
            pass
        case Failure(_):
            return Failure(f"Couldn't find right number in line: `{line}` ")

    match get_number(rest):
        case Success((_, right_num)):
            return Success((left_num, right_num))
        case Failure(_):
            return Failure(f"Couldn't find right number in line: `{line}` ")


def get_all_left_right_numbers(lines: list[str]) -> tuple[list[int], list[int]]:
    """Get all the left numbers and all the right numbers as lists of ints."""
    left_numbers: list[int] = []
    right_numbers: list[int] = []

    for line in lines:
        match get_left_right_list_nos_from_line(line):
            case Success((left_num, right_num)):
                left_numbers.append(left_num)
                right_numbers.append(right_num)
            case Failure(err_msg):
                raise RuntimeError(err_msg)
    return (left_numbers, right_numbers)


###############################################################################
# Solving
###############################################################################


def solve_part_1(input: str) -> int:
    _, lines = get_lines(input).unwrap()

    left_numbers, right_numbers = get_all_left_right_numbers(lines)

    left_numbers.sort()
    right_numbers.sort()

    running_diff = 0

    for left_no, right_no in zip(left_numbers, right_numbers):
        running_diff += abs(left_no - right_no)

    return running_diff


def solve_part_2(input: str) -> int:
    _, lines = get_lines(input).unwrap()

    left_numbers, right_numbers = get_all_left_right_numbers(lines)

    running_similarity_score = 0

    for left_no in left_numbers:
        no_of_occurrences_in_right = right_numbers.count(left_no)
        similarity_score = left_no * no_of_occurrences_in_right
        running_similarity_score += similarity_score

    return running_similarity_score


if __name__ == "__main__":
    part_1_answer = solve_part_1(TEST_INPUT)
    assert part_1_answer == PART_1_CORRECT_ANSWER

    part_2_answer = solve_part_2(TEST_INPUT)
    assert part_2_answer == PART_2_CORRECT_ANSWER


def test_AOC_day_1_part_1():
    part_1_answer = solve_part_1(TEST_INPUT)
    assert part_1_answer == PART_1_CORRECT_ANSWER


def test_AOC_day_1_part_2():
    part_2_answer = solve_part_2(TEST_INPUT)
    assert part_2_answer == PART_2_CORRECT_ANSWER
```
