Piece = str | None
Move = tuple[int, int] # (from_square, to_square)

START_PLACEMENT = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR"
PIECE_LETTERS = set("PNBRQKpnbrqk")

class Board:
  def __init__(self) -> None:
    self.squares: list[Piece] = [None] * 64
    self.history: list[tuple[list[Piece], Move | None]] = []
    self.last_move: Move | None = None
    self.load_placement(START_PLACEMENT)

  def load_placement(self, placement: str) -> None:
    """Load the piece-placement part of a FEN"""
    placement = placement.split()[0]
    rows = placement.split("/")
    if len(rows) != 8:
      raise ValueError(f"FEN placement needs 8 ranks, got {len(rows)}")

    squares: list[Piece] = [None] * 64
    for i, row in enumerate(rows):
      rank = 7 - i
      file = 0
      for ch in row:
        if ch.isdigit():
          file += int(ch)
        elif ch in PIECE_LETTERS:
          if file > 7:
            raise ValueError(f"Too many squares in rank {rank + 1}: {row!r}")
          squares[rank * 8 + file] = ch
          file += 1
        else:
          raise ValueError(f"Invalid character {ch!r} in FEN placement")
      if file != 8:
        raise ValueError(f"Rank {rank + 1} has {file} squares, expected 8: {row!r}")

    self.squares = squares
    self.history.clear()
    self.last_move = None

  def to_placement(self) -> str:
    """Export the board as a FEN placement string."""
    rows = []
    for rank in range(7, -1, -1):
      row, empty = "", 0
      for file in range(8):
        piece = self.squares[rank * 8 + file]
        if piece is None:
          empty += 1
        else:
          if empty:
            row += str(empty)
            empty = 0
          row += piece
      if empty:
        row += str(empty)
      rows.append(row)
    return "/".join(rows)