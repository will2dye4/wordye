#!/usr/bin/env python3

import random

from wordye import Game, MAX_ATTEMPTS


class AIGame(Game):

    def get_guess(self) -> str:
        # TODO - make this 'intelligent'
        guess = random.choice(list(self._valid_guesses))
        print(f'[{len(self.attempts) + 1}/{MAX_ATTEMPTS}] Guessing: {guess}')
        return guess


def main() -> None:
    AIGame().play()


if __name__ == '__main__':
    main()
