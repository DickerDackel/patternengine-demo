import pygame

from enum import Enum

FPS = 60
SCREEN = pygame.Rect(0, 0, 1024, 768)
TITLE = 'Pattern Engine Demo'


class States(Enum):
    TITLE = 1
    DEMO = 2
