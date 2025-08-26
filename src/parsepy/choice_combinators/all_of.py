from collections.abc import Sequence
from typing import (
    Any,
    TypeVar,
    final,
    overload,
)

from returns.result import Failure, Result, Success

from parsepy import ParseResult, ParserLike

T = TypeVar("T")
Taken1 = TypeVar("Taken1")
Taken2 = TypeVar("Taken2")
Taken3 = TypeVar("Taken3")
Taken4 = TypeVar("Taken4")
Taken5 = TypeVar("Taken5")
InputSequence = TypeVar("InputSequence")


@final
class _AllOf:
    def __init__(self, parsers):
        self.parsers = parsers

    def __call__(
        self,
        input: Sequence[T],
    ) -> ParseResult[tuple[Sequence[T], tuple[Any, ...]], str]:
        if isinstance(input, Result):
            raise ValueError(
                f"input should be of form `Sequence[T]` but got ParseResult: `{input}`"
            )
        rest = input
        taken_list = []

        for i, parser in enumerate(self.parsers):
            result = parser(rest)
            match result:
                case Success((new_rest, taken)):
                    rest = new_rest
                    taken_list.append(taken)
                case Failure(error_msg):
                    return Failure(
                        f"AllOf failed because parser {i} failed with error: {error_msg}"
                    )

        return Success((rest, tuple(taken_list)))


@final
class AllOf[InputSequence]:
    """`AllOf`.

    AllOf applies multiple parsers one after another on the same input. Each
    parser consumes from the remaining input produced by the previous one.
    Parsing only succeeds when all the given parsers succeed.

    The result is a tuple of all the "taken" values from each parser in order,
    paired with the final remainder of the input after the last parser.

    - If any parser fails, `AllOf` fails immediately and wraps the error in a
    `Failure`, indicating which parser index failed and why.

    - If all parsers succeed, `AllOf` returns a `Success` containing a tuple
    `(rest, (taken1, taken2, ...))`.

    This is similar to `PermutationOf`, except `PermutationOf` does not enforce
    a fixed sequence, while `AllOf` is order-dependent.

    Examples
    --------
    ```python
    from collections.abc import Sequence
    from typing import Any, Never

    from returns.result import Failure, Success

    from parsepy import ParseResult
    from parsepy.choice_combinators import AllOf
    from parsepy.basic_elements import TakeN, TakeInclude

    ###########################################################################
    # Succeeds when using simple parser.

    input = "abcdef"
    # TakeN(1) x5 -> consumes one char each time
    result = AllOf(TakeN(1), TakeN(1), TakeN(1), TakeN(1), TakeN(1))(input)
    assert result == Success(("f", ("a", "b", "c", "d", "e")))


    ###########################################################################
    # Succeeds when using function condition and simple parser.

    input = [1, 2, 3, 4, 5]
    parser = AllOf(TakeInclude(lambda x: x == 3), TakeN(1))
    # TakeInclude(x==3) -> ([4,5], [1,2,3])
    # Then TakeN(1) -> ([5], [4])
    result = parser(input)
    assert result == Success(([5], ([1, 2, 3], [4])))


    ###########################################################################
    # Fails when any parser fails.

    def always_fail[T](input: Sequence[T]) -> ParseResult[Never, Never]:
        '''Will always fail with err msg `nope`.'''
        return Failure("nope")

    input = "hello"
    result = AllOf(TakeN(1), always_fail, TakeN(1))(input)
    assert isinstance(result, Failure)
    assert result.failure() == "AllOf failed because parser 1 failed with error: nope"
    ```
    """

    @overload
    def __new__(
        cls,
        p1: ParserLike[InputSequence, Taken1],
    ) -> ParserLike[InputSequence, tuple[Taken1]]: ...

    @overload
    def __new__(
        cls,
        p1: ParserLike[InputSequence, Taken1],
        p2: ParserLike[InputSequence, Taken2],
    ) -> ParserLike[InputSequence, tuple[Taken1, Taken2]]: ...

    @overload
    def __new__(
        cls,
        p1: ParserLike[InputSequence, Taken1],
        p2: ParserLike[InputSequence, Taken2],
        p3: ParserLike[InputSequence, Taken3],
    ) -> ParserLike[InputSequence, tuple[Taken1, Taken2, Taken3]]: ...

    @overload
    def __new__(
        cls,
        p1: ParserLike[InputSequence, Taken1],
        p2: ParserLike[InputSequence, Taken2],
        p3: ParserLike[InputSequence, Taken3],
        p4: ParserLike[InputSequence, Taken4],
    ) -> ParserLike[InputSequence, tuple[Taken1, Taken2, Taken3, Taken4]]: ...

    @overload
    def __new__(
        cls,
        p1: ParserLike[InputSequence, Taken1],
        p2: ParserLike[InputSequence, Taken2],
        p3: ParserLike[InputSequence, Taken3],
        p4: ParserLike[InputSequence, Taken4],
        p5: ParserLike[InputSequence, Taken5],
    ) -> ParserLike[InputSequence, tuple[Taken1, Taken2, Taken3, Taken4, Taken5]]: ...

    @overload
    def __new__(
        cls,
        *other_parsers: ParserLike[InputSequence, Any],
    ) -> ParserLike[InputSequence, tuple[Any]]: ...

    def __new__(cls, *parsers):
        return _AllOf(parsers)


# from parsepy.basic_elements import TakeN, TakeUntil
#
# parser = AllOf(TakeN(3), TakeN(3))
# res = parser("lsakjdf;lsakjf")
#
# parser = AllOf(TakeUntil("h"), TakeUntil("h"))
# rest = parser("lsakjdf;lsakjf")
#
# parser = AllOf(TakeUntil(["h"]), TakeUntil(["i"]))
# rest = parser(["h", "i", " ", "t", "h", "e", "r", "e"])
#
# parser = AllOf(TakeUntil(2), TakeUntil(2))
# rest = parser([1,2,3,1,2,3])
