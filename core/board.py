from core import movegen
from core.movegen import Move, Piece

START_PLACEMENT = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR"
PIECE_LETTERS = set("PNBRQKpnbrqk")

# Moving from or capturing on these squares removes these castling rights.
CASTLING_SQUARES = {4: "KQ", 60: "kq", 0: "Q", 7: "K", 56: "q", 63: "k"}

class Board:
  def __init__(self) -> None:
    self.squares: list[Piece] = [None] * 64
    self.turn = "w"
    self.castling = "KQkq"
    self.ep_square: int | None = None
    self.history: list[tuple] = []
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

  def legal_moves_from(self, sq: int) -> list[Move]:
    """Legal moves of the piece on `sq`"""
    return [m for m in movegen.legal_moves(self) if m.from_sq == sq]

  def is_promotion(self, from_sq: int, to_sq: int) -> bool:
    return any(
      m.to_sq == to_sq and m.promotion is not None
      for m in self.legal_moves_from(from_sq)
    )

  def in_check(self) -> bool:
    return movegen.in_check(self.squares, self.turn == "w")

  def king_square(self) -> int | None:
    return movegen.king_square(self.squares, self.turn == "w")

  def apply_move(self, from_sq: int, to_sq: int, promotion: str | None = None) -> bool:
    """The single entry point for moves."""
    promotion = (promotion or "q").lower()
    for move in movegen.legal_moves(self):
      if move.from_sq == from_sq and move.to_sq == to_sq and move.promotion in (None, promotion):
        break
    else:
      return False

    piece = self.squares[from_sq]
    self.history.append((self.squares.copy(), self.turn, self.castling, self.ep_square, self.last_move))
    self.squares = movegen.squares_after(self.squares, move, self.ep_square)

    # A pawn that just moved two squares can be captured en passant on the square
    if piece in ("P", "p") and abs(to_sq - from_sq) == 16:
      self.ep_square = (from_sq + to_sq) // 2
    else:
      self.ep_square = None

    # Update castling rights when the King or a Rook moves, or when a Rook is captured
    for sq in (from_sq, to_sq):
      for right in CASTLING_SQUARES.get(sq, ""):
        self.castling = self.castling.replace(right, "")

    self.last_move = move
    self.turn = "b" if self.turn == "w" else "w"
    return True