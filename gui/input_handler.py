import pygame

from core.board import Board
from core.movegen import PROMOTIONS
from gui.coords import pixel_to_square, square_to_rect
from gui import constants as C

def same_color(a: str, b: str) -> bool:
  return a.isupper() == b.isupper()

class InputHandler:
  def __init__(self, board: Board) -> None:
    self.board = board
    self.flipped = False
    self.selected: int | None = None
    self.drag_square: int | None = None
    self.drag_pos: tuple[int, int] = (0, 0)
    self.drag_offset: tuple[int, int] = (0, 0)
    self._was_selected = False
    self.flash_square: int | None = None
    self.flash_start = 0
    self.promotion: tuple[int, int] | None = None

  def handle(self, event: pygame.event.Event) -> None:
    if event.type == pygame.MOUSEBUTTONDOWN:
      if event.button == 1:
        self._on_press(event.pos)
      elif event.button == 3:
        self._cancel()
    elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
      self._on_release(event.pos)
    elif event.type == pygame.MOUSEMOTION and self.drag_square is not None:
      self.drag_pos = event.pos
    elif event.type == pygame.KEYDOWN:
      if event.key == pygame.K_ESCAPE:
        self._cancel()
      elif self.promotion is not None and len(event.unicode) == 1 and event.unicode.lower() in PROMOTIONS:
        self._finish_promotion(event.unicode.lower())
    elif event.type == pygame.WINDOWFOCUSLOST:
      self._cancel()

  def _on_press(self, pos: tuple[int, int]) -> None:
    sq = pixel_to_square(pos)

    if self.promotion is not None:
      for choice_sq, piece in self.promotion_choices():
        if sq == choice_sq:
          self._finish_promotion(piece)
          return
      self.promotion = None
      return

    if sq is None:
      self._cancel()
      return

    target_piece = self.board.squares[sq]

    # A piece is selected and this press is on a target square: click-to-move.
    if self.selected is not None and sq != self.selected:
      selected_piece = self.board.squares[self.selected]
      if target_piece is None or not same_color(target_piece, selected_piece):
        self._try_move(self.selected, sq)
        self.selected = None
        return

    # empty square, nothing selected
    if target_piece is None:
      self.selected = None
      return

    # Pressed a piece: select it and pick it up.
    self._was_selected = sq == self.selected
    self.selected = sq
    self.drag_square = sq
    self.drag_pos = pos
    cx, cy = square_to_rect(sq).center
    self.drag_offset = (pos[0] - cx, pos[1] - cy)

  def _on_release(self, pos: tuple[int, int]) -> None:
    if self.drag_square is None:
      return

    from_sq = self.drag_square
    self.drag_square = None
    sq = pixel_to_square(pos)

    # drop off the board: snap back
    if sq is None:
      self.selected = None
      return

    # press + release on the same square
    if sq == from_sq:
      if self._was_selected:
        self.selected = None
      return

    # dropped on own piece: snap back, stay selected
    target = self.board.squares[sq]
    if target is not None and same_color(target, self.board.squares[from_sq]):
      return

    self._try_move(from_sq, sq)
    self.selected = None

  def _cancel(self) -> None:
    self.selected = None
    self.drag_square = None
    self.promotion = None

  def drag_center(self) -> tuple[int, int]:
    return (self.drag_pos[0] - self.drag_offset[0], self.drag_pos[1] - self.drag_offset[1])

  def _try_move(self, from_sq: int, to_sq: int) -> bool:
    """Ask the board to make a move. If it's illegal while in check, flash the king."""
    if self.board.is_promotion(from_sq, to_sq):
      self.promotion = (from_sq, to_sq)
      self.flash_square = None
      return True
    if self.board.apply_move(from_sq, to_sq):
      self.flash_square = None
      return True
    if self.board.in_check():
      self.flash_square = self.board.king_square()
      self.flash_start = pygame.time.get_ticks()
    return False

  def flashing_square(self) -> int | None:
    if self.flash_square is None:
      return None
    elapsed = pygame.time.get_ticks() - self.flash_start
    if elapsed >= C.CHECK_FLASH_MS:
      self.flash_square = None
      return None
    phase = elapsed * C.CHECK_FLASH_BLINKS * 2 // C.CHECK_FLASH_MS
    return self.flash_square if phase % 2 == 0 else None

  # Promotion
  def promotion_choices(self) -> list[tuple[int, str]]:
    if self.promotion is None:
      return []
    to_sq = self.promotion[1]
    white = self.board.turn == "w"
    step = -8 if white else 8
    letters = PROMOTIONS.upper() if white else PROMOTIONS
    return [(to_sq + i * step, letter) for i, letter in enumerate(letters)]

  def _finish_promotion(self, piece: str) -> None:
    from_sq, to_sq = self.promotion
    self.promotion = None
    self.board.apply_move(from_sq, to_sq, piece)