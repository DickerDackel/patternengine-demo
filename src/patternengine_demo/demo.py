import pygame
import tinyecs as ecs
import tinyecs.compsys as ecsc

import patternengine as pe
import patternengine.compsys as pecs

from functools import lru_cache, partial
from itertools import cycle
from random import random

from pgcooldown import Cooldown, CronD, LerpThing
from pygame import Vector2
from patternengine_demo.framework import GameState
from rpeasings import *  # noqa: F401, F403

from patternengine_demo.config import States


class FBlitGroup(pygame.sprite.Group):
    def draw(self, screen):
        blit_list = [(sprite.image, sprite.rect.topleft) for sprite in self.sprites()]
        screen.fblits(blit_list)


crond = CronD()
sprite_group = FBlitGroup()


class TextSprite(pygame.sprite.Sprite):
    def __init__(self, pos, group, size=48):
        super().__init__(group)

        self._text = ''

        self.font = pygame.Font(None, size)
        self.image = self.font.render(self._text, True, 'white')
        self.rect = self.image.get_rect(center=pos)

    @property
    def text(self): return self._text  # noqa: E704

    @text.setter
    def text(self, s):
        self._text = s
        self.image = self.font.render(s, True, 'white')
        self.rect = self.image.get_rect(center=self.rect.center)

    def __repr__(self):
        return self._text


@lru_cache
def bullet_image_factory(r0, r1, w, c0, c1, c2=None):
    size = 2 * r1 if r1 else 2 * r0
    image = pygame.Surface((size, size))
    image.set_colorkey('black')
    rect = image.get_rect()

    c0 = pygame.Color(c0)
    c1 = pygame.Color(c1)

    for i in range(0, r0 - 1):
        t = out_sine(i / r0)  # noqa: F405
        color = c1.lerp(c0, t)
        r = r0 - i
        pygame.draw.circle(image, color, rect.center, r)

    if r1:
        if not c2:
            c2 = c0
        pygame.draw.circle(image, c2, rect.center, r1, width=w)

    return image


def bullet_factory(position, momentum, speed, image, sprite_group, fade=False, **kwargs):
    fade_duration = 0.25

    e = ecs.create_entity()
    ecs.add_component(e, 'position', position)
    ecs.add_component(e, 'momentum', momentum * speed)
    ecs.add_component(e, 'world', True)

    if fade & 1:
        rsai = ecsc.RSAImage(image=image, alpha=0)
        ecs.add_component(e, 'rsai', rsai)
        ecs.add_component(e, 'sprite', ecsc.EVSprite(rsai, sprite_group))
        ecs.add_component(e, 'fade', LerpThing(0, 255, fade_duration, ease=in_quad))  # noqa: F405
    else:
        ecs.add_component(e, 'sprite', ecsc.ESprite(sprite_group, image=image))

    def add_fadeout(eid):
        if ecs.has(eid):
            ecs.add_component(eid, 'fade', LerpThing(255, 0, fade_duration, ease=in_quad))  # noqa: F405

    for cid, comp in kwargs.items():
        if cid == 'rotation':
            comp.duration.reset()

        if cid == 'lifetime':
            comp = Cooldown(comp)

            if fade & 2:
                fadeout_start = comp.duration
                crond.add(fadeout_start - fade_duration, partial(add_fadeout, e))

        ecs.add_component(e, cid, comp)

    return e


def pattern_factory(position, bullet_source, bullet_factory, **kwargs):
    if not isinstance(position, Vector2):
        position = Vector2(position)
    e = ecs.create_entity()
    ecs.add_component(e, 'position', position)
    ecs.add_component(e, 'bullet_source', bullet_source)
    ecs.add_component(e, 'bullet_factory', bullet_factory)
    ecs.add_component(e, 'lifetime-display', True)
    for cid, comp in kwargs.items():
        if cid == 'lifetime':
            comp = Cooldown(comp)
        ecs.add_component(e, cid, comp)
    return e


BULLET_IMAGES = {
    'hotpink': bullet_image_factory(8, 0, 1, 'white', 'hotpink', 'hotpink'),
    'cyan': bullet_image_factory(8, 0, 1, 'cyan', 'darkblue', 'cyan'),
    'yellow': bullet_image_factory(9, 12, 1, 'yellow', 'darkorange', 'darkorange'),
    'lightblue': bullet_image_factory(10, 13, 1, 'white', 'lightblue', 'lightblue'),
    'green': bullet_image_factory(6, 8, 1, 'yellow', 'green', 'green'),
    'red': bullet_image_factory(4, 0, 1, 'red', 'brown', 'red'),
    'beat': bullet_image_factory(16, 0, 0, 'white', 'grey80', 'white'),
}

BULLET_FACTORIES = {
    'hotpink': partial(bullet_factory, sprite_group=sprite_group, image=BULLET_IMAGES['hotpink']),
    'cyan': partial(bullet_factory, sprite_group=sprite_group, image=BULLET_IMAGES['cyan']),
    'yellow': partial(bullet_factory, sprite_group=sprite_group, image=BULLET_IMAGES['yellow']),
    'lightblue': partial(bullet_factory, sprite_group=sprite_group, image=BULLET_IMAGES['lightblue']),
    'green': partial(bullet_factory, sprite_group=sprite_group, image=BULLET_IMAGES['green']),
    'red': partial(bullet_factory, sprite_group=sprite_group, image=BULLET_IMAGES['red']),
    'beat': partial(bullet_factory, sprite_group=sprite_group, image=BULLET_IMAGES['beat']),
}


def schedule_demo(t, label, rect, target):
    def update_label(s):
        label.text = s

    crond.add(t, partial(update_label, 'Simple 4 step ring'))
    crond.add(t, partial(pattern_factory,
                         position=rect.center,
                         bullet_source=pe.BulletSource(
                             bullets=4,
                             ring=pe.Ring(50, 4),
                             heartbeat=pe.Heartbeat(1, '#.......#.......')),
                         bullet_factory=partial(BULLET_FACTORIES['hotpink'], speed=100, fade=1),
                         lifetime=7.95))
    t += 8

    crond.add(t, partial(update_label, 'Ring stack'))
    crond.add(t, partial(pattern_factory,
                         position=rect.center,
                         bullet_source=pe.BulletSource(
                             bullets=18,
                             ring=pe.Ring(50, 18),
                             heartbeat=pe.Heartbeat(1, '#.#.#...........')),
                         bullet_factory=partial(BULLET_FACTORIES['cyan'], speed=100, fade=1),
                         lifetime=7.95))
    t += 8

    crond.add(t, partial(update_label, 'Simple ring + Stack with 10° aim'))
    crond.add(t, partial(pattern_factory,
                         position=rect.center,
                         bullet_source=pe.BulletSource(
                             bullets=18,
                             ring=pe.Ring(50, 18),
                             heartbeat=pe.Heartbeat(1, '#.......#.......')),
                         bullet_factory=partial(BULLET_FACTORIES['hotpink'], speed=100, fade=1),
                         lifetime=7.95))
    crond.add(t, partial(pattern_factory,
                         position=rect.center,
                         bullet_source=pe.BulletSource(
                             bullets=18,
                             ring=pe.Ring(50, 18),
                             heartbeat=pe.Heartbeat(1, '#.#.#...........'),
                             aim=10),
                         bullet_factory=partial(BULLET_FACTORIES['cyan'], speed=100, fade=1),
                         lifetime=7.95))
    t += 8

    crond.add(t, partial(update_label, 'Ring with 5 steps'))
    crond.add(t, partial(pattern_factory,
                         position=rect.center,
                         bullet_source=pe.BulletSource(
                             bullets=5,
                             ring=pe.Ring(50, 5),
                             heartbeat=pe.Heartbeat(1, '#...............')),
                         bullet_factory=partial(BULLET_FACTORIES['yellow'], speed=100, fade=1),
                         lifetime=3.95))
    t += 4
    crond.add(t, partial(update_label, 'Ring with 5 steps'))
    crond.add(t, partial(pattern_factory,
                         position=rect.center,
                         bullet_source=pe.BulletSource(
                             bullets=5,
                             ring=pe.Ring(50, 5),
                             heartbeat=pe.Heartbeat(1, '#.......#.......')),
                         bullet_factory=partial(BULLET_FACTORIES['yellow'], speed=100, fade=1),
                         lifetime=3.95))
    t += 4

    crond.add(t, partial(update_label, 'Ring with 5 steps, rotating'))
    crond.add(t, partial(pattern_factory,
                         position=rect.center,
                         bullet_source=pe.BulletSource(
                             bullets=5,
                             ring=pe.Ring(50, 5),
                             heartbeat=pe.Heartbeat(1, '#...#...#...#...')),
                         bullet_factory=partial(BULLET_FACTORIES['yellow'], speed=100, fade=3),
                         rotation=LerpThing(0, 360, 8, repeat=1),
                         lifetime=3.95))
    t += 4

    crond.add(t, partial(update_label, 'Ring with 1 step, rotating'))
    crond.add(t, partial(pattern_factory,
                         position=rect.center,
                         bullet_source=pe.BulletSource(
                             bullets=1,
                             ring=pe.Ring(50, 1),
                             heartbeat=pe.Heartbeat(1, '################')),
                         bullet_factory=partial(BULLET_FACTORIES['green'], speed=100, fade=1),
                         rotation=LerpThing(0, 360, 8, repeat=1),
                         lifetime=1.95))
    t += 2

    crond.add(t, partial(update_label, 'Ring with 2 steps, rotating'))
    crond.add(t, partial(pattern_factory,
                         position=rect.center,
                         bullet_source=pe.BulletSource(
                             bullets=2,
                             ring=pe.Ring(10, 2),
                             heartbeat=pe.Heartbeat(1, '#...#...#...#...')),
                         bullet_factory=partial(BULLET_FACTORIES['green'], speed=100, fade=1),
                         rotation=LerpThing(0, 360, 8, repeat=1),
                         lifetime=1.95))
    t += 2

    crond.add(t, partial(update_label, 'Ring with 4 steps, rotating'))
    crond.add(t, partial(pattern_factory,
                         position=rect.center,
                         bullet_source=pe.BulletSource(
                             bullets=4,
                             ring=pe.Ring(10, 4),
                             heartbeat=pe.Heartbeat(1, '#...#...#...#...')),
                         bullet_factory=partial(BULLET_FACTORIES['green'], speed=100, fade=1),
                         rotation=LerpThing(0, 360, 8, repeat=1),
                         lifetime=1.95))
    t += 2

    crond.add(t, partial(update_label, 'Ring with 8 steps, rotating'))
    crond.add(t, partial(pattern_factory,
                         position=rect.center,
                         bullet_source=pe.BulletSource(
                             bullets=8,
                             ring=pe.Ring(10, 8),
                             heartbeat=pe.Heartbeat(1, '#...#...#...#...')),
                         bullet_factory=partial(BULLET_FACTORIES['green'], speed=100, fade=1),
                         rotation=LerpThing(0, 360, 8, repeat=1),
                         lifetime=1.95))
    t += 2

    crond.add(t, partial(update_label, 'Ring with 36 steps, rotating'))
    crond.add(t, partial(pattern_factory,
                         position=rect.center,
                         bullet_source=pe.BulletSource(
                             bullets=36,
                             ring=pe.Ring(10, 36),
                             heartbeat=pe.Heartbeat(1, '#...#...#...#...')),
                         bullet_factory=partial(BULLET_FACTORIES['green'], speed=100, fade=1),
                         rotation=LerpThing(0, 360, 8, repeat=1),
                         lifetime=3.95))
    t += 8

    crond.add(t, partial(update_label, 'Half rings'))
    crond.add(t, partial(pattern_factory,
                         position=(rect.centerx, 50),
                         bullet_source=pe.BulletSource(
                             bullets=18,
                             ring=pe.Ring(50, 18, aim=90, width=180),
                             heartbeat=pe.Heartbeat(1, '#...#...#...#...')),
                         bullet_factory=partial(BULLET_FACTORIES['hotpink'], speed=100, fade=1),
                         lifetime=7.95))
    crond.add(t, partial(pattern_factory,
                         position=(rect.centerx, rect.height - 50),
                         bullet_source=pe.BulletSource(
                             bullets=18,
                             ring=pe.Ring(50, 18, aim=-90, width=180),
                             heartbeat=pe.Heartbeat(1, '#...#...#...#...')),
                         bullet_factory=partial(BULLET_FACTORIES['cyan'], speed=100, fade=1),
                         lifetime=7.95))
    t += 4

    crond.add(t, partial(update_label, 'Quarter rings'))
    crond.add(t, partial(pattern_factory,
                         position=(50, 50),
                         bullet_source=pe.BulletSource(
                             bullets=5,
                             ring=pe.Ring(0, 5, aim=45, width=90),
                             heartbeat=pe.Heartbeat(2, '#.#.#.#.#.#.#.#.')),
                         bullet_factory=partial(BULLET_FACTORIES['green'], speed=100, fade=1),
                         lifetime=7.95))
    crond.add(t, partial(pattern_factory,
                         position=(rect.width - 50, rect.height - 50),
                         bullet_source=pe.BulletSource(
                             bullets=5,
                             ring=pe.Ring(0, 5, aim=-135, width=90),
                             heartbeat=pe.Heartbeat(2, '#.#.#.#.#.#.#.#.')),
                         bullet_factory=partial(BULLET_FACTORIES['green'], speed=100, fade=1),
                         lifetime=7.95))
    t += 4

    crond.add(t, partial(update_label, 'Actually any angle rings'))
    crond.add(t, partial(pattern_factory,
                         position=(rect.width / 4 * 3, 50),
                         bullet_source=pe.BulletSource(
                             bullets=4,
                             ring=pe.Ring(50, 4, aim=90, width=30),
                             heartbeat=pe.Heartbeat(2, '#...#...#...#...')),
                         bullet_factory=partial(BULLET_FACTORIES['yellow'], speed=100, fade=1),
                         lifetime=3.95))
    crond.add(t, partial(pattern_factory,
                         position=(rect.width / 4, rect.height - 50),
                         bullet_source=pe.BulletSource(
                             bullets=4,
                             ring=pe.Ring(50, 4, aim=-90, width=30),
                             heartbeat=pe.Heartbeat(1, '#...#...#...#...')),
                         bullet_factory=partial(BULLET_FACTORIES['yellow'], speed=100, fade=1),
                         lifetime=3.95))
    t += 8

    crond.add(t, partial(update_label, 'Oscillating partial ring'))
    crond.add(t, partial(pattern_factory,
                         position=(rect.centerx, 50),
                         bullet_source=pe.BulletSource(
                             bullets=5,
                             ring=pe.Ring(50, 5, width=30),
                             heartbeat=pe.Heartbeat(1, '#...#...#...#...')),
                         bullet_factory=partial(BULLET_FACTORIES['hotpink'], speed=200, fade=1),
                         rotation=LerpThing(165, 15, 2, repeat=2),
                         lifetime=7.95))
    t += 8

    crond.add(t, partial(update_label, 'Aiming partial ring'))
    crond.add(t, partial(ecs.add_component, target, 'circle', (16, 'red')))
    crond.add(t, partial(pattern_factory,
                         position=(rect.centerx, 50),
                         bullet_source=pe.BulletSource(
                             bullets=5,
                             ring=pe.Ring(50, 5, aim=-30, width=30),
                             heartbeat=pe.Heartbeat(1, '#...#...#...#...')),
                         bullet_factory=partial(BULLET_FACTORIES['green'], speed=200, fade=1),
                         lifetime=7.95,
                         target=target))
    t += 8

    crond.add(t, partial(ecs.remove_component, target, 'circle'))
    crond.add(t, partial(update_label, 'Static ring, turning bullets'))
    crond.add(t, partial(pattern_factory,
                         position=rect.center,
                         bullet_source=pe.BulletSource(
                             bullets=16,
                             ring=pe.Ring(250, 8),
                             heartbeat=pe.Heartbeat(1, '#...#...#...#...')),
                         bullet_factory=partial(BULLET_FACTORIES['cyan'], speed=150, lifetime=4, angular_momentum=90, fade=1),
                         # rotation=LerpThing(0, 360, 16, repeat=1),
                         lifetime=3.95))
    t += 8

    crond.add(t, partial(update_label, 'Slow turning bullets, negative speed'))
    crond.add(t, partial(pattern_factory,
                         position=rect.center,
                         bullet_source=pe.BulletSource(
                             bullets=16,
                             ring=pe.Ring(250, 16),
                             heartbeat=pe.Heartbeat(1, '#...#...#...#...')),
                         bullet_factory=partial(BULLET_FACTORIES['cyan'], speed=-150, lifetime=8, angular_momentum=15, fade=1),
                         lifetime=7.95))
    t += 8

    crond.add(t, partial(update_label, 'Fast turning bullets, negative speed'))
    crond.add(t, partial(pattern_factory,
                         position=rect.center,
                         bullet_source=pe.BulletSource(
                             bullets=16,
                             ring=pe.Ring(100, 16),
                             heartbeat=pe.Heartbeat(1, '#...#...#...#...')),
                         bullet_factory=partial(BULLET_FACTORIES['green'], speed=-150, lifetime=8, angular_momentum=45, fade=3),
                         lifetime=8))
    t += 16

    crond.add(t, partial(update_label, 'Rotating 5 step ring in motion'))
    crond.add(t, partial(pattern_factory,
                         position=(50, 50),
                         momentum=Vector2(1024, 768).normalize() * 100,
                         bullet_source=pe.BulletSource(
                             bullets=5,
                             ring=pe.Ring(50, 5),
                             heartbeat=pe.Heartbeat(1, '#.#.#.#.#.#.#.#.')),
                         bullet_factory=partial(BULLET_FACTORIES['yellow'], speed=10, lifetime=8, fade=3),
                         fade=1,
                         rotation=LerpThing(0, 360, 8, repeat=1),
                         lifetime=16))
    t += 16

    crond.add(t, partial(update_label, 'Is python too slow?'))
    crond.add(t, partial(pattern_factory,
                         position=(100, 100),
                         bullet_source=pe.BulletSource(
                             bullets=8,
                             ring=pe.Ring(25, 8),
                             heartbeat=pe.Heartbeat(2, '###.............')),
                         bullet_factory=partial(BULLET_FACTORIES['cyan'], speed=100),
                         lifetime=47.95))
    crond.add(t, partial(pattern_factory,
                         position=(rect.width - 100, 100),
                         bullet_source=pe.BulletSource(
                             bullets=8,
                             ring=pe.Ring(25, 8),
                             heartbeat=pe.Heartbeat(2, '###.............')),
                         bullet_factory=partial(BULLET_FACTORIES['cyan'], speed=100),
                         lifetime=47.95))
    t += 8

    crond.add(t, partial(pattern_factory,
                         position=(100, 100),
                         bullet_source=pe.BulletSource(
                             bullets=36,
                             ring=pe.Ring(50, 36),
                             heartbeat=pe.Heartbeat(2, '........#.......')),
                         bullet_factory=partial(BULLET_FACTORIES['hotpink'], speed=100),
                         lifetime=39.95))
    crond.add(t, partial(pattern_factory,
                         position=(rect.width - 100, 100),
                         bullet_source=pe.BulletSource(
                             bullets=36,
                             ring=pe.Ring(50, 36),
                             heartbeat=pe.Heartbeat(2, '........#.......')),
                         bullet_factory=partial(BULLET_FACTORIES['hotpink'], speed=100),
                         lifetime=39.95))
    t += 8

    crond.add(t, partial(pattern_factory,
                         position=(100, 100),
                         bullet_source=pe.BulletSource(
                             bullets=36,
                             ring=pe.Ring(50, 36),
                             heartbeat=pe.Heartbeat(2, '#...#...#...#...')),
                         bullet_factory=partial(BULLET_FACTORIES['hotpink'], speed=100),
                         lifetime=37.95))
    crond.add(t, partial(pattern_factory,
                         position=(rect.width - 100, 100),
                         bullet_source=pe.BulletSource(
                             bullets=36,
                             ring=pe.Ring(50, 36),
                             heartbeat=pe.Heartbeat(2, '#...#...#...#...')),
                         bullet_factory=partial(BULLET_FACTORIES['hotpink'], speed=100),
                         lifetime=37.95))
    t += 4

    crond.add(t, partial(pattern_factory,
                         position=(100, 100),
                         bullet_source=pe.BulletSource(
                             bullets=36,
                             ring=pe.Ring(50, 36),
                             heartbeat=pe.Heartbeat(2, '#.#.#.#.#.#.#.#.')),
                         bullet_factory=partial(BULLET_FACTORIES['hotpink'], speed=100),
                         lifetime=33.95))
    crond.add(t, partial(pattern_factory,
                         position=(rect.width - 100, 100),
                         bullet_source=pe.BulletSource(
                             bullets=36,
                             ring=pe.Ring(50, 36),
                             heartbeat=pe.Heartbeat(2, '#.#.#.#.#.#.#.#.')),
                         bullet_factory=partial(BULLET_FACTORIES['hotpink'], speed=100),
                         lifetime=33.95))
    t += 4

    crond.add(t, partial(pattern_factory,
                         position=(100, rect.height - 100),
                         bullet_source=pe.BulletSource(
                             bullets=10,
                             ring=pe.Ring(30, 10),
                             heartbeat=pe.Heartbeat(2, '#...#...#...#...')),
                         bullet_factory=partial(BULLET_FACTORIES['green'], speed=100, angular_momentum=45, lifetime=10),
                         lifetime=29.95))
    crond.add(t, partial(pattern_factory,
                         position=(rect.width - 100, rect.height - 100),
                         bullet_source=pe.BulletSource(
                             bullets=10,
                             ring=pe.Ring(30, 10),
                             heartbeat=pe.Heartbeat(2, '#...#...#...#...')),
                         bullet_factory=partial(BULLET_FACTORIES['green'], speed=100, angular_momentum=45, lifetime=10),
                         lifetime=29.95))
    t += 8

    crond.add(t, partial(pattern_factory,
                         position=rect.center,
                         bullet_source=pe.BulletSource(
                             bullets=16,
                             ring=pe.Ring(100, 16),
                             heartbeat=pe.Heartbeat(2, '#.#.#.#.#.#.#.#.')),
                         bullet_factory=partial(BULLET_FACTORIES['yellow'], speed=100, fade=1),
                         rotation=LerpThing(0, 360, 5, repeat=1),
                         lifetime=21.95))
    t += 8

    crond.add(t, partial(pattern_factory,
                         position=rect.center,
                         bullet_source=pe.BulletSource(
                             bullets=8,
                             ring=pe.Ring(100, 8),
                             heartbeat=pe.Heartbeat(1, '#.#.#.#.#.#.#.#.')),
                         bullet_factory=partial(BULLET_FACTORIES['lightblue'], speed=-100, angular_momentum=10, fade=1),
                         rotation=LerpThing(0, 360, 5, repeat=1),
                         lifetime=13.95))
    t += 8

    crond.add(t, partial(pattern_factory,
                         position=rect.center,
                         bullet_source=pe.BulletSource(
                             bullets=6,
                             ring=pe.Ring(0, 6),
                             heartbeat=pe.Heartbeat(2, '################')),
                         bullet_factory=partial(BULLET_FACTORIES['red'], speed=150, angular_momentum=35, lifetime=16),
                         rotation=LerpThing(0, 360, 4, repeat=1),
                         lifetime=8))
    t += 24

    crond.add(t, partial(update_label, ''))
    t += 3
    return t


