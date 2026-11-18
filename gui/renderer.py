import pygame

from core.board import Board
from gui import constants as C
from gui.coords import pixel_to_square, square_to_rect
from gui.input_handler import InputHandler
from core import movegen

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

    self.promotion_dim = pygame.Surface((C.BOARD_SIZE, C.BOARD_SIZE), pygame.SRCALPHA)
    self.promotion_dim.fill(C.PROMO_DIM_COLOR)

    self.win_badge = self._badge(C.WIN_BADGE_COLOR)
    self.lose_badge = self._badge(C.LOSE_BADGE_COLOR)
    self.draw_badge = self._badge(C.DRAW_BADGE_COLOR)

  def draw(self, board: Board, ui: InputHandler, fps: float) -> None:
    self.screen.fill(C.BACKGROUND)
    self._draw_squares()
    self._draw_highlights(board, ui)
    self._draw_check_flash(ui)
    self._draw_pieces(board, skip=ui.drag_square)
    self._draw_result_badges(board)
    self._draw_move_hints(board, ui)
    self._draw_promotion_picker(ui)
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
    squares: set[int] = set()
    if board.last_move is not None:
      squares.update((board.last_move.from_sq, board.last_move.to_sq))
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

    targets = {move.to_sq for move in board.legal_moves_from(ui.selected)}
    for to_sq in targets:
      hint = self.capture_ring if board.squares[to_sq] is not None else self.move_dot
      self.screen.blit(hint, square_to_rect(to_sq))

  def _draw_promotion_picker(self, ui: InputHandler) -> None:
    """Dim the board and show a column of promotion pieces over the target file."""
    choices = ui.promotion_choices()
    if not choices:
      return
    self.screen.blit(self.promotion_dim, self.board_rect.topleft)

    column = square_to_rect(choices[0][0]).union(square_to_rect(choices[-1][0]))
    pygame.draw.rect(self.screen, C.PROMO_BG, column, border_radius=C.PROMO_RADIUS)

    mouse = pygame.mouse.get_pos()
    for sq, piece in choices:
      rect = square_to_rect(sq)
      if rect.collidepoint(mouse):
        pygame.draw.rect(self.screen, C.PROMO_HOVER_BG, rect, border_radius=C.PROMO_RADIUS)
      img = self.piece_images[piece]
      self.screen.blit(img, img.get_rect(center=rect.center))

  def _draw_check_flash(self, ui: InputHandler) -> None:
    sq = ui.flashing_square()
    if sq is not None:
      self.screen.blit(self.check_flash_overlay, square_to_rect(sq))

  @staticmethod
  def _badge(color: tuple[int, int, int]) -> pygame.Surface:
    r, b = C.BADGE_RADIUS, C.BADGE_BORDER
    size = 2 * (r + b)
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    center = (size // 2, size // 2)
    pygame.draw.circle(surf, C.BADGE_BORDER_COLOR, center, r + b)
    pygame.draw.circle(surf, color, center, r)
    return surf

  def _draw_result_badges(self, board: Board) -> None:
    if board.is_stalemate():
      badges = ((self.draw_badge, True), (self.draw_badge, False))
    else:
      winner = board.winner()
      if winner is None:
        return
      badges = ((self.win_badge, winner == "w"), (self.lose_badge, winner != "w"))

    for badge, white in badges:
      k = movegen.king_square(board.squares, white)
      if k is not None:
        rect = square_to_rect(k)
        self.screen.blit(badge, badge.get_rect(topright=(rect.right, rect.top)))