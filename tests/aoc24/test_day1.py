from parsepy import ParseResult
from parsepy.basic_elements import TakeWhile, TakeUntil, TakeInclude
from returns.result import Success, Result, Failure


###############################################################################
# Advent of code 2024 day 1 part 1 test input
###############################################################################
TEST_INPUT = """3   4
4   3
2   5
1   3
3   9
3   3
"""
# This is equivilant to: test_input = '3   4\n4   3\n2   5\n1   3\n3   9\n3   3\n'

PART_1_CORRECT_ANSWER = 11
PART_2_CORRECT_ANSWER = 31

###############################################################################
# Line parsing
###############################################################################


def get_line(input: str) -> ParseResult[str, str]:
    """Get the left number chars, space chars, and right number chars untill a
    new line escape char.

    The line does not include this new line escape char.
    """
    match TakeInclude("\n")(input):
        case Success((rest, taken)):
            _, taken = TakeUntil("\n")(taken).unwrap()
            return Success((rest, taken))
        case Failure(err_msg):
            return Failure(err_msg)


def get_lines(input: str) -> ParseResult[str, list[str]]:
    """Get all the lines from the input."""
    more_lines = True

    lines: list[str] = []
    rest = input

    while more_lines:
        result = get_line(rest)
        match result:
            case Success((rest, line)):
                lines.append(line)
            case Failure(_):
                more_lines = False
                break

    return Success((rest, lines))


###############################################################################
# Nubmers parsing
###############################################################################


def get_number(input: str) -> ParseResult[str, int]:
    """Get the number from input."""
    match TakeWhile(lambda x: x.isnumeric())(input):
        case Success((rest, left_num_str)):
            return Success((rest, int(left_num_str)))
        case Failure(_):
            return Failure("Couldn't find number!")


def get_left_right_list_nos_from_line(line: str) -> ParseResult[str, tuple[int, int]]:
    """Get the left number and right number from a line."""
    match get_number(line):
        case Success((rest, left_num)):
            pass
        case Failure(_):
            return Failure(f"Couldn't find left number in line: `{line}` ")

    match TakeUntil(lambda x: x.isnumeric())(rest):
        case Success((rest, _)):
            pass
        case Failure(_):
            return Failure(f"Couldn't find right number in line: `{line}` ")

    match get_number(rest):
        case Success((_, right_num)):
            return Success((left_num, right_num))
        case Failure(_):
            return Failure(f"Couldn't find right number in line: `{line}` ")


def get_all_left_right_numbers(lines: list[str]) -> tuple[list[int], list[int]]:
    """Get all the left numbers and all the right numbers as lists of ints."""
    left_numbers: list[int] = []
    right_numbers: list[int] = []

    for line in lines:
        match get_left_right_list_nos_from_line(line):
            case Success((left_num, right_num)):
                left_numbers.append(left_num)
                right_numbers.append(right_num)
            case Failure(err_msg):
                raise RuntimeError(err_msg)
    return (left_numbers, right_numbers)


###############################################################################
# Solving
###############################################################################


def solve_part_1(input: str) -> int:
    _, lines = get_lines(input).unwrap()

    left_numbers, right_numbers = get_all_left_right_numbers(lines)

    left_numbers.sort()
    right_numbers.sort()

    running_diff = 0

    for left_no, right_no in zip(left_numbers, right_numbers):
        running_diff += abs(left_no - right_no)

    return running_diff


def solve_part_2(input: str) -> int:
    _, lines = get_lines(input).unwrap()

    left_numbers, right_numbers = get_all_left_right_numbers(lines)

    running_similarity_score = 0

    for left_no in left_numbers:
        no_of_occurrences_in_right = right_numbers.count(left_no)
        similarity_score = left_no * no_of_occurrences_in_right
        running_similarity_score += similarity_score

    return running_similarity_score


if __name__ == "__main__":
    part_1_answer = solve_part_1(TEST_INPUT)
    assert part_1_answer == PART_1_CORRECT_ANSWER

    part_2_answer = solve_part_2(TEST_INPUT)
    assert part_2_answer == PART_2_CORRECT_ANSWER


def test_AOC_day_1_part_1():
    part_1_answer = solve_part_1(TEST_INPUT)
    assert part_1_answer == PART_1_CORRECT_ANSWER


def test_AOC_day_1_part_2():
    part_2_answer = solve_part_2(TEST_INPUT)
    assert part_2_answer == PART_2_CORRECT_ANSWER