class Demo(GameState):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.bgcolor = pygame.Color('black')
        self.bgcrit = pygame.Color('red')

        self.group = FBlitGroup()
        self.target = ecs.create_entity('target')
        ecs.add_component(self.target, 'position', Vector2(self.app.rect.center))
        ecs.add_component(self.target, 'momentum', Vector2(1, 0).rotate(random() * 30 + 15) * 100)
        ecs.add_component(self.target, 'bounce', True)

        self.label = TextSprite((self.app.rect.centerx, 50), self.group)
        self.slowest = TextSprite((self.app.rect.centerx, self.app.rect.centery - 50), self.group)
        self.most = TextSprite((self.app.rect.centerx, self.app.rect.centery + 50), self.group)

        self.countdown = TextSprite(self.app.rect.center, self.group, size=128)

        self.countdown_text = None
        self.countdown_cooldown = Cooldown(1, cold=True)
        self.post_countdown = False

        self.deadzone = self.app.rect.scale_by(1.5)

        self.reset()

    def update_label(self, s):
        self.label.text = s

    def reset(self, *args, **kwargs):
        super().reset(*args, **kwargs)

        self.stats = {
            'slowest': [999, 0],
            'most': [0, 0]
        }

        self.label.text = ''

        self.countdown_text = iter(['3', '2', '1', 'Go!'])
        self.countdown.text = next(self.countdown_text)
        self.countdown_cooldown.reset()
        self.post_countdown = False
        self.group.add(self.countdown)

        rect = self.app.rect

        crond.heap.clear()
        t = 3
        t = schedule_demo(t, self.label, rect, self.target)

        def show_stats():
            self.slowest.text = f'Slowest: {self.stats["slowest"][1]} Sprites at {self.stats["slowest"][0]} FPS'
            self.most.text = f'Most: {self.stats["most"][1]} Sprites at {self.stats["most"][0]} FPS'

        crond.add(t, show_stats)
        t += 5

        def done():
            raise SystemExit

        crond.add(t, done)

    def do_countdown(self):
        if self.post_countdown:
            return

        if self.countdown_cooldown:
            return

        try:
            self.countdown.text = next(self.countdown_text)
        except StopIteration:
            self.post_countdown = True
            self.countdown.kill()
            return

        self.countdown_cooldown.reset()

    def update(self, dt):
        self.do_countdown()

        sprite_group.update(dt)
        self.group.update(dt)

        def bounce_system(dt, eid, bounce, position, momentum):
            if self.app.rect.collidepoint(position):
                return
            if position.x < 0:
                position.x = -position.x
                momentum.x = -momentum.x
            elif position.x > self.app.rect.width:
                position.x = 2 * self.app.rect.width - position.x
                momentum.x = -momentum.x
            if position.y < 0:
                position.y = -position.y
                momentum.y = -momentum.y
            elif position.y > self.app.rect.height:
                position.y = 2 * self.app.rect.height - position.y
                momentum.y = -momentum.y

        def fade_system(dt, eid, fade, rsai):
            rsai.alpha = fade()
            if fade.duration.cold:
                ecs.remove_component(eid, 'fade')

        def angular_momentum_system(dt, eid, angular_momentum, momentum):
            momentum.rotate_ip(angular_momentum * dt)

        crond.update()

        ecs.run_system(dt, fade_system, 'fade', 'rsai')
        ecs.run_system(dt, pecs.aim_ring_system, 'bullet_source', 'position', 'target')
        ecs.run_system(dt, pecs.bullet_source_rotate_system, 'bullet_source', 'rotation')
        ecs.run_system(dt, pecs.bullet_source_system, 'bullet_source', 'bullet_factory', 'position')
        ecs.run_system(dt, angular_momentum_system, 'angular_momentum', 'momentum')
        ecs.run_system(dt, bounce_system, 'bounce', 'position', 'momentum')
        ecs.run_system(dt, ecsc.momentum_system, 'momentum', 'position')
        ecs.run_system(dt, ecsc.sprite_system, 'sprite', 'position')
        ecs.run_system(dt, ecsc.deadzone_system, 'world', 'position', container=self.deadzone)
        ecs.run_system(dt, ecsc.lifetime_system, 'lifetime')

    def draw(self, screen):
        def lifetime_display(dt, eid, lifetime_display, lifetime, position):
            img = self.persist.font.render(f'{lifetime.remaining:.3f}', True, 'white')
            rect = img.get_rect(center=position)
            screen.blit(img, rect)

        def circle_system(dt, eid, circle, position):
            pygame.draw.circle(screen, circle[1], position, circle[0], width=1)

        runtime = pygame.time.get_ticks() / 1000
        sprites = len(sprite_group)
        fps = self.app.clock.get_fps()

        if fps:
            bgcolor = self.bgcolor.lerp(self.bgcrit, 1 - (min(self.app.fps, fps) / self.app.fps))
        else:
            bgcolor = self.bgcolor

        screen.fill(bgcolor)

        sprite_group.draw(screen)
        self.group.draw(screen)

        # ecs.run_system(0, lifetime_display, 'lifetime-display', 'lifetime', 'position')
        ecs.run_system(0, circle_system, 'circle', 'position')

        if fps and sprites > 100 and fps < self.stats['slowest'][0]:
            self.stats['slowest'][0] = int(fps)
            self.stats['slowest'][1] = sprites
        if sprites > self.stats['most'][1] and fps > 58:
            self.stats['most'][0] = int(fps)
            self.stats['most'][1] = sprites

        pygame.display.set_caption(f'{self.app. title} - {runtime=:.2f}  {fps=:.2f}  {sprites=}')
