import pygame

from core.board import Board
from gui import constants as C

PIECE_FILES = {
  "P": "PawnW",   "p": "PawnB",
  "N": "KnightW", "n": "KnightB",
  "B": "BishopW", "b": "BishopB",
  "R": "RookW",   "r": "RookB",
  "Q": "QueenW",  "q": "QueenB",
  "K": "KingW",   "k": "KingB",
}

class Renderer:
  def __init__(self, screen: pygame.Surface) -> None:
    self.screen = screen
    self.panel_font = pygame.font.Font(None, C.PANEL_FONT_SIZE)
    self.board_rect = pygame.Rect(C.BOARD_ORIGIN, (C.BOARD_SIZE, C.BOARD_SIZE))
    self.panel_rect = pygame.Rect(
      C.BOARD_ORIGIN[0] + C.BOARD_SIZE, 0, C.PANEL_WIDTH, C.WINDOW_HEIGHT
    )
    self.piece_images = self._load_piece_images()

  def draw(self, board: Board, fps: float) -> None:
    self.screen.fill(C.BACKGROUND)
    self._draw_squares()
    self._draw_pieces(board)
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

  # Asset
  def _load_piece_images(self) -> dict[str, pygame.Surface]:
    target = C.SQUARE_SIZE - 2 * C.PIECE_PADDING
    images: dict[str, pygame.Surface] = {}
    missing = []

    for letter, name in PIECE_FILES.items():
      path = C.PIECES_DIR / f"{name}.png"
      if not path.exists():
        missing.append(path.name)
        continue
      img = pygame.image.load(path).convert_alpha()
      scale = target / max(img.get_width(), img.get_height())
      size = (round(img.get_width() * scale), round(img.get_height() * scale))
      images[letter] = pygame.transform.smoothscale(img, size)

    if missing:
      raise FileNotFoundError(f"Missing piece images in {C.PIECES_DIR}: {', '.join(missing)}")
    return images

  # Board
  def _draw_squares(self) -> None:
    for sq in range(64):
      color = C.LIGHT_SQUARE if self.is_light(sq) else C.DARK_SQUARE
      pygame.draw.rect(self.screen, color, self.square_to_rect(sq))

  def _draw_pieces(self, board: Board) -> None:
    for sq, piece in enumerate(board.squares):
      if piece is None:
        continue
      img = self.piece_images[piece]
      self.screen.blit(img, img.get_rect(center=self.square_to_rect(sq).center))

  # Panel
  def _draw_panel(self, fps: float) -> None:
    pygame.draw.rect(self.screen, C.PANEL_BG, self.panel_rect)
    lines = [C.WINDOW_TITLE, f"FPS: {fps:.0f}"]
    x, y = self.panel_rect.x + 16, 16
    for line in lines:
      surf = self.panel_font.render(line, True, C.PANEL_TEXT)
      self.screen.blit(surf, (x, y))
      y += surf.get_height() + 8