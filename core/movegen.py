from __future__ import annotations

from typing import TYPE_CHECKING, NamedTuple

if TYPE_CHECKING:
  from core.board import Board

Piece = str | None
PROMOTIONS = "qrbn"

class Move(NamedTuple):
  from_sq: int
  to_sq: int
  promotion: str | None = None

# Precomputed tables
def _offset(sq: int, df: int, dr: int) -> int | None:
  """Square reached by moving df files and dr ranks, or None if off the board."""
  f, r = sq % 8 + df, sq // 8 + dr
  return r * 8 + f if 0 <= f < 8 and 0 <= r < 8 else None

KNIGHT_STEPS = [(1, 2), (2, 1), (2, -1), (1, -2), (-1, -2), (-2, -1), (-2, 1), (-1, 2)]
KING_STEPS = [(1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)]
ROOK_DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1)]
BISHOP_DIRS = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
QUEEN_DIRS = ROOK_DIRS + BISHOP_DIRS

def _jump_table(steps: list[tuple[int, int]]) -> list[list[int]]:
  table = []
  for sq in range(64):
    targets = [_offset(sq, df, dr) for df, dr in steps]
    table.append([t for t in targets if t is not None])
  return table

def _ray_table(dirs: list[tuple[int, int]]) -> list[list[list[int]]]:
  """For each square, one ray (list of squares, nearest first) per direction."""
  table = []
  for sq in range(64):
    rays = []
    for df, dr in dirs:
      rays.append(_ray(sq, df, dr))
    table.append(rays)
  return table

def _ray(sq: int, df: int, dr: int) -> list[int]:
  ray = []
  t = _offset(sq, df, dr)
  while t is not None:
    ray.append(t)
    t = _offset(t, df, dr)
  return ray

KNIGHT_TARGETS = _jump_table(KNIGHT_STEPS)
KING_TARGETS = _jump_table(KING_STEPS)
ROOK_RAYS = _ray_table(ROOK_DIRS)
BISHOP_RAYS = _ray_table(BISHOP_DIRS)
QUEEN_RAYS = _ray_table(QUEEN_DIRS)

# Helpers
def is_white(piece: str) -> bool:
  return piece.isupper()

def _is_enemy(piece: Piece, white: bool) -> bool:
  return piece is not None and is_white(piece) != white

def _is_friend(piece: Piece, white: bool) -> bool:
  return piece is not None and is_white(piece) == white

def king_square(squares: list[Piece], white: bool) -> int | None:
  try:
    return squares.index("K" if white else "k")
  except ValueError:
    return None

# Attacks
def is_attacked(squares: list[Piece], sq: int, by_white: bool) -> bool:
  """Is `sq` attacked by any piece of the given color?"""
  pawn, knight, bishop, rook, queen, king = ("PNBRQK" if by_white else "pnbrqk")

  # pawn attack
  dr = -1 if by_white else 1
  for df in (-1, 1):
    t = _offset(sq, df, dr)
    if t is not None and squares[t] == pawn:
      return True

  for t in KNIGHT_TARGETS[sq]:
    if squares[t] == knight:
      return True

  for t in KING_TARGETS[sq]:
    if squares[t] == king:
      return True

  for ray in ROOK_RAYS[sq]:
    for t in ray:
      p = squares[t]
      if p is not None:
        if p == rook or p == queen:
          return True
        break

  for ray in BISHOP_RAYS[sq]:
    for t in ray:
      p = squares[t]
      if p is not None:
        if p == bishop or p == queen:
          return True
        break

  return False

def in_check(squares: list[Piece], white: bool) -> bool:
  k = king_square(squares, white)
  return k is not None and is_attacked(squares, k, not white)

# Making a move on a square list
def squares_after(squares: list[Piece], move: Move) -> list[Piece]:
  """Simulate a chess move without modifying the original board."""
  new = squares.copy()
  piece = new[move.from_sq]
  new[move.from_sq] = None

  if move.promotion:
    piece = move.promotion.upper() if is_white(piece) else move.promotion.lower()

  new[move.to_sq] = piece
  return new

# Move generation
def _pawn_moves(board: Board, sq: int) -> list[Move]:
  """One step forward, two from the start rank, diagonal captures."""
  squares = board.squares
  white = squares[sq].isupper()
  dr = 1 if white else -1
  start_rank = 1 if white else 6
  promo_rank = 7 if white else 0
  moves: list[Move] = []

  def add(to: int) -> None:
    if to // 8 == promo_rank:
      moves.extend(Move(sq, to, p) for p in PROMOTIONS)
    else:
      moves.append(Move(sq, to))

  one = _offset(sq, 0, dr)
  if one is not None and squares[one] is None:
    add(one)
    two = _offset(sq, 0, 2 * dr)
    if sq // 8 == start_rank and squares[two] is None:
      moves.append(Move(sq, two))

  for df in (-1, 1):
    t = _offset(sq, df, dr)
    if t is not None and _is_enemy(squares[t], white):
      add(t)
  return moves

def _jump_moves(squares: list[Piece], sq: int, targets: list[int]) -> list[Move]:
  white = squares[sq].isupper()
  moves: list[Move] = []
  for t in targets:
    if not _is_friend(squares[t], white):
      moves.append(Move(sq, t))
  return moves

def _slide_moves(squares: list[Piece], sq: int, rays: list[list[int]]) -> list[Move]:
  white = squares[sq].isupper()
  moves: list[Move] = []
  for ray in rays:
    for t in ray:
      p = squares[t]
      if p is None:
        moves.append(Move(sq, t))
      else:
        if is_white(p) != white:
          moves.append(Move(sq, t))
        break
  return moves

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
    elif piece.upper() == "B":
      moves.extend(_slide_moves(squares, sq, BISHOP_RAYS[sq]))
    elif piece.upper() == "R":
      moves.extend(_slide_moves(squares, sq, ROOK_RAYS[sq]))
    elif piece.upper() == "Q":
      moves.extend(_slide_moves(squares, sq, QUEEN_RAYS[sq]))

  return moves

def legal_moves(board: Board) -> list[Move]:
  """Pseudo-legal moves that don't leave the mover's own king in check."""
  white = board.turn == "w"
  return [
    m for m in pseudo_legal_moves(board)
    if not in_check(squares_after(board.squares, m), white)
  ]