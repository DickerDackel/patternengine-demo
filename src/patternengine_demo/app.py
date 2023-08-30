import pygame

from enum import Enum
from types import SimpleNamespace

from patternengine_demo.framework import App

from patternengine_demo.config import TITLE, SCREEN, FPS, States
from patternengine_demo.title import Title
from patternengine_demo.demo import Demo


def main():
    app = App(TITLE, SCREEN, FPS)

    persist = SimpleNamespace(
        font=pygame.Font(None),
    )

    states = {
        States.TITLE: Title(app, persist),
        States.DEMO: Demo(app, persist),
    }

    app.run(States.TITLE, states)


if __name__ == '__main__':
    main()
