from collections.abc import Callable, Sequence
from inspect import signature
from typing import final

from returns.result import Failure, Success

from parsepy import Parser, ParseResult


@final
class TakeInclude[T](Parser[T]):
    """`TakeInclude`.

    The parser will return the longest slice until the condition is matched.
    This will include the condition itself in the taken Sequence.
    This is similar to TakeUntil but TakeInclude will include the condition.

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

    Fails if the condition is not found.


    Examples
    --------
    ```python
    from parsepy.basic_elements import TakeInclude
    from returns.result import Success, Failure

    ###########################################################################
    # Succeeds with str
    input = "Hello, world"
    result = TakeInclude(",")(input)
    assert result == Success((" world", "Hello,"))


    ###########################################################################
    # Fails with str
    input = "Hello world"
    result = TakeInclude(",")(input)
    assert isinstance(result, Failure)


    ###########################################################################
    # Succeeds with list[int]
    input = [1, 2, 3, 4, 5]
    result = TakeInclude(3)(input)
    assert result == Success(([4, 5], [1, 2, 3]))


    ###########################################################################
    # Succeeds with Sequence[str] condition
    input = "abc123xyz"
    result = TakeInclude("123")(input)
    assert result == Success(("xyz", "abc123"))


    ###########################################################################
    # Succeeds with function condition on str
    input = "Hello123"
    result = TakeInclude(lambda x: x.isnumeric())(input)
    assert result == Success(("23", "Hello1"))


    ###########################################################################
    # Succeeds with function condition on list[int]
    input = [1, 2, 3, 4, 5]
    result = TakeInclude(lambda x: x > 3)(input)
    assert result == Success(([5], [1, 2, 3, 4]))


    ###########################################################################
    # Succeeds with multi arg function condition on list[int]
    input = [1, 2, 3, 4, 5]
    result = TakeInclude(lambda x, y: x + y > 6)(input)
    assert result == Success(([5], [1, 2, 3, 4]))
    ```
    """

    def __init__(
        self,
        condition: T | Sequence[T] | Callable[[*tuple[T, ...]], bool],
    ) -> None:
        """`TakeInclude`.

        The parser will return the longest slice until the condition is matched.
        This will include the condition itself in the taken Sequence.
        This is similar to TakeUntil but TakeInclude will include the condition.

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

        Fails if the condition is not found.
        """
        if isinstance(condition, Callable):
            self.condition_function: Callable[[*tuple[T, ...]], bool] | None = condition
            self.condition_match: None | T | Sequence[T] = None
        else:
            self.condition_function: None | Callable[[*tuple[T, ...]], bool] = None
            self.condition_match: T | Sequence[T] | None = condition

    @classmethod
    def _parse_condition_match[T](
        cls,
        input: Sequence[T],
        condition_match: T | Sequence[T],
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
                rest = input[i + chunk_size :]
                taken = input[: i + chunk_size]
                return Success((rest, taken))
        return Failure(f"Could not find condition=`{condition_match}` in input.")

    @classmethod
    def _parse_condition_function(
        cls,
        input: Sequence[T],
        condition_function: Callable[[*tuple[T, ...]], bool],
    ) -> ParseResult[Sequence[T], Sequence[T]]:
        chunk_size = len(signature(condition_function).parameters)
        range_stop = len(input) - chunk_size + 1
        for i in range(range_stop):
            if condition_function(*input[i : i + chunk_size]):
                rest = input[i + chunk_size :]
                taken = input[: i + chunk_size]
                return Success((rest, taken))

        return Failure(
            f"Could not find where condition=`{condition_function.__name__}` evaluated to True."
        )

    def parse(
        self,
        input: Sequence[T],
    ) -> ParseResult[Sequence[T], Sequence[T]]:
        if self.condition_match is not None:
            return self._parse_condition_match(
                input,
                self.condition_match,
            )

        if self.condition_function is not None:
            return self._parse_condition_function(
                input,
                self.condition_function,
            )

        raise RuntimeError("This should never happen.")
