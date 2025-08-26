from collections.abc import Callable, Sequence
from inspect import signature
from typing import final

from returns.result import Failure, Success

from parsepy import Parser, ParseResult


@final
class TakeUntil[T](Parser[T]):
    """`TakeUntil`.

    The parser will return the longest slice until the condition is matched.
    This will not include the condition itself in the taken Sequence.
    This is similar to TakeInclude but TakeUntil won't include the condition.

    - If the condition is a single element of type T, the parser succeeds when
    it finds that element in the input. i.e. input[i] == condition.

    - If the condition is a Sequence[T], the parser checks the input with a
    rolling window of size len(condition). The parser succeeds when
    input[i: i + len(condition)] == condition.

    - If the condition is a Callable, it must be a function that accepts one
    or more arguments of type T and returns a bool. The parser will slide a
    rolling window over the input, where the window size is determined by the
    number of parameters the Callable accepts. If the Callable returns True
    for any window, parsing succeeds at that position.

    By default fail_on_no_match=True means the parser fails when no match is
    found. Otherwise, it consumes the entire input.

    Examples
    --------

    ```python
    from returns.result import Failure, Success
    from parsepy.basic_elements import TakeUntil

    ###########################################################################
    # Succeeds with str
    input = "Hello, world"
    result = TakeUntil(",")(input)
    assert result == Success((", world", "Hello"))


    ###########################################################################
    # Succeeds with str with fail_on_no_match specified
    input = "Hello world"
    result = TakeUntil(",", fail_on_no_match=False)(input)
    assert result == Success(("", "Hello world"))


    ###########################################################################
    # Succeeds with list[int]
    input = [1, 2, 3, 4, 5]
    result = TakeUntil(3)(input)
    assert result == Success(([3, 4, 5], [1, 2]))


    ###########################################################################
    # Succeeds with Sequence[str] condition
    input = "abc123xyz"
    result = TakeUntil("123")(input)
    assert result == Success(("123xyz", "abc"))


    ###########################################################################
    # Succeeds with function condition on str
    input = "Hello123"
    result = TakeUntil(lambda x: x.isnumeric())(input)
    assert result == Success(("123", "Hello"))


    ###########################################################################
    # Succeeds with function condition on list[int]
    input = [1, 2, 3, 4, 5]
    result = TakeUntil(lambda x: x > 3)(input)
    assert result == Success(([4, 5], [1, 2, 3]))


    ###########################################################################
    # Succeeds with multi arg function condition on list[int]
    input = [1, 2, 3, 4, 5]
    result = TakeUntil(lambda x, y: x + y > 6)(input)
    assert result == Success(([3, 4, 5], [1, 2]))
    ```
    """

    def __init__(
        self,
        condition: T | Sequence[T] | Callable[[*tuple[T, ...]], bool],
        fail_on_no_match: bool = True,
    ) -> None:
        """TakeUntil`.

        The parser will return the longest slice until the condition is matched.
        This will not include the condition itself in the taken Sequence.
        This is similar to TakeInclude but TakeUntil won't include the condition.

        - If the condition is a single element of type T, the parser succeeds when
        it finds that element in the input. i.e. input[i] == condition.

        - If the condition is a Sequence[T], the parser checks the input with a
        rolling window of size len(condition). The parser succeeds when
        input[i: i + len(condition)] == condition.

        - If the condition is a Callable, it must be a function that accepts one
        or more arguments of type T and returns a bool. The parser will slide a
        rolling window over the input, where the window size is determined by the
        number of parameters the Callable accepts. If the Callable returns True
        for any window, parsing succeeds at that position.

        By default fail_on_no_match=True means the parser fails when no match is
        found. Otherwise, it consumes the entire input.
        """

        self.condition_function: Callable[[*tuple[T, ...]], bool] | None = None
        self.condition_match: None | T | Sequence[T] = None

        if isinstance(condition, Callable):
            self.condition_function = condition
        else:
            self.condition_match = condition
        self.fail_on_no_match = fail_on_no_match

    @classmethod
    def _parse_condition_match(
        cls,
        input: Sequence[T],
        condition_match: T | Sequence[T],
        fail_on_no_match: bool = True,
    ) -> ParseResult[Sequence[T], Sequence[T]]:
        """Parses for input[x, ...] == condition_match."""
        # str types of a single char has a length of one but is still
        # considered a Sequence. This try catch get the correct chunk size.
        try:
            chunk_size = len(condition_match)
        except TypeError:
            chunk_size = 1
        for i in range(len(input)):
            if chunk_size == 1:
                input_chunk = input[i]
            else:
                input_chunk = input[i : i + chunk_size]
            if condition_match == input_chunk:
                rest = input[i:]
                taken = input[:i]
                return Success((rest, taken))
        if fail_on_no_match:
            return Failure(f"Could not find condition=`{condition_match}` in input.")
        return Success((input[len(input) :], input))

    @classmethod
    def _parse_condition_function(
        cls,
        input: Sequence[T],
        condition_function: Callable[[*tuple[T, ...]], bool],
        fail_on_no_match: bool = True,
    ) -> ParseResult[Sequence[T], Sequence[T]]:
        chunk_size = len(signature(condition_function).parameters)
        range_stop = len(input) - chunk_size + 1
        for i in range(range_stop):
            if condition_function(*input[i : i + chunk_size]):
                rest = input[i:]
                taken = input[:i]
                return Success((rest, taken))

        if fail_on_no_match:
            return Failure(
                f"Could not find where condition=`{condition_function.__name__}` evaluated to True."
            )
        return Success((input[len(input) :], input))

    def parse(
        self,
        input: Sequence[T],
    ) -> ParseResult[Sequence[T], Sequence[T]]:
        if self.condition_match is not None:
            return self._parse_condition_match(
                input,
                self.condition_match,
                self.fail_on_no_match,
            )
        if self.condition_function is not None:
            return self._parse_condition_function(
                input,
                self.condition_function,
                self.fail_on_no_match,
            )
        raise RuntimeError("This should never happen.")
