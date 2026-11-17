import pygame

from core.board import Board
from gui import constants as C
from gui.coords import pixel_to_square, square_to_rect
from gui.input_handler import InputHandler

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
    self.light_square_overlay = self._overlay(C.HIGHLIGHT_LIGHT)
    self.dark_square_overlay = self._overlay(C.HIGHLIGHT_DARK)
    self.drop_target_overlay = self._overlay(C.HIGHLIGHT_DROP_TARGET, C.DROP_TARGET_WIDTH)
    self.check_flash_overlay = self._overlay(C.CHECK_FLASH_COLOR)

    self.move_dot = self._circle(C.HINT_DOT_RADIUS)
    self.capture_ring = self._circle(C.SQUARE_SIZE // 2, C.HINT_RING_WIDTH)

  def draw(self, board: Board, ui: InputHandler, fps: float) -> None:
    self.screen.fill(C.BACKGROUND)
    self._draw_squares()
    self._draw_highlights(board, ui)
    self._draw_check_flash(ui)
    self._draw_pieces(board, skip=ui.drag_square)
    self._draw_move_hints(board, ui)
    self._draw_panel(fps)
    self._draw_dragged_piece(board, ui)

  @staticmethod
  def is_light(sq:int) -> bool:
    return (sq % 8 + sq // 8) % 2 == 1

  @staticmethod
  def _circle(radius: int, width: int = 0) -> pygame.Surface:
    """Square-sized surface with a centered translucent circle: filled, or a ring if width > 0."""
    surf = pygame.Surface((C.SQUARE_SIZE, C.SQUARE_SIZE), pygame.SRCALPHA)
    pygame.draw.circle(surf, C.HINT_COLOR, surf.get_rect().center, radius, width)
    return surf

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

  @staticmethod
  def _overlay(rgba: tuple[int, int, int, int], border: int = 0) -> pygame.Surface:
    """Square-sized translucent surface: filled, or only an outline if border > 0."""
    surf = pygame.Surface((C.SQUARE_SIZE, C.SQUARE_SIZE), pygame.SRCALPHA)
    pygame.draw.rect(surf, rgba, surf.get_rect(), border)
    return surf

  # Board
  def _draw_squares(self) -> None:
    for sq in range(64):
      color = C.LIGHT_SQUARE if self.is_light(sq) else C.DARK_SQUARE
      pygame.draw.rect(self.screen, color, square_to_rect(sq))

  def _draw_highlights(self, board: Board, ui: InputHandler) -> None:
    squares = set(board.last_move or ())
    if ui.selected is not None:
      squares.add(ui.selected)
    for sq in squares:
      self._highlight_square(sq)

    if ui.drag_square is not None:
      hover = pixel_to_square(ui.drag_pos)
      if hover is not None and hover != ui.drag_square:
        self.screen.blit(self.drop_target_overlay, square_to_rect(hover))

  def _highlight_square(self, sq: int) -> None:
    overlay = self.light_square_overlay if self.is_light(sq) else self.dark_square_overlay
    self.screen.blit(overlay, square_to_rect(sq))

  def _draw_pieces(self, board: Board, skip: int | None = None) -> None:
    for sq, piece in enumerate(board.squares):
      if piece is None or sq == skip:
        continue
      img = self.piece_images[piece]
      self.screen.blit(img, img.get_rect(center=square_to_rect(sq).center))

  def _draw_dragged_piece(self, board: Board, ui: InputHandler) -> None:
    if ui.drag_square is None:
      return
    piece = board.squares[ui.drag_square]
    if piece is None:
      return
    img = self.piece_images[piece]
    self.screen.blit(img, img.get_rect(center=ui.drag_center()))

  # Panel
  def _draw_panel(self, fps: float) -> None:
    pygame.draw.rect(self.screen, C.PANEL_BG, self.panel_rect)
    lines = [C.WINDOW_TITLE, f"FPS: {fps:.0f}"]
    x, y = self.panel_rect.x + 16, 16
    for line in lines:
      surf = self.panel_font.render(line, True, C.PANEL_TEXT)
      self.screen.blit(surf, (x, y))
      y += surf.get_height() + 8

  def _draw_move_hints(self, board: Board, ui: InputHandler) -> None:
    """Dot on each empty legal target of the selected piece, ring on each legal capture."""
    if ui.selected is None:
      return
    piece = board.squares[ui.selected]

    if piece is None:
      return
    for move in board.legal_moves_from(ui.selected):
      hint = self.capture_ring if board.squares[move.to_sq] is not None else self.move_dot
      self.screen.blit(hint, square_to_rect(move.to_sq))

  def _draw_check_flash(self, ui: InputHandler) -> None:
    sq = ui.flashing_square()
    if sq is not None:
      self.screen.blit(self.check_flash_overlay, square_to_rect(sq))