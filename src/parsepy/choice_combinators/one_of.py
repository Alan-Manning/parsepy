from collections.abc import Sequence
from typing import final

from returns.pipeline import is_successful
from returns.result import Failure

from parsepy import MultiParser, ParseResult, ParserLike


@final
class OneOf[T, Taken](MultiParser[T, Taken]):
    """`OneOf`.

    The parser will return the result of the first parser that succeeds.
    The parser fails if none of the parsers succeed.

    Examples
    --------
    ```python
    from collections.abc import Sequence
    from typing import Any, Never

    from parsepy import ParseResult
    from parsepy.basic_elements import TakeN
    from parsepy.choice_combinators import OneOf
    from returns.result import Success, Failure


    ###########################################################################
    # Succeeds when first parser succeeds.
    input = "abcd"
    result = OneOf(TakeN(2), TakeN(10))(input)
    assert result == Success(("cd", "ab"))


    ###########################################################################
    # Succeeds when first parser fails.
    input = "abcd"
    result = OneOf(lambda s: Failure("nope"), TakeN(2))(input)
    assert result == Success(("cd", "ab"))


    ###########################################################################
    # Fails when all parsers fail.

    def always_fail(input: Sequence[Any]) -> ParseResult[Never, Never]:
        '''Will always fail with err msg `nope`.'''
        return Failure("nope")

    input = "zzz"
    result = OneOf(always_fail, always_fail)(input)
    assert result == Failure("None or the parsers succeeded.")
    ```
    """

    def __init__(
        self,
        *parsers: ParserLike[T, Taken],
    ) -> None:
        """`OneOf`.

        The parser will return the result of the first parser that
        succeeds. The parser fails if none of the parsers succeed.
        """
        if not parsers:
            raise ValueError("OneOf must be initialized with at least one parser.")

        self.parsers: tuple[ParserLike[T, Taken], ...] = parsers

    def parse(
        self,
        input: Sequence[T],
    ) -> ParseResult[Sequence[T], Taken]:
        for parser in self.parsers:
            result = parser(input)
            if is_successful(result):
                return result
        return Failure("None or the parsers succeeded.")
