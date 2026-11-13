import pygame

from gui import constants as C

class Renderer:
  def __init__(self, screen: pygame.Surface) -> None:
    self.screen = screen
    self.panel_font = pygame.font.Font(None, C.PANEL_FONT_SIZE)
    self.board_rect = pygame.Rect(C.BOARD_ORIGIN, (C.BOARD_SIZE, C.BOARD_SIZE))
    self.panel_rect = pygame.Rect(
      C.BOARD_ORIGIN[0] + C.BOARD_SIZE, 0, C.PANEL_WIDTH, C.WINDOW_HEIGHT
    )

  def draw(self, fps: float) -> None:
    self.screen.fill(C.BACKGROUND)
    self._draw_squares()
    self._draw_panel(fps)

  # Coordinates
  def square_to_rect(self, sq: int) -> pygame.Rect:
    file, rank = sq % 8, sq // 8
    col = file
    row = 7 - rank
    x = C.BOARD_ORIGIN[0] + col * C.SQUARE_SIZE
    y = C.BOARD_ORIGIN[1] + row * C.SQUARE_SIZE
    return pygame.Rect(x, y, C.SQUARE_SIZE, C.SQUARE_SIZE)

  @staticmethod
  def is_light(sq:int) -> bool:
    return (sq % 8 + sq // 8) % 2 == 1

  # Board
  def _draw_squares(self) -> None:
    for sq in range(64):
      color = C.LIGHT_SQUARE if self.is_light(sq) else C.DARK_SQUARE
      pygame.draw.rect(self.screen, color, self.square_to_rect(sq))

  # Panel
  def _draw_panel(self, fps: float) -> None:
    pygame.draw.rect(self.screen, C.PANEL_BG, self.panel_rect)
    lines = [C.WINDOW_TITLE, f"FPS: {fps:.0f}"]
    x, y = self.panel_rect.x + 16, 16
    for line in lines:
      surf = self.panel_font.render(line, True, C.PANEL_TEXT)
      self.screen.blit(surf, (x, y))
      y += surf.get_height() + 8