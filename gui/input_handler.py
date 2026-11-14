import pygame

from core.board import Board
from gui.coords import pixel_to_square

def same_color(a: str, b: str) -> bool:
  return a.isupper() == b.isupper()

class InputHandler:
  def __init__(self, board: Board) -> None:
    self.board = board
    self.flipped = False
    self.selected: int | None = None

  def handle(self, event: pygame.event.Event) -> None:
    if event.type == pygame.MOUSEBUTTONDOWN:
      if event.button == 1:
        self._on_left_click(event.pos)
      elif event.button == 3:
        self.selected = None
    elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
      self.selected = None

  def _on_left_click(self, pos: tuple[int, int]) -> None:
    sq = pixel_to_square(pos)
    if sq is None:
      self.selected = None
      return

    piece = self.board.squares[sq]

    # Nothing selected yet: select a piece, ignore empty squares.
    if self.selected is None:
      if piece is not None:
        self.selected = sq
      return

    # Clicked the selected square again: deselect.
    if sq == self.selected:
      self.selected = None
      return

    # Clicked another piece of the same color: switch selection.
    selected_piece = self.board.squares[self.selected]
    if piece is not None and same_color(piece, selected_piece):
      self.selected = sq
      return

    # Empty square or opposite color: move (capturing if occupied).
    self.board.apply_move(self.selected, sq)
    self.selected = None