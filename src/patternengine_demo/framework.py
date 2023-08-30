import pygame

from abc import ABC, abstractmethod
from types import SimpleNamespace

__all__ = ['App', 'GameState']

QUIT = 'QUIT'


class App:
    """A pygame application framework.

    This class provides basic initialization, a classical game loop (event
    dispatching/update/draw), and a State system with GameState classes to be
    implemented by the user.

    Parameters
    ----------
    title : str
        The title in the window border

        This is initialized once and can be overwritten with FPS or debugging
        info from the GameState. (See attributes)

    screen : pygame.rect.Rect
        A pygame rect representing the screen.  Only the size is used by the
        App framework, but the location might be used by the GameState, e.g. to
        position a viewport camera.

    FPS : int
        The wanted frames per second for the game loop.

    Attributes
    ----------
    screen : pygame.display.Surface
        The result of the pygame.display.set_mode() call.
    rect:
        The rect of the screen surface.  Should be identical with the `SCREEN`
        rect from the class initialization.
    clock:
        The `pygame.time.Clock` object.  Can be queried to e.g. get the real
        framerate.
    fps : int
        Copy of `fps` from the class initialization.
    running : bool = True
        Set this to `False` from the GameState to end the application.

    """
    def __init__(self, title, screen, fps):
        """Initialize the app framework."""
        self.title = title
        self.screen = pygame.display.set_mode(screen.size)
        pygame.display.set_caption(self.title)
        self.rect = self.screen.get_rect()
        self.clock = pygame.time.Clock()
        self.fps = fps
        self.running = True

        self._states = None
        self._state = None
        self._state_stack = []
        self._dt_max = 3 / fps

        pygame.init()

    # The persist stuff is stolen from here:
    # https://gist.github.com/iminurnamez/8d51f5b40032f106a847
    def next_state(self, state, persist):
        """Switch state.

        If the new state is None, return to a previously stacked state, if one
        exists, otherwise end the app.
        """
        # If we don't have a follow up state, but there are states in the
        # stack, continue these, otherwise finish the game loop.
        if state is None:
            if self._state_stack:
                self._state = self._state_stack.pop()
                return
            else:
                self.running = False
                return

        # We do have a follow up state
        self._state = self._states[state]
        self._state.reset(persist)

    def dispatch_events(self):
        """Delegate events to current state."""
        for e in pygame.event.get():
            self._state.dispatch_event(e)

    def update(self, dt):
        """Call update method of current state.

        If the current state running property is False, exit the app.

        If the current state returns a tuple of (next_state, persist), switch
        states.
        """
        res = self._state.update(dt)

        if not self._state.running:
            self.running = False
            return

        if res:
            next_state, persist = res
            self.next_state(next_state, persist)

    def draw(self):
        """Call draw method of current state."""
        self._state.draw(self.screen)

    def run(self, state, states):
        """The game loop."""

        self._states = states
        self._state = self._states[state]
        while self.running:
            dt = min(self.clock.tick(self.fps) / 1000.0, self._dt_max)

            self.dispatch_events()
            self.update(dt)
            self.draw()

            pygame.display.flip()

        pygame.quit()

    def push(self, substate):
        """push the current state onto the stack, run the new one.

            self.persist.state.push(pause_screen)

        once the sub state finishes, control is returned to the previous state.
        persist is merged to provide results.
        """

        self._state_stack.append(self._state)
        self._state = substate


class GameState(ABC):
    """The base class for game states

    Calling super().__init__(app, persist, parent) is required for this to work
    if you run your own __init__.

    reset(persist=None):

        To avoid reinstantiating the state class again and again, you can
        create an instance at the beginning of the application once, and in
        repeated uses, the reset function will be called every time the state
        starts.  Optionally, you can put fresh 'persist' data in here.

    dispatch_event(self, e):

        Note, if you decide to not overwrite this method, pygame.QUIT will be
        handled and pygame.K_ESCAPE will end the application.

        If you overwrite this method, either call super().dispatch_event(e) to
        keep this behaviour, or replace it with your own.

    @abstractmethod
    update(dt), draw(screen):

        While the basic handling of events is already covered by the famework,
        every game state must have these two.

        dt is delta-time from the game loop
        screen is the primary display

        The display is flipped by the framework, but an initial fill with e.g.
        black is the job of the state class.
    """

    def __init__(self, app, persist, parent=None):
        """Initialize a game state.

        Arguments:
            persist - any container type that can transfer data between your
                      game states.  A dict, a SimpleNamespace or a state class
                      come to mind.  The persist object is handed from state to
                      state.
            parent - feature in progress, please ignore
        """

        self.app = app
        self.persist = persist if persist is not None else SimpleNamespace()
        self.parent = parent
        self.font = pygame.font.Font(None)
        self.running = True

    def reset(self, persist=None):
        """Reset settings when re-running."""
        self.running = True
        if persist:
            self.persist = persist

    def dispatch_event(self, e):
        """Handle user events"""
        if (e.type == pygame.QUIT or
                e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
            self.running = False

    @abstractmethod
    def update(self, dt):
        """Update frame by delta time dt."""
        raise NotImplementedError

    @abstractmethod
    def draw(self, screen):
        """Draw current frame to surface screen."""
        raise NotImplementedError
