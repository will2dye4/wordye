#!/usr/bin/env python3

from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
import argparse
import random
import string


MAX_ATTEMPTS = 6
WORD_LENGTH = 5

BLACK_SQUARE_EMOJI = '\u2B1B'
GREEN_SQUARE_EMOJI = '\U0001f7e9'
YELLOW_SQUARE_EMOJI = '\U0001f7e8'


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


class Game(ABC):

    def __init__(self, hard_mode: bool = False) -> None:
        self.hard_mode = hard_mode
        self._attempts = []
        self._letters = {letter: LetterState.UNKNOWN for letter in string.ascii_uppercase}
        valid_solutions = get_word_list('valid_solutions.txt')
        self._solution = random.choice(valid_solutions)
        self._valid_guesses = set(valid_solutions + get_word_list('valid_guesses.txt'))
        self._correct_letter_indices = defaultdict(list)
        for index, letter in enumerate(self._solution):
            self._correct_letter_indices[letter].append(index)

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
                if letter.state == LetterState.IN_CORRECT_POSITION and guess[index] != letter.text:
                    #  or (letter.state == LetterState.IN_WORD and letter.text not in guess)):
                    raise HardModeRuleViolation()

        for letter, state in self._letters.items():
            if state != LetterState.NOT_IN_WORD:
                self._letters[letter] = LetterState.UNKNOWN

        guess_letter_indices = defaultdict(list)
        for index, letter in enumerate(guess):
            guess_letter_indices[letter].append(index)

        word = Word()
        for index, (guess_letter, correct_letter) in enumerate(zip(guess, self._solution)):
            state = LetterState.NOT_IN_WORD
            if guess_letter == correct_letter:
                state = LetterState.IN_CORRECT_POSITION
            elif guess_letter in self._solution:
                correct_indices = self._correct_letter_indices[guess_letter]
                correctly_guessed_indices = []
                incorrectly_guessed_indices = []
                for i in guess_letter_indices[guess_letter]:
                    if i in correct_indices:
                        correctly_guessed_indices.append(i)
                    else:
                        incorrectly_guessed_indices.append(i)
                if incorrectly_guessed_indices.index(index) + len(correctly_guessed_indices) < len(correct_indices):
                    state = LetterState.IN_WORD
            word.letters.append(Letter(guess_letter, state))
            self._letters[guess_letter] = state
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

    def print_game_emoji(self) -> None:
        if not self.game_over:
            return
        if ''.join(letter.text for letter in self.attempts[-1].letters) == self._solution:
            score = len(self.attempts)
        else:
            score = 'X'
        heading = f'Wordye {self._solution} {score}/{MAX_ATTEMPTS}'
        if self.hard_mode:
            heading += '*'
        print(f'\n{heading}')
        for attempt in self.attempts:
            word_emoji = ''
            for letter in attempt.letters:
                if letter.state == LetterState.IN_CORRECT_POSITION:
                    word_emoji += GREEN_SQUARE_EMOJI
                elif letter.state == LetterState.IN_WORD:
                    word_emoji += YELLOW_SQUARE_EMOJI
                else:
                    word_emoji += BLACK_SQUARE_EMOJI
            print(word_emoji)

    @abstractmethod
    def get_guess(self) -> str:
        raise NotImplementedError()

    def make_guess(self) -> None:
        while True:
            guess = self.get_guess()
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

    def play(self) -> bool:
        try:
            print('\n' + ('  _  ' * WORD_LENGTH))
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
            self.print_game_emoji()
        except KeyboardInterrupt:
            if self.game_over:
                print('\nGoodbye!')
            else:
                print(f'\nYou lost! The correct answer was: {self._solution}')
        return self.won


class CLIGame(Game):

    def get_guess(self) -> str:
        letters = ''.join(
            self.format_letter_text(letter, state)
            for letter, state in self._letters.items()
            if state != LetterState.NOT_IN_WORD
        )
        try:
            return input(f'[{len(self.attempts) + 1}/{MAX_ATTEMPTS}] Enter guess ({letters}): ')
        except EOFError:
            raise KeyboardInterrupt()


def get_word_list(filename) -> list[str]:
    with open(filename) as f:
        return [line.strip().upper() for line in f if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description='play a game of Wordye')
    parser.add_argument('-!', '--hard-mode', action='store_true', help='play in hard mode')
    args = parser.parse_args()
    CLIGame(hard_mode=args.hard_mode).play()


if __name__ == '__main__':
    main()
