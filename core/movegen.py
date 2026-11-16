from __future__ import annotations

from typing import TYPE_CHECKING, NamedTuple

if TYPE_CHECKING:
  from core.board import Board

Piece = str | None

class Move(NamedTuple):
  from_sq: int
  to_sq: int

# Precomputed tables
def _offset(sq: int, df: int, dr: int) -> int | None:
  """Square reached by moving df files and dr ranks, or None if off the board."""
  f, r = sq % 8 + df, sq // 8 + dr
  return r * 8 + f if 0 <= f < 8 and 0 <= r < 8 else None

KNIGHT_STEPS = [(1, 2), (2, 1), (2, -1), (1, -2), (-1, -2), (-2, -1), (-2, 1), (-1, 2)]
KING_STEPS = [(1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)]

def _jump_table(steps: list[tuple[int, int]]) -> list[list[int]]:
  table = []
  for sq in range(64):
    targets = [_offset(sq, df, dr) for df, dr in steps]
    table.append([t for t in targets if t is not None])
  return table

KNIGHT_TARGETS = _jump_table(KNIGHT_STEPS)
KING_TARGETS = _jump_table(KING_STEPS)

# Helpers
def is_white(piece: str) -> bool:
  return piece.isupper()

def _is_enemy(piece: Piece, white: bool) -> bool:
  return piece is not None and is_white(piece) != white

def _is_friend(piece: Piece, white: bool) -> bool:
  return piece is not None and is_white(piece) == white

# Move generation
def _pawn_moves(board: Board, sq: int) -> list[Move]:
  """One step forward, two from the start rank, diagonal captures."""
  squares = board.squares
  white = squares[sq].isupper()
  dr = 1 if white else -1
  start_rank = 1 if white else 6
  moves: list[Move] = []

  one = _offset(sq, 0, dr)
  if one is None:
    return moves

  if squares[one] is None:
    moves.append(Move(sq, one))
    two = _offset(sq, 0, 2 * dr)
    if sq // 8 == start_rank and squares[two] is None:
      moves.append(Move(sq, two))

  for df in (-1, 1):
    t = _offset(sq, df, dr)
    if t is not None and _is_enemy(squares[t], white):
      moves.append(Move(sq, t))
  return moves

def _jump_moves(squares: list[Piece], sq: int, targets: list[int]) -> list[Move]:
  white = squares[sq].isupper()
  moves: list[Move] = []
  for t in targets:
    if not _is_friend(squares[t], white):
      moves.append(Move(sq, t))
  return moves

def free_moves(board: Board, sq: int) -> list[Move]:
  """Placeholder for pieces without a rule yet."""
  squares = board.squares
  white = squares[sq].isupper()
  return [Move(sq, t) for t in range(64)
          if t != sq and (squares[t] is None or _is_enemy(squares[t], white))]

def pseudo_legal_moves(board: Board) -> list[Move]:
  """Moves for the side to move, ignoring whether the own king is left in check."""
  white = board.turn == "w"
  squares = board.squares
  moves: list[Move] = []

  for sq, piece in enumerate(squares):
    if piece is None or is_white(piece) != white:
      continue
    if piece.upper() == "P":
      moves.extend(_pawn_moves(board, sq))
    elif piece.upper() == "N":
      moves.extend(_jump_moves(squares, sq, KNIGHT_TARGETS[sq]))
    elif piece.upper() == "K":
      moves.extend(_jump_moves(squares, sq, KING_TARGETS[sq]))
    else:
      moves.extend(free_moves(board, sq))
  return moves

def legal_moves(board: Board) -> list[Move]:
  return pseudo_legal_moves(board)