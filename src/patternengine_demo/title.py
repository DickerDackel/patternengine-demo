import pygame
import tinyecs.compsys as ecsc

from pgcooldown import Cooldown
from patternengine_demo.framework import GameState
from patternengine_demo.config import States


class Title(GameState):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.group = pygame.sprite.Group()
        self.group_off = pygame.sprite.Group()

        font = pygame.Font(None, 64)
        image = font.render('Pattern Engine Demo', True, 'white')
        sprite = ecsc.ESprite(self.group, self.group_off, image=image)
        sprite.rect.center = (self.app.rect.centerx, self.app.rect.height // 5 * 2)

        font = pygame.Font(None, 48)
        image = font.render('press SPACE', True, 'white')
        sprite = ecsc.ESprite(self.group, image=image)
        sprite.rect.center = (self.app.rect.centerx, self.app.rect.height // 5 * 3)

        self.blink_cooldown = Cooldown(0.5)
        self.blink = True
        self.go = False

    def reset(self, *args, **kwargs):
        super().reset(*args, **kwargs)
        self.blink_cooldown.reset()
        self.blink = True
        self.go = False

    def dispatch_event(self, e):
        super().dispatch_event(e)
        match e.type:
            case pygame.KEYDOWN if e.key == pygame.K_SPACE:
                self.go = True

    def update(self, dt):
        if self.go:
            return States.DEMO, self.persist

        if self.blink_cooldown.cold:
            self.blink_cooldown.reset()
            self.blink = not self.blink

        self.group.update(dt)

    def draw(self, screen):
        screen.fill('black')

        if self.blink:
            self.group.draw(screen)
        else:
            self.group_off.draw(screen)
