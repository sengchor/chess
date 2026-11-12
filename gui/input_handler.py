import pygame

from core.board import Board

class InputHandler:
  def __init__(self, board: Board) -> None:
    self.board = board
    self.flipped = False

  def handle(self, event: pygame.event.Event) -> None:
    pass