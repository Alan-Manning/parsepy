from collections.abc import Callable, Sequence
from typing import final

from returns.result import Failure, Success

from parsepy import Parser, ParseResult
from parsepy.basic_elements import TakeInclude, TakeUntil


@final
class TakeBetween[T](Parser[T]):
    """`TakeBetween`.

    The parser will return the first slice between the start and end delimiter.
    By default discard_end_delimiter=True means the parser will remove the end
    delimiter from the rest slice. Otherwise, the end delimiter is included in
    the rest slice.

    This is similar to `TakeAround`, except `TakeAround` includes the start
    and end delimiters in the taken slice, while `TakeBetween` does not
    include those delimiters in the taken slice.

    - If the start_delimiter or end_delimiter is a single element of type T,
    the delimiter is matched when it finds that element in the input. i.e.
    input[i] == delimiter.

    - If the start_delimiter or end_delimiter is a Sequence[T], the parser
    checks the input with a rolling window of size len(delimiter). The
    delimiter is matched when input[i: i + len(delimiter)] == delimiter.

    - If the start_delimiter or end_delimiter is a Callable, it must be a
    function that accepts one or more arguments of type T and returns a bool.
    The parser will slide a rolling window over the input, where the window
    size is determined by the number of parameters the Callable accepts. If
    the Callable returns True for any window, the delimiter is matched at that
    position.

    Fails if the start_delimiter is not found.
    Fails if the end_delimiter is not found after the start_delimiter.

    Example
    -------
    ```python
    from returns.result import Failure, Success
    from parsepy.sequence_combinators import TakeBetween

    ###########################################################################
    # Succeeds with str with simple match delimiters
    input = "Hello Bob (the best Bob). Welcome."
    result = TakeBetween("(", ")")(input)
    assert result == Success((". Welcome.", "the best Bob"))


    ###########################################################################
    # Succeeds with str with simple match delimiters, keeping the end_delimiter
    input = "Hello Bob (the best Bob). Welcome."
    result = TakeBetween("(", ")", discard_end_delimiter=False)(input)
    assert result == Success(("). Welcome.", "the best Bob"))


    ###########################################################################
    # Succeeds with nothing between delimiters.
    input = "prefix()suffix"
    result = TakeBetween("(", ")")(input)
    assert result == Success(("suffix", ""))


    ###########################################################################
    # Succeeds with function delimiters
    input = "1 apple 2 oranges 3 melons."
    result = TakeBetween(
        lambda x: x.isnumeric(),
        lambda x: x.isnumeric(),
    )(input)
    assert result == Success((" oranges 3 melons.", " apple "))
    result = TakeBetween(
        lambda x: x.isnumeric(),
        lambda x: x.isnumeric(),
        discard_end_delimiter=False,
    )(input)
    assert result == Success(("2 oranges 3 melons.", " apple "))


    ###########################################################################
    # Succeeds with multi arg function delimiters
    input = "aa<<mid>>bb"
    result = TakeBetween(
        lambda a, b: a == "<" and b == "<",
        lambda a, b: a == ">" and b == ">",
    )(input)
    assert result == Success(("bb", "mid"))

    result = TakeBetween(
        lambda a, b: a == "<" and b == "<",
        lambda a, b: a == ">" and b == ">",
        discard_end_delimiter=False,
    )(input)
    assert result == Success((">>bb", "mid"))


    ###########################################################################
    # Succeeds with function delimiters on list[int]
    input = [5, 6, 7, 8, 9, 12, 13]
    result = TakeBetween(
        lambda x: x % 2 == 0,
        lambda x: x > 10,
    )(input)
    assert result == Success(([13], [7, 8, 9]))
    ```
    """

    def __init__(
        self,
        start_delimiter: T | Sequence[T] | Callable[[*tuple[T, ...]], bool],
        end_delimiter: T | Sequence[T] | Callable[[*tuple[T, ...]], bool],
        discard_end_delimiter: bool = True,
    ) -> None:
        """`TakeBetween`.

        The parser will return the first slice between the start and end delimiter.
        By default discard_end_delimiter=True means the parser will remove the end
        delimiter from the rest slice. Otherwise, the end delimiter is included in
        the rest slice.

        This is similar to `TakeAround`, except `TakeAround` includes the start
        and end delimiters in the taken slice, while `TakeBetween` does not
        include those delimiters in the taken slice.

        - If the start_delimiter or end_delimiter is a single element of type T,
        the delimiter is matched when it finds that element in the input. i.e.
        input[i] == delimiter.

        - If the start_delimiter or end_delimiter is a Sequence[T], the parser
        checks the input with a rolling window of size len(delimiter). The
        delimiter is matched when input[i: i + len(delimiter)] == delimiter.

        - If the start_delimiter or end_delimiter is a Callable, it must be a
        function that accepts one or more arguments of type T and returns a bool.
        The parser will slide a rolling window over the input, where the window
        size is determined by the number of parameters the Callable accepts. If
        the Callable returns True for any window, the delimiter is matched at that
        position.

        Fails if the start_delimiter is not found.
        Fails if the end_delimiter is not found after the start_delimiter.
        """
        self.start_delimiter = start_delimiter
        self.end_delimiter = end_delimiter
        self.discard_end_delimiter = discard_end_delimiter

    def _parse_keep_delimiter(
        self,
        input: Sequence[T],
    ) -> ParseResult[Sequence[T], Sequence[T]]:
        match TakeInclude(self.start_delimiter)(input):
            case Success((rest, _)):
                match TakeUntil(self.end_delimiter)(rest):
                    case Success((rest, taken_between_delimiters)):
                        return Success((rest, taken_between_delimiters))
                    case Failure(_):
                        return Failure(
                            f"Could not find end_delimiter=`{self.end_delimiter}` in input after start_delimiter=`{self.start_delimiter}`."
                        )
            case Failure(_):
                return Failure(
                    f"Could not find start_delimiter=`{self.start_delimiter}` in input."
                )

    def parse(
        self,
        input: Sequence[T],
    ) -> ParseResult[Sequence[T], Sequence[T]]:
        result = self._parse_keep_delimiter(input)

        if not self.discard_end_delimiter:
            return result

        # Remove the end_delimiter from rest by TakeInclude
        match result:
            case Success((rest, taken_between_delimiters)):
                match TakeInclude(self.end_delimiter)(rest):
                    case Success((rest, _)):
                        return Success((rest, taken_between_delimiters))
                    case Failure(_):
                        return Failure(
                            f"Could not remove end_delimiter=`{self.end_delimiter}` from the input."
                        )
            case Failure(_):
                return result

    # def old_parse(
    #     self,
    #     input: Sequence[T],
    # ) -> ParseResult[Sequence[T], Sequence[T]]:
    #     if self.include_delimiters:
    #         start_index_position = "start"
    #         end_index_position = "end"
    #     else:
    #         start_index_position = "end"
    #         end_index_position = "start"
    #
    #     result = TakeUntil(self.start_delimiter)(input)
    #     if not is_successful(result):
    #         return Failure(
    #             f"Could not find start_delimiter=`{self.start_delimiter}` in input."
    #         )
    #         rest, _taken = result.unwrap()
    #
    #     if self.include_delimiters:
    #         result = TakeUntil(self.start_delimiter)(input)
    #         if not is_successful(result):
    #             return Failure(
    #                 f"Could not find start_delimiter=`{self.start_delimiter}` in input."
    #             )
    #         rest, _taken = result.unwrap()
    #
    #         end_index_end = find_index(
    #             rest,
    #             self.end_delimiter,
    #             index_position="end",
    #         )
    #         if end_index_end == -1:
    #             return Failure(
    #                 f"Could not find end_delimiter=`{self.end_delimiter}` in input after start_delimiter=`{self.start_delimiter}`."
    #             )
    #
    #         taken = rest[:end_index_end]
    #         rest = rest[end_index_end:]
    #         return Success((rest, taken))
    #
    #     else:
    #         result = TakeInclude(self.start_delimiter)(input)
    #         if not is_successful(result):
    #             return Failure(
    #                 f"Could not find start_delimiter=`{self.start_delimiter}` in input."
    #             )
    #         rest, _taken = result.unwrap()
    #
    #         result = TakeUntil(self.end_delimiter)(rest)
    #
    #         if not is_successful(result):
    #             return Failure(
    #                 f"Could not find end_delimiter=`{self.end_delimiter}` in input after start_delimiter=`{self.start_delimiter}`."
    #             )
    #         rest, taken_between_delimiters = result.unwrap()
    #
    #         # end delimiter not included in taken_between_delimiters
    #         # the end delimiter is included in rest though
    #         # so remove the end_delimiter from rest by TakeInclude
    #         result = TakeInclude(self.end_delimiter)(rest)
    #
    #         match result:
    #             case Success((rest, _taken_end_delimiter)):
    #                 return Success((rest, taken_between_delimiters))
    #             case Failure(_):
    #                 return Failure(
    #                     f"Could not remove end_delimiter=`{self.end_delimiter}` from the input."
    #                 )
    #
    #     # ######################################################################
    #     # ######################################################################
    #     # ######################################################################
    #     # ######################################################################
    #     # ######################################################################
    #     # if self.include_delimiters:
    #     #     result = TakeUntil(self.start_delimiter)(input)
    #     # else:
    #     #     result = TakeInclude(self.start_delimiter)(input)
    #     #
    #     # if not is_successful(result):
    #     #     return Failure(
    #     #         f"Could not find start_delimiter=`{self.start_delimiter}` in input."
    #     #     )
    #     # rest, _taken = result.unwrap()
    #     #
    #     # if self.include_delimiters:
    #     #     result = TakeInclude(self.end_delimiter)(rest)
    #     # else:
    #     #     result = TakeUntil(self.end_delimiter)(rest)
    #     #
    #     # if not is_successful(result):
    #     #     return Failure(
    #     #         f"Could not find end_delimiter=`{self.end_delimiter}` in input after start_delimiter=`{self.start_delimiter}`."
    #     #     )
    #     # rest, taken_between_delimiters = result.unwrap()
    #     #
    #     # if self.include_delimiters:
    #     #     # end delimiter already included in taken_between_delimiters so just return
    #     #     return Success((rest, taken_between_delimiters))
    #     # else:
    #     #     # end delimiter not included in taken_between_delimiters
    #     #     # the end delimiter is included in rest though
    #     #     # so remove the end_delimiter from rest by TakeInclude
    #     #     result = TakeInclude(self.end_delimiter)(rest)
    #     #
    #     #     match result:
    #     #         case Success((rest, _taken_end_delimiter)):
    #     #             return Success((rest, taken_between_delimiters))
    #     #         case Failure(_):
    #     #             return Failure(
    #     #                 f"Could not remove end_delimiter=`{self.end_delimiter}` from the input."
    #     #             )
