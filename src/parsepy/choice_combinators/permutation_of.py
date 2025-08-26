from collections.abc import Sequence
from typing import (
    Any,
    TypeVar,
    final,
    overload,
)

from returns.result import Failure, Result, Success

from parsepy.base_parser import ParseResult, ParserLike

T = TypeVar("T")
Taken1 = TypeVar("Taken1")
Taken2 = TypeVar("Taken2")
Taken3 = TypeVar("Taken3")
InputSequence = TypeVar("InputSequence")


@final
class _PermutationOf:
    def __init__(self, parsers):
        self.parsers = list(parsers)

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

        no_of_parsers = len(self.parsers)

        unsuccessfull_parser_nos_set: set[int] = set(range(no_of_parsers))
        successfull_parser_nos_set: set[int] = set()

        for _ in range(no_of_parsers):
            for i, parser in enumerate(self.parsers):
                if parser is None:
                    continue

                result = parser(rest)
                match result:
                    case Success((new_rest, taken)):
                        rest = new_rest
                        taken_list.append(taken)
                        self.parsers[i] = None
                        unsuccessfull_parser_nos_set.remove(i)
                        successfull_parser_nos_set.add(i)
                        break
                    case Failure(_):
                        continue

        if len(unsuccessfull_parser_nos_set) == 0:
            return Success((rest, tuple(taken_list)))

        if len(unsuccessfull_parser_nos_set) == 1:
            return Failure(
                f"PermutationOf failed because parser `{list(unsuccessfull_parser_nos_set)[0]}` never succeeded. The parsers `{list(successfull_parser_nos_set)}` all succeeded"
            )

        if len(unsuccessfull_parser_nos_set) > 1:
            error_msg = f"PermutationOf failed because parsers `{list(unsuccessfull_parser_nos_set)}` never succeeded."
            if len(successfull_parser_nos_set) == 1:
                error_msg += (
                    f" The parser `{list(successfull_parser_nos_set)[0]}` succeeded."
                )
            elif len(successfull_parser_nos_set) == 0:
                error_msg += " No parsers succeeded."
            else:
                error_msg += (
                    f" The parsers `{list(successfull_parser_nos_set)}` all succeeded."
                )

            return Failure(error_msg)


@final
class PermutationOf[InputSequence]:
    """`PermutationOf`.

    A parser combinator that applies multiple parsers on the same input, but
    allows them to succeed in any order. Each parser consumes from the
    remaining input produced by the previous one, and parsing only succeeds
    if all the given parsers succeed.

    The order of parsers still matters for priority only when more than one
    parser could match at the same position, the parser listed earlier is
    tried first and "claims" that part of the input. Subsequent parsers must
    then work with the remaining input.

    The result is a tuple of the "taken" values from each parser (in the order
    they succeeded), paired with the final remainder of the input after the
    last parser.

    - If all parsers succeed in some order, returns a `Success` with:
    `(rest, (taken1, taken2, ...))`.

    - If one parser never succeeds, returns a `Failure` with an error
    indicating which parser index failed.

    - If more than one parser never succeeds, returns a `Failure` listing all
    failing parser indices.

    This is similar to `AllOf`, except `AllOf` enforces a fixed sequence,
    while `PermutationOf` is order-independent.

    Examples
    --------
    ```python
    from returns.result import Failure, Success

    from parsepy import ParseResult
    from parsepy.choice_combinators import PermutationOf, OneOf
    from parsepy.basic_elements import TakeN, TakeWhile, TakeUntil, TakeInclude

    ###########################################################################
    # Succeeds with 2 simple parsers

    input = "123abc"
    # TakeN(3) can run first or second, doesn't matter
    result = PermutationOf(TakeN(3), TakeN(3))(input)
    assert result == Success(("", ("123", "abc")))


    ###########################################################################
    # Succeeds with combining with OneOf

    input = "abcdef"
    parser = PermutationOf(OneOf(TakeN(2), TakeN(3)), TakeN(2))
    # OneOf(TakeN(2), TakeN(3)) succeeds on TakeN(2) leaving TakeN(2)
    result = parser(input)
    assert isinstance(result, Success)
    rest, taken = result.unwrap()
    assert rest == "ef"
    assert taken == ("ab", "cd")


    ###########################################################################
    # Succeeds with in one order but not another showing order still matters.

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

    input = "abc123xyz"
    parser = PermutationOf(
        sum_start_numbers,
        TakeN(3),
        TakeUntil("z"),
    )
    # succeeds with order TakeN(3) -> sum_start_numbers -> TakeUntil("z")
    result = parser(input)
    assert result == Success(("z", ("abc", 6, "xy")))

    parser_order_changed = PermutationOf(
        TakeUntil("z"),
        sum_start_numbers,
        TakeN(3),
    )
    # fails becuase TakeUntil("z") succeeds then the other 2 fail because of this.
    result_rev = parser_order_changed(input)
    assert result_rev == Failure(
        "PermutationOf failed because parsers `[1, 2]` never succeeded. The parser `0` succeeded."
    )


    ###########################################################################
    # Succeeds when ordering does not matter.

    def first_gt_10(input: list[int]) -> ParseResult[list[int], list[int]]:
        if input and input[0] > 10:
            return Success((input[1:], [input[0]]))
        return Failure("first <= 10")

    input = [5, 6, 11, 12]
    parser = PermutationOf(
        first_gt_10,
        TakeN(2),
    )
    # succeeds with order TakeN(2) -> first_gt_10
    result = parser(input)
    assert result == Success(([12], ([5, 6], [11])))

    # Reverse order
    parser_rev = PermutationOf(
        TakeN(2),
        first_gt_10,
    )
    # succeeds with order TakeN(2) -> first_gt_10
    result_rev = parser_rev(input)
    assert result_rev == Success(([12], ([5, 6], [11])))


    ###########################################################################
    # Fails when any parser fails.

    input = "abc123"
    parser = PermutationOf(sum_start_numbers, TakeInclude("zzz"))
    # sum_start_numbers fails and take_include fails no matter the order
    result = parser(input)
    assert isinstance(result, Failure)
    assert result == Failure(
        "PermutationOf failed because parsers `[0, 1]` never succeeded. No parsers succeeded."
    )
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
    ) -> ParserLike[InputSequence, tuple[Taken1, Taken2] | tuple[Taken2, Taken1]]: ...

    @overload
    def __new__(
        cls,
        p1: ParserLike[InputSequence, Taken1],
        p2: ParserLike[InputSequence, Taken2],
        p3: ParserLike[InputSequence, Taken3],
    ) -> ParserLike[
        InputSequence,
        tuple[Taken1, Taken2, Taken3]
        | tuple[Taken1, Taken3, Taken2]
        | tuple[Taken2, Taken1, Taken3]
        | tuple[Taken2, Taken3, Taken1]
        | tuple[Taken3, Taken1, Taken2]
        | tuple[Taken3, Taken2, Taken1],
    ]: ...

    @overload
    def __new__(
        cls,
        *other_parsers: ParserLike[InputSequence, Any],
    ) -> ParserLike[InputSequence, tuple[Any]]: ...

    def __new__(cls, *parsers):
        return _PermutationOf(parsers)
