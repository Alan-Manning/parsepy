from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Protocol, TypeAlias, TypeVar

from returns.result import Result

T = TypeVar("T")

Taken = TypeVar("Taken", covariant=True)
"""The type of the taken / parsed part of the input."""

ParseResult: TypeAlias = Result[tuple[T, Taken], str]
"""The result from a parser:

    - `Success( (rest, taken) )` when parsing succeeds where `rest` is the remaining input and `taken` is the consumed input.
    - `Failure( error_message )` when parsing fails, where `error_message` is the str explaining the error.
    """

T_contra = TypeVar("T_contra", contravariant=True)


class ParserLike(Protocol[T_contra, Taken]):
    """A Parser or something that takes an input and returns a Result with a
    tuple of rest and taken or error str. This is any subclass of `Parser` or a
    custom Callable. This Callable can transform the taken input but rest
    should remain the same type as the input.

    Examples
    --------
    ```python
    from collections.abc import Sequence
    from returns.result import Failure, Success
    from parsepy import ParseResult

    # maintain taken type.
    def my_parser(input: Sequence[int]) -> ParseResult[Sequence[int], Sequence[int]]:
        if input[1] > 10:
            rest = input[1:]
            taken = input[:1]
            return Success((rest, taken))
        return Failure("The second number wasnt bigger than 10!")
    ```

    ```python
    from collections.abc import Sequence
    from returns.result import Failure, Success
    from parsepy import ParseResult

    # transform taken chars form str.
    def sum_start_numbers(input: Sequence[str]) -> ParseResult[Sequence[str], int]:
        '''Take the start numbers from string and sum them together.'''
        result = TakeWhile(lambda x: x.isdigit())(input)
        match result:
            case Success((rest, taken)):
                nums_summed = sum([int(x) for x in taken])
                return Success((rest, nums_summed))
            case Failure(error_msg):
                return Failure(error_msg)
    ```
    """

    def __call__(self, input: T_contra) -> ParseResult[T_contra, Taken]: ...


class Parser[I](ABC):
    # def __new__(cls, *args, **kwargs) -> ParserLike[Sequence[I], Sequence[I]]:
    #     return super().__new__(*args, **kwargs)

    @abstractmethod
    def parse(
        self,
        input: Sequence[I],
    ) -> ParseResult[Sequence[I], Sequence[I]]: ...

    def __call__(self, input: Sequence[I]) -> ParseResult[Sequence[I], Sequence[I]]:
        if not isinstance(input, Result):
            return self.parse(input)
        else:
            raise ValueError(
                f"input should be of form `Sequence[T]` but got ParseResult: `{input}`"
            )


class MultiParser[T, Taken](ABC):
    """Most general parser base: Sequence[T] → ParseResult[Sequence[T], Taken]."""

    @abstractmethod
    def parse(
        self,
        input: Sequence[T],
    ) -> ParseResult[Sequence[T], Taken]: ...

    def __call__(self, input: Sequence[T]) -> ParseResult[Sequence[T], Taken]:
        if not isinstance(input, Result):
            return self.parse(input)
        else:
            raise ValueError(
                f"input should be of form `Sequence[T]` but got ParseResult: `{input}`"
            )
