from collections.abc import Callable, Sequence
from inspect import signature
from typing import final

from returns.result import Success

from parsepy import Parser, ParseResult


@final
class TakeWhile[T](Parser[T]):
    """`TakeWhile`.

    The parser will return the longest slice that until the condition no longer
    matches or until the condition evaluates to False.
    This will not include the condition itself in the taken Sequence.

    - If the condition is a single element of type T, the parser succeeds until
    it fails to find that element in the input. i.e. input[i] != condition.

    - If the condition is a Sequence[T], the parser checks the input in chunks
    of size len(condition). The parser succeeds untill
    input[i: i + len(condition)] != condition.

    - If the condition is a Callable, it must be a function that accepts one
    or more arguments of type T and returns a bool. The parser will slide a
    rolling window over the input, where the window size is determined by the
    number of parameters the Callable accepts. Parsing succeeds untill the
    Callable returns False for any window.

    The parser succeeds even if the condition is immediately not matched or
    evaluates to False.

    Examples
    --------
    ```python
    from returns.result import Success
    from parsepy.basic_elements import TakeWhile

    ###########################################################################
    # Succeeds with str
    input = "aaaa"
    result = TakeWhile("a")(input)
    assert result == Success(("", "aaaa"))


    ###########################################################################
    # Succeeds with list[int]
    input = [1, 1, 1, 2, 3]
    result = TakeWhile(1)(input)
    assert result == Success(([2, 3], [1, 1, 1]))


    ###########################################################################
    # Succeeds with Sequence[str] condition
    input = "aaabbb"
    result = TakeWhile("aa")(input)
    assert result == Success(("abbb", "aa"))


    ###########################################################################
    # Succeeds with function condition on list[int]
    input = [1, 2, 3]
    result = TakeWhile(lambda x: x < 5)(input)
    assert result == Success(([], [1, 2, 3]))


    ###########################################################################
    # Succeeds with multi arg function condition on list[int]
    input = [1, 2, 3, 4, 5, 1, 2, 3]
    result = TakeWhile(lambda x, y: x < y)(input)
    assert result == Success(([1, 2, 3], [1, 2, 3, 4, 5]))
    ```
    """

    def __init__(
        self,
        condition: T | Sequence[T] | Callable[[*tuple[T, ...]], bool],
    ) -> None:
        """`TakeWhile`.

        The parser will return the longest slice that until the condition no longer
        matches or until the condition evaluates to False.
        This will not include the condition itself in the taken Sequence.

        - If the condition is a single element of type T, the parser succeeds until
        it fails to find that element in the input. i.e. input[i] != condition.

        - If the condition is a Sequence[T], the parser checks the input in chunks
        of size len(condition). The parser succeeds untill
        input[i: i + len(condition)] != condition.

        - If the condition is a Callable, it must be a function that accepts one
        or more arguments of type T and returns a bool. The parser will slide a
        rolling window over the input, where the window size is determined by the
        number of parameters the Callable accepts. Parsing succeeds untill the
        Callable returns False for any window.

        The parser succeeds even if the condition is immediately not matched or
        evaluates to False.
        """
        if isinstance(condition, Callable):
            self.condition_function: Callable[[*tuple[T, ...]], bool] | None = condition
            self.condition_match: None | T | Sequence[T] = None
        else:
            self.condition_function: Callable[[*tuple[T, ...]], bool] | None = None
            self.condition_match: T | Sequence[T] | None = condition

    @classmethod
    def _parse_condition_match[T](
        cls,
        input: Sequence[T],
        condition_match: T | Sequence[T],
    ) -> ParseResult[Sequence[T], Sequence[T]]:
        # str types of a single char has a length of one but is still
        # considered a Sequence. This try catch get the correct chunk size.
        try:
            chunk_size = len(condition_match)
        except TypeError:
            chunk_size = 1
        for i in range(0, len(input), chunk_size):
            if chunk_size == 1:
                input_chunk = input[i]
            else:
                input_chunk = input[i : i + chunk_size]
            if condition_match != input_chunk:
                rest = input[i:]
                taken = input[:i]
                return Success((rest, taken))

        return Success((input[len(input) :], input))

    @classmethod
    def _parse_condition_function(
        cls,
        input: Sequence[T],
        condition_function: Callable[[*tuple[T, ...]], bool],
    ) -> ParseResult[Sequence[T], Sequence[T]]:
        chunk_size = len(signature(condition_function).parameters)
        range_stop = len(input) - chunk_size + 1
        for i in range(range_stop):
            if not condition_function(*input[i : i + chunk_size]):
                if i == 0:
                    rest = input[0:]
                    taken = input[:0]
                    return Success((rest, taken))
                rest = input[i + chunk_size - 1 :]
                taken = input[: i + chunk_size - 1]
                return Success((rest, taken))
        return Success((input[len(input) :], input))

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
