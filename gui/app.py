import pygame

from core.board import Board
from gui import constants as C
from gui.input_handler import InputHandler
from gui.renderer import Renderer

class App:
  def __init__(self) -> None:
    pygame.init()
    pygame.display.set_caption(C.WINDOW_TITLE)
    self.screen = pygame.display.set_mode((C.WINDOW_WIDTH, C.WINDOW_HEIGHT))
    self.clock = pygame.time.Clock()
    self.running = False

    self.board = Board()
    self.input = InputHandler(self.board)
    self.renderer = Renderer(self.screen)

  def run(self) -> None:
    self.running = True
    try:
      while self.running:
        self._handle_events()
        self._update()
        self.renderer.draw(self.clock.get_fps())
        pygame.display.flip()
        self.clock.tick(C.FPS)
    finally:
      pygame.quit()

  def _handle_events(self) -> None:
    for event in pygame.event.get():
      if event.type == pygame.QUIT:
        self.running = False
      else:
        self.input.handle(event)

  def _update(self) -> None:
    pass