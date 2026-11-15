import pygame

from core.board import Board
from gui.coords import pixel_to_square, square_to_rect

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
    elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
      self._cancel()
    elif event.type == pygame.WINDOWFOCUSLOST:
      self._cancel()

  def _on_press(self, pos: tuple[int, int]) -> None:
    sq = pixel_to_square(pos)
    if sq is None:
      self._cancel()
      return

    target_piece = self.board.squares[sq]

    # A piece is selected and this press is on a target square: click-to-move.
    if self.selected is not None and sq != self.selected:
      selected_piece = self.board.squares[self.selected]
      if target_piece is None or not same_color(target_piece, selected_piece):
        self.board.apply_move(self.selected, sq)
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

    self.board.apply_move(from_sq, sq)
    self.selected = None

  def _cancel(self) -> None:
    self.selected = None
    self.drag_square = None

  def drag_center(self) -> tuple[int, int]:
    return (self.drag_pos[0] - self.drag_offset[0], self.drag_pos[1] - self.drag_offset[1])