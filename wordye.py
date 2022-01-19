#!/usr/bin/env python3

from dataclasses import dataclass, field
from enum import Enum
import argparse
import random
import string


MAX_ATTEMPTS = 6
WORD_LENGTH = 5


class HardModeRuleViolation(Exception):
    pass


class WordLengthViolation(Exception):
    pass


class WordExistenceViolation(Exception):
    pass


class LetterState(Enum):
    UNKNOWN = 1
    NOT_IN_WORD = 2
    IN_WORD = 3
    IN_CORRECT_POSITION = 4


@dataclass
class Letter:
    text: str
    state: LetterState


@dataclass
class Word:
    letters: list[Letter] = field(default_factory=list)


class Game:

    def __init__(self, hard_mode: bool = False) -> None:
        self.hard_mode = hard_mode
        self._attempts = []
        self._letters = {letter: LetterState.UNKNOWN for letter in string.ascii_uppercase}
        valid_solutions = get_word_list('valid_solutions.txt')
        self._solution = random.choice(valid_solutions)
        self._valid_guesses = set(valid_solutions + get_word_list('valid_guesses.txt'))

    @property
    def attempts(self) -> list[Word]:
        return self._attempts

    @property
    def game_over(self) -> bool:
        return self.won or len(self.attempts) >= MAX_ATTEMPTS

    @property
    def won(self) -> bool:
        return (
            0 < len(self.attempts) <= MAX_ATTEMPTS and
            all(letter.state == LetterState.IN_CORRECT_POSITION for letter in self.attempts[-1].letters)
        )

    def guess_word(self, guess: str) -> None:
        if self.game_over:
            return

        if not guess or len(guess) != WORD_LENGTH:
            raise WordLengthViolation()
        guess = guess.upper()

        if guess not in self._valid_guesses:
            raise WordExistenceViolation()

        if self.hard_mode and self.attempts:
            prev_attempt = self.attempts[-1]
            for index, letter in enumerate(prev_attempt.letters):
                if ((letter.state == LetterState.IN_CORRECT_POSITION and guess[index] != letter.text) or
                        (letter.state == LetterState.IN_WORD and letter.text not in guess)):
                    raise HardModeRuleViolation()

        word = Word()
        seen_letters = set()
        for guess_letter, correct_letter in zip(guess, self._solution):
            state = LetterState.NOT_IN_WORD
            if guess_letter == correct_letter:
                state = LetterState.IN_CORRECT_POSITION
            elif guess_letter in self._solution and guess_letter not in seen_letters:
                correct_index = self._solution.index(guess_letter)
                if guess[correct_index] != guess_letter:  # prevent marking the same letter as yellow and green
                    state = LetterState.IN_WORD
            word.letters.append(Letter(guess_letter, state))
            seen_letters.add(guess_letter)
            self._letters[guess_letter] = state  # TODO - need to reset non-ruled-out letters to unknown first?
        self.attempts.append(word)

    @staticmethod
    def format_text(text: str, format_code: str) -> str:
        return f'\033[{format_code}m{text}\033[0m'

    @classmethod
    def format_letter_text(cls, text: str, state: LetterState) -> str:
        if state == LetterState.IN_CORRECT_POSITION:
            return cls.format_text(text, '30;102')  # black on green
        elif state == LetterState.IN_WORD:
            return cls.format_text(text, '30;103')  # black on yellow
        elif state == LetterState.NOT_IN_WORD:
            return cls.format_text(text, '97;40')  # white on black
        return text

    def print_last_guess(self) -> None:
        if self.attempts:
            guess = [
                f' {self.format_letter_text(f" {letter.text} ", letter.state)} '
                for letter in self.attempts[-1].letters
            ]
            print(f'\n{"".join(guess)}')

    def make_guess(self) -> None:
        letters = ''.join(
            self.format_letter_text(letter, state)
            for letter, state in self._letters.items()
            if state != LetterState.NOT_IN_WORD
        )
        while True:
            try:
                guess = input(f'[{len(self.attempts) + 1}/{MAX_ATTEMPTS}] Enter guess ({letters}): ')
            except EOFError:
                raise KeyboardInterrupt()

            try:
                self.guess_word(guess)
            except HardModeRuleViolation:
                print('Invalid guess! Must use all revealed hints from previous guesses (hard mode).')
            except WordLengthViolation:
                print(f'Invalid guess! Must be {WORD_LENGTH} letters long.')
            except WordExistenceViolation:
                print(f'Invalid guess! Could not find "{guess}" in the dictionary.')
            else:
                return

    def play(self) -> None:
        try:
            print('  _  ' * WORD_LENGTH)
            while not self.game_over:
                self.make_guess()
                self.print_last_guess()
            if self.won:
                attempts = len(self.attempts)
                pluralized_tries = 'try' if attempts == 1 else 'tries'
                print(f'Congrats! You solved it in {attempts} {pluralized_tries}!')
            else:
                print('Better luck next time!')
                print(f'The correct solution was: {self._solution}')
        except KeyboardInterrupt:
            print('\nGoodbye!')


def get_word_list(filename) -> list[str]:
    with open(filename) as f:
        return [line.strip().upper() for line in f if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description='play a game of Wordye')
    parser.add_argument('-!', '--hard-mode', action='store_true', help='play in hard mode')
    args = parser.parse_args()
    Game(hard_mode=args.hard_mode).play()


if __name__ == '__main__':
    main()
