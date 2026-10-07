import pygame
import random

LANES = 4
LANE_KEYS = [pygame.K_d, pygame.K_f, pygame.K_j, pygame.K_k]
LANE_LABELS = ['D', 'F', 'J', 'K']
LANE_COLORS = [(220,80,80),(80,180,220),(100,220,100),(220,180,60)]

class Note:
    WIDTH = 70
    HEIGHT = 20
    TAIL_WIDTH = 30
    def __init__(self, lane, y=-30, speed=4, hold_frames=0):
        self.lane = lane
        self.y = y
        self.speed = speed
        self.hit = False
        self.missed = False
        # Hold notes: hold_frames > 0 is how long the key must stay down.
        # A normal tap note has hold_frames == 0 and never uses the rest.
        self.hold_frames = hold_frames
        self.holding = False   # key is currently held on this note
        self.held = 0          # frames held so far
        self.grade = None      # (grade, pts, col) earned by the press, paid out on completion

    def update(self):
        if self.holding:
            self.held += 1     # head stays on the hit line while the hold runs
        else:
            self.y += self.speed

    def get_rect(self, lane_x):
        return pygame.Rect(lane_x - self.WIDTH//2, int(self.y), self.WIDTH, self.HEIGHT)

    def get_tail_rect(self, lane_x):
        # Body of a hold note, sitting on top of the head. Its length is the
        # distance the note travels in the frames still to be held, so it shows
        # the full hold duration on the way down and drains while the key is held.
        length = int(self.speed * (self.hold_frames - self.held))
        return pygame.Rect(lane_x - self.TAIL_WIDTH//2, int(self.y) - length, self.TAIL_WIDTH, length)