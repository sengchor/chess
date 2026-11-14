import pygame

from gui import constants as C

FILES = "abcdefgh"

def square_to_rect(sq: int) -> pygame.Rect:
  file, rank = sq % 8, sq // 8
  col = file
  row = 7 - rank
  x = C.BOARD_ORIGIN[0] + col * C.SQUARE_SIZE
  y = C.BOARD_ORIGIN[1] + row * C.SQUARE_SIZE
  return pygame.Rect(x, y, C.SQUARE_SIZE, C.SQUARE_SIZE)

def pixel_to_square(pos: tuple[int, int]) -> int | None:
  x = pos[0] - C.BOARD_ORIGIN[0]
  y = pos[1] - C.BOARD_ORIGIN[1]
  if not (0 <= x < C.BOARD_SIZE and 0 <= y < C.BOARD_SIZE):
    return None
  col = x // C.SQUARE_SIZE
  row = y // C.SQUARE_SIZE
  file = col
  rank = 7 - row
  return rank * 8 + file

def square_name(sq: int) -> str:
  return f"{FILES[sq % 8]}{sq // 8 + 1}"