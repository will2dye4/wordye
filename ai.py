#!/usr/bin/env python3

import random

from wordye import Game, LetterState, MAX_ATTEMPTS


STARTING_GUESS = 'ADIEU'


class AIGame(Game):

    def __init__(self) -> None:
        # The algorithm as implemented always plays by the hard mode rules.
        super().__init__(hard_mode=True)
        self._candidates = self._valid_guesses.copy()

    def filter_candidates_for_exact_match(self, letter: str, index: int) -> None:
        self._candidates = {word for word in self._candidates if word[index] == letter}

    def filter_candidates_for_inexact_match(self, letter: str, index: int) -> None:
        self._candidates = {word for word in self._candidates if word[index] != letter and letter in word}

    def exclude_candidates(self, letter: str) -> None:
        self._candidates -= {word for word in self._candidates if letter in word}

    def get_guess(self) -> str:
        if self.attempts:
            prev_attempt = self.attempts[-1]
            for index, letter in enumerate(prev_attempt.letters):
                text = letter.text
                if letter.state == LetterState.IN_CORRECT_POSITION:
                    self.filter_candidates_for_exact_match(text, index)
                elif letter.state == LetterState.IN_WORD:
                    self.filter_candidates_for_inexact_match(text, index)
                elif letter.state == LetterState.NOT_IN_WORD and not any(
                        letter.text == text and letter.state in (LetterState.IN_WORD, LetterState.IN_CORRECT_POSITION)
                        for letter in prev_attempt.letters
                ):
                    self.exclude_candidates(text)
            if (candidates := len(self._candidates)) > 1:
                print(f'Considering {candidates:,} total candidates...')
            else:
                print('Solved it!')
            guess = random.choice(list(self._candidates))
        else:
            guess = STARTING_GUESS
        print(f'[{len(self.attempts) + 1}/{MAX_ATTEMPTS}] Guessing: {guess}')
        self._candidates.remove(guess)
        return guess


def main() -> None:
    AIGame().play()


if __name__ == '__main__':
    main()
