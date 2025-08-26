from collections.abc import Callable, Sequence
from typing import final

from returns.result import Failure, Success

from parsepy import Parser, ParseResult
from parsepy.basic_elements import TakeInclude, TakeUntil, TakeN


@final
class TakeAround[T](Parser[T]):
    """`TakeAround`.

    The parser will return the first slice around the start and end delimiter.

    This is similar to `TakeBetween`, except `TakeBetween` does not include
    the start and end delimiters in the taken slice, while `TakeAround` does
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
    from parsepy.sequence_combinators import TakeAround

    ###########################################################################
    # Succeeds with str with simple match delimiters
    input = "Hello Bob (the best Bob). Welcome."
    result = TakeAround("(", ")")(input)
    assert result == Success((". Welcome.", "(the best Bob)"))


    ###########################################################################
    # Succeeds with str with sequence match delimiters
    input = "BEGIN some text END here"
    result = TakeAround("BEGIN", "END")(input)
    assert result == Success((" here", "BEGIN some text END"))


    ###########################################################################
    # Succeeds with function delimiters
    input = "1 apple 2 oranges 3 melons."
    result = TakeAround(
        lambda x: x.isnumeric(),
        lambda x: x.isnumeric(),
    )(input)
    assert result == Success((" oranges 3 melons.", "1 apple 2"))


    ###########################################################################
    # Succeeds with nothing between delimiters.
    input = "prefix()suffix"
    result = TakeAround("(", ")")(input)
    assert result == Success(("suffix", "()"))

    ```
    """

    def __init__(
        self,
        start_delimiter: T | Sequence[T] | Callable[[*tuple[T, ...]], bool],
        end_delimiter: T | Sequence[T] | Callable[[*tuple[T, ...]], bool],
    ) -> None:
        """`TakeAround`.

        The parser will return the first slice around the start and end delimiter.

        This is similar to `TakeBetween`, except `TakeBetween` does not include
        the start and end delimiters in the taken slice, while `TakeAround` does
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

    def parse(
        self,
        input: Sequence[T],
    ) -> ParseResult[Sequence[T], Sequence[T]]:
        match TakeUntil(self.start_delimiter)(input):
            case Success((start_delim_onward, _)):
                pass
            case Failure(_):
                return Failure(
                    f"Could not find start_delimiter=`{self.start_delimiter}` in input."
                )

        # Temporary remove the start delim such that the end delim doesnt match
        # on the start delim
        after_start_delim_onward, start_delim = TakeInclude(self.start_delimiter)(
            start_delim_onward
        ).unwrap()

        len_start_delim = len(start_delim)

        # Find the end delim
        # Get the len of the input after the start_delim until and including the end delim
        match TakeInclude(self.end_delimiter)(after_start_delim_onward):
            case Success((_, taken_inc_end_delim)):
                len_taken_inc_end_delim = len(taken_inc_end_delim)
            case Failure(_):
                return Failure(
                    f"Could not find end_delimiter=`{self.end_delimiter}` in input after start_delimiter=`{self.start_delimiter}`."
                )

        # Find the len of the start delim and input until and including end delim
        len_around_both_delims = len_start_delim + len_taken_inc_end_delim

        # Take that length from the original start delim onward
        # This is the start delim up to and including the end delim and then the rest of the input
        rest, around_delims = TakeN(len_around_both_delims)(start_delim_onward).unwrap()
        return Success((rest, around_delims))
