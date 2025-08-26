from collections.abc import Sequence
from typing import final

from returns.result import Failure, Success

from parsepy import Parser, ParseResult


@final
class TakeN[T](Parser[T]):
    """`TakeN`.

    The parser will return the first N input elements. N can be negative
    and will take until N elements from the end of the input.

    Fails if the input is shorter than N.

    Examples
    --------
    ```python
    from returns.result import Failure, Success
    from parsepy.basic_elements import TakeN

    ###########################################################################
    # Succeeds with str
    input = "Hello, world"
    result = TakeN(5)(input)
    assert result == Success((", world", "Hello"))


    ###########################################################################
    # Succeeds with list[int]
    input = [1, 2, 3, 4, 5]
    result = TakeN(3)(input)
    assert result == Success(([4, 5], [1, 2, 3]))


    ###########################################################################
    # Succeeds with str with negative N
    input = "abcdef"
    result = TakeN(-3)(input)
    assert result == Success(("def", "abc"))


    ###########################################################################
    # Succeeds with list[int] with negative N
    input = [1, 2, 3, 4, 5]
    result = TakeN(-2)(input)
    assert result == Success(([4, 5], [1, 2, 3]))


    ###########################################################################
    # Fails with N > len(input)
    input = "Hi"
    result = TakeN(5)(input)
    assert isinstance(result, Failure)
    ```
    """

    # def __new__[T](cls, n: int) -> ParserLike[Sequence[T], Sequence[T]]:
    #     return super().__new__(cls)

    #
    def __init__(self, n: int) -> None:
        """`TakeN`.

        The parser will return the first N input elements. N can be
        negative and will take until N elements from the end of the
        input.

        Fails if the input is shorter than N.
        """
        self.n = n

    # def __call__[T](self, input: Sequence[T]) -> ParseResult[Sequence[T], Sequence[T]]:
    #     return self.parse(input)
    def __call__[T](self, input: T) -> ParseResult[T, T]:
        return self.parse(input)

    def parse[T](
        self,
        input: Sequence[T],
    ) -> ParseResult[Sequence[T], Sequence[T]]:
        if len(input) < abs(self.n):
            return Failure(f"Can't take N={self.n} from string of length={len(input)}.")
        rest = input[self.n :]
        taken = input[: self.n]
        return Success((rest, taken))
