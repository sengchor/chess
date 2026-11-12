Piece = str | None
Move = tuple[int, int] # (from_square, to_square)

class Board:
  def __init__(self) -> None:
    self.squares: list[Piece] = [None] * 64
    self.history: list[tuple[list[Piece], Move | None]] = []
    self.last_move: Move | None = None