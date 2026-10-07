import math
from array import array
import pygame
import random
from game.beat import Note, LANES, LANE_KEYS, LANE_LABELS, LANE_COLORS

WIDTH, HEIGHT = 480, 640
FPS = 60
HIT_Y = HEIGHT - 80
HIT_WINDOW = 30
MAX_MISSES = 15
BPM = 120              # tempo: one note spawns on every beat
HOLD_FRAMES = FPS      # a hold note must be held for 1 second
HOLD_CHANCE = 0.2      # share of spawned notes that are hold notes
HOLD_GAP = 45          # extra frames a lane stays clear after a hold note's body
BG = (15, 10, 25)
LANE_W = WIDTH // LANES

def make_hit_sound():
    # Short 880 Hz beep built in memory, so no audio file is needed.
    # Samples are signed 16-bit (pygame's default mixer format) and are written
    # for whatever sample rate / channel count the mixer actually opened with.
    rate, _, channels = pygame.mixer.get_init()
    length = int(rate * 0.08)  # 80 ms
    samples = array("h")
    for i in range(length):
        fade = 1 - i / length  # fade out so the beep doesn't end with a click
        value = int(32767 * 0.4 * fade * math.sin(2 * math.pi * 880 * i / rate))
        samples.extend([value] * channels)
    return pygame.mixer.Sound(buffer=samples)

class GameEngine:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        self.hit_sound = make_hit_sound()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Rhythm Tap")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("monospace", 26, bold=True)
        self.big_font = pygame.font.SysFont("monospace", 44, bold=True)
        self.reset()

    def reset(self):
        self.notes = []
        self.score = 0
        self.combo = 0
        self.max_combo = 0
        self.misses = 0
        self.grade_counts = {"PERFECT": 0, "GREAT": 0, "OK": 0}  # successful hits per grade
        self.beat = 0  # beats of BPM elapsed so far
        self.speed = 5
        self.frame = 0
        self.feedback = []  # (text, color, ttl, x, y)
        self.game_over = False
        self.lane_block = [0] * LANES  # frames each lane stays reserved by a hold note

    def spawn_note(self):
        # A lane reserved by a hold note gets no new notes until the hold is over,
        # so nothing can reach the line in a lane whose key has to stay down.
        lane = random.choice([i for i in range(LANES) if self.lane_block[i] == 0])
        hold_frames = 0
        # Only one hold note at a time: no new hold while any lane is still reserved.
        if not any(self.lane_block) and random.random() < HOLD_CHANCE:
            hold_frames = HOLD_FRAMES
            self.lane_block[lane] = HOLD_FRAMES + HOLD_GAP
        self.notes.append(Note(lane, y=-30, speed=self.speed, hold_frames=hold_frames))

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    self.reset()
                elif not self.game_over:
                    for i, key in enumerate(LANE_KEYS):
                        if event.key == key:
                            self.process_tap(i)
            if event.type == pygame.KEYUP and not self.game_over:
                for i, key in enumerate(LANE_KEYS):
                    if event.key == key:
                        self.process_release(i)
        return True

    def process_tap(self, lane):
        # Find closest note in this lane near hit zone
        best = None
        best_dist = 9999
        for note in self.notes:
            if note.lane == lane and not note.hit and not note.missed and not note.holding:
                dist = abs(note.y + Note.HEIGHT//2 - HIT_Y)
                if dist < best_dist:
                    best_dist = dist
                    best = note
        lane_x = lane * LANE_W + LANE_W // 2
        if best and best_dist <= HIT_WINDOW:
            if best_dist < 8:
                grade, pts = "PERFECT", 300
                col = (255, 220, 0)
            elif best_dist < 18:
                grade, pts = "GREAT", 200
                col = (100, 220, 100)
            else:
                grade, pts = "OK", 100
                col = (180, 180, 255)
            if best.hold_frames:
                # Hold note: the press only starts the hold. Score, combo and
                # sound are given in update() once it has been held long enough.
                best.holding = True
                best.grade = (grade, pts, col)
                best.y = HIT_Y - Note.HEIGHT//2  # pin the head to the hit line
            else:
                best.hit = True
                self.award_hit(grade, pts, col, lane_x)
        else:
            # Empty/invalid tap: counts as exactly one miss.
            self.register_miss(lane_x)

    def process_release(self, lane):
        # Letting go while a hold note in this lane is still running is a miss.
        for note in self.notes:
            if note.lane == lane and note.holding:
                self.notes.remove(note)
                self.register_miss(lane * LANE_W + LANE_W // 2)
                break

    def award_hit(self, grade, pts, col, lane_x):
        # Credit for one successful note: a tap, or a hold that was completed.
        self.grade_counts[grade] += 1
        self.combo += 1
        self.max_combo = max(self.max_combo, self.combo)
        self.score += pts * max(1, self.combo // 5)
        self.feedback.append([grade, col, 40, lane_x, HIT_Y - 30])
        self.hit_sound.play()  # successful hits only (PERFECT / GREAT / OK)

    def register_miss(self, lane_x):
        # Player-caused miss: an empty/invalid tap, or a hold released too early.
        self.combo = 0
        self.misses += 1
        if self.misses >= MAX_MISSES:
            # End the run now so further key events this frame can't over-count.
            self.game_over = True
        self.feedback.append(["MISS", (220,60,60), 40, lane_x, HIT_Y - 30])

    def accuracy(self):
        # Successful hits as a percentage of all attempts (hits + misses).
        hits = sum(self.grade_counts.values())
        attempts = hits + self.misses
        return 100 * hits / attempts if attempts else 0.0

    def update(self):
        if self.game_over: return
        self.frame += 1
        # BPM-synced spawning: one note on every beat. The beat count is derived
        # straight from the frame count (a minute is FPS * 60 frames), so beats
        # never drift, even when a beat is not a whole number of frames.
        beat = self.frame * BPM // (FPS * 60)
        if beat > self.beat:
            self.beat = beat
            self.spawn_note()
        self.lane_block = [max(0, b - 1) for b in self.lane_block]

        # Difficulty ramp: every 600 frames (10 s), regardless of spawn timing.

        if self.frame % 600 == 0:
            self.speed = min(10, self.speed + 0.5)

        for note in self.notes:
            note.update()
            if note.holding and note.held >= note.hold_frames:
                # Held for the full duration: now it counts as a hit.
                note.holding = False
                note.hit = True
                self.award_hit(*note.grade, note.lane * LANE_W + LANE_W // 2)
            # Same measure process_tap uses: once the note's centre is more than
            # HIT_WINDOW below the hit line it can no longer be hit, so it is a miss.
            if not note.hit and not note.missed and note.y + Note.HEIGHT//2 - HIT_Y > HIT_WINDOW:
                note.missed = True
                self.misses += 1
                self.combo = 0

        self.notes = [n for n in self.notes if not (n.hit or n.missed)]
        self.feedback = [[t,c,ttl-1,x,y] for t,c,ttl,x,y in self.feedback if ttl > 1]

        if self.misses >= MAX_MISSES:
            self.game_over = True

    def draw(self):
        self.screen.fill(BG)
        # Lane dividers
        for i in range(LANES + 1):
            pygame.draw.line(self.screen, (40,40,60), (i*LANE_W,0), (i*LANE_W,HEIGHT), 1)

        # Hit line
        pygame.draw.line(self.screen, (80,80,100), (0,HIT_Y), (WIDTH,HIT_Y), 2)
        for i in range(LANES):
            lx = i*LANE_W + LANE_W//2
            pygame.draw.rect(self.screen, LANE_COLORS[i],
                pygame.Rect(lx - Note.WIDTH//2, HIT_Y - 12, Note.WIDTH, 24), border_radius=6)
            lbl = self.font.render(LANE_LABELS[i], True, (20,20,20))
            self.screen.blit(lbl, (lx - lbl.get_width()//2, HIT_Y - 10))

        # Notes
        for note in self.notes:
            if note.hit: continue
            lx = note.lane * LANE_W + LANE_W // 2
            color = LANE_COLORS[note.lane]
            if note.hold_frames:
                # Hold body: dim while falling, bright and draining while held.
                if note.holding:
                    tail_color = [min(255, c + 80) for c in color]
                else:
                    tail_color = [c // 2 for c in color]
                pygame.draw.rect(self.screen, tail_color, note.get_tail_rect(lx), border_radius=5)
            if note.holding:
                # Outline the lane button instead of covering its key label.
                pygame.draw.rect(self.screen, (255,255,255),
                    pygame.Rect(lx - Note.WIDTH//2, HIT_Y - 12, Note.WIDTH, 24), 2, border_radius=6)
                continue
            rect = note.get_rect(lx)
            pygame.draw.rect(self.screen, color, rect, border_radius=5)

        # Feedback
        for text, color, ttl, x, y in self.feedback:
            surf = self.font.render(text, True, color)
            alpha = min(255, ttl * 7)
            surf.set_alpha(alpha)
            self.screen.blit(surf, (x - surf.get_width()//2, y))

        # HUD
        sc = self.font.render(f"Score: {self.score}", True, (220,220,220))
        co = self.font.render(f"Combo: {self.combo}x", True, (255,220,80))
        mi = self.font.render(f"Misses: {self.misses}/{MAX_MISSES}", True, (220,100,100))
        self.screen.blit(sc, (10, 10))
        self.screen.blit(co, (10, 40))
        self.screen.blit(mi, (WIDTH - mi.get_width() - 10, 10))

        if self.game_over:
            ov = pygame.Surface((WIDTH,HEIGHT), pygame.SRCALPHA)
            ov.fill((0,0,0,160))
            self.screen.blit(ov,(0,0))
            msg = self.big_font.render("GAME OVER", True, (220,60,60))
            self.screen.blit(msg, (WIDTH//2-msg.get_width()//2, 110))
            lines = [
                (185, f"Final Score: {self.score}", (200,200,200)),
                (215, f"Max Combo: {self.max_combo}x", (200,200,200)),
                (415, f"Accuracy: {self.accuracy():.1f}%", (220,220,220)),
                (475, "Press R to Restart", (160,160,160)),
            ]
            for y, text, color in lines:
                line = self.font.render(text, True, color)
                self.screen.blit(line, (WIDTH//2-line.get_width()//2, y))
            # Grade summary: label on the left, count right-aligned, one row per grade.
            grades = [
                ("PERFECT", self.grade_counts["PERFECT"], (255,220,0)),
                ("GREAT", self.grade_counts["GREAT"], (100,220,100)),
                ("OK", self.grade_counts["OK"], (180,180,255)),
                ("MISS", self.misses, (220,60,60)),
            ]
            for i, (label, count, color) in enumerate(grades):
                name = self.font.render(label, True, color)
                num = self.font.render(str(count), True, color)
                self.screen.blit(name, (WIDTH//2-100, 270 + i*30))
                self.screen.blit(num, (WIDTH//2+100-num.get_width(), 270 + i*30))
        pygame.display.flip()

    def run(self):
        running = True
        while running:
            running = self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        pygame.quit()