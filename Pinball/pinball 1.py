# PINBALL PINBALL — feature-packed single-file pygame game
# --------------------------------------------------------
# Keyboard Controls:
#   LEFT / RIGHT  -> Flippers
#   SPACE (hold)  -> Charge Plunger
#   SPACE (release) -> Launch Ball
#   ENTER         -> Select / Confirm (menus & name entry)
#   ESC           -> Pause (in-game) / Back (menus)
#
# Requirements:
#   pip install pygame
#
# Notes:
# - Saves top 10 high scores to ./saves/highscores.json
# - Portrait playfield (720x1280). Easily adjustable.
# - Silver ball rendering (simple highlight & rim).
# - Classic geometry: shooter lane w/ one-way gate, slings, bumpers,
#   inlanes/outlanes, top rollovers. Robust wall containment.
#
# Steam-readiness (future):
# - Assets/saves in project folder; pack with PyInstaller later.
# - Clean quit; simple main menu; consistent FPS; no external deps.

import os
import sys
import json
import math
import random
import pygame
from datetime import datetime

# -------------------------------
# Config & Globals
# -------------------------------
pygame.init()
GAME_TITLE = "PINBALL PINBALL"
VERSION = "0.1.0"
W, H = 720, 1280  # portrait table
FPS = 120
DT = 1.0 / FPS

# Physics
GRAVITY = 2400.0
AIR_FRICTION = 0.999
BALL_RADIUS = 14
BALL_RESTITUTION = 0.90
WALL_RESTITUTION = 0.96
FLIPPER_RESTITUTION = 1.03
SLING_KICK = 950.0
BUMPER_KICK = 720.0

# Gameplay
BALLS_PER_GAME = 3
EXTRA_BALL_THRESHOLD = 100_000
ROLL_OVER_BONUS = 2500  # for completing all three
TOP_LANE_SCORE = 500
BUMPER_SCORE = 200
SLING_SCORE = 75
TARGET_SCORE = 350
INLANE_SCORE = 400
OUTLANE_PENALTY = 0  # purely drain (no score)

# Colors
WHITE = (240, 240, 240)
GREY = (110, 114, 126)
DARK = (16, 18, 22)
BG = (24, 26, 30)
ACCENT = (90, 190, 255)
NEON1 = (50, 220, 180)
NEON2 = (255, 120, 80)
NEON3 = (180, 140, 255)
RED = (240, 80, 90)
YELLOW = (250, 220, 80)
GREEN = (110, 220, 120)
BLUE = (90, 170, 255)

# UI
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption(GAME_TITLE)
clock = pygame.time.Clock()
UI_FONT = pygame.font.SysFont("consolas", 26)
UI_FONT_BIG = pygame.font.SysFont("consolas", 44, bold=True)
UI_FONT_HUGE = pygame.font.SysFont("consolas", 64, bold=True)

# Saves
SAVE_DIR = os.path.join(os.getcwd(), "saves")
HS_PATH = os.path.join(SAVE_DIR, "highscores.json")
os.makedirs(SAVE_DIR, exist_ok=True)

# Scenes
SCENE_MENU = "MENU"
SCENE_HISCORES = "HISCORES"
SCENE_PLAY = "PLAY"
SCENE_PAUSE = "PAUSE"
SCENE_GAMEOVER = "GAMEOVER"
SCENE_NAMEENTRY = "NAMEENTRY"

# -------------------------------
# Utilities
# -------------------------------
def clamp(x, lo, hi):
    return lo if x < lo else hi if x > hi else x

def vlen(v):
    return math.hypot(v[0], v[1])

def vnorm(v):
    L = vlen(v)
    return (0.0, 0.0) if L == 0 else (v[0]/L, v[1]/L)

def dot(a, b):
    return a[0]*b[0] + a[1]*b[1]

def reflect(v, n, restitution=1.0):
    # n must be unit
    vn = dot(v, n)
    return (v[0] - (1+restitution)*vn*n[0],
            v[1] - (1+restitution)*vn*n[1])

def seg_normal(a, b):
    d = (b[0]-a[0], b[1]-a[1])
    n = (-d[1], d[0])
    return vnorm(n)

def proj_point_on_segment(p, a, b):
    ap = (p[0]-a[0], p[1]-a[1])
    ab = (b[0]-a[0], b[1]-a[1])
    ab2 = dot(ab, ab)
    if ab2 == 0: return a, 0.0
    t = clamp(dot(ap, ab)/ab2, 0.0, 1.0)
    q = (a[0] + ab[0]*t, a[1] + ab[1]*t)
    return q, t

def draw_text_center(surf, text, font, color, center):
    obj = font.render(text, True, color)
    rect = obj.get_rect(center=center)
    surf.blit(obj, rect)

def draw_silver_ball(surf, pos, r):
    # Base
    pygame.draw.circle(surf, (210, 210, 215), (int(pos[0]), int(pos[1])), r)
    # Rim
    pygame.draw.circle(surf, (120, 125, 135), (int(pos[0]), int(pos[1])), r, 2)
    # Gradient inner ring
    pygame.draw.circle(surf, (235, 235, 240), (int(pos[0]), int(pos[1])), max(1, r-4))
    # Highlight
    hilite = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
    pygame.draw.circle(hilite, (255, 255, 255, 120), (int(r*0.7), int(r*0.6)), r//3)
    pygame.draw.circle(hilite, (255, 255, 255, 80), (int(r*0.9), int(r*0.9)), r//4)
    surf.blit(hilite, (int(pos[0]-r), int(pos[1]-r)))

# -------------------------------
# High Scores
# -------------------------------
class HighScores:
    def __init__(self, path, max_records=10):
        self.path = path
        self.max_records = max_records
        self.records = []
        self.load()

    def load(self):
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                self.records = json.load(f)
        except Exception:
            self.records = []

    def save(self):
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self.records, f, indent=2)
        except Exception:
            pass

    def qualifies(self, score):
        if score <= 0:
            return False
        if len(self.records) < self.max_records:
            return True
        return score > min(r["score"] for r in self.records)

    def add(self, name, score):
        self.records.append({
            "name": name[:3].upper(),
            "score": int(score),
            "date": datetime.now().strftime("%Y-%m-%d")
        })
        self.records.sort(key=lambda r: r["score"], reverse=True)
        self.records = self.records[:self.max_records]
        self.save()

HS = HighScores(HS_PATH, max_records=10)

# -------------------------------
# Geometry Objects
# -------------------------------
class Wall:
    def __init__(self, a, b, restitution=WALL_RESTITUTION):
        self.a = a
        self.b = b
        self.n = seg_normal(a, b)  # left-hand normal
        self.restitution = restitution

    def collide(self, ball):
        q, t = proj_point_on_segment(ball.p, self.a, self.b)
        d = (ball.p[0]-q[0], ball.p[1]-q[1])
        dist = vlen(d)
        if dist < ball.r:
            n = vnorm(d) if dist > 1e-6 else self.n
            push = ball.r - dist + 0.5
            ball.p[0] += n[0]*push
            ball.p[1] += n[1]*push
            ball.v = list(reflect(ball.v, n, self.restitution))

    def draw(self, surf, color=GREY, width=3):
        pygame.draw.line(surf, color, self.a, self.b, width)

class OneWayWall(Wall):
    # Only collides if ball is moving into the "blocked" side (dot(v, n)<0)
    def collide(self, ball):
        if dot(ball.v, self.n) < 0.0:
            super().collide(ball)

class CircleBumper:
    def __init__(self, pos, r=34, score=BUMPER_SCORE, kick=BUMPER_KICK, color=(200, 220, 255)):
        self.pos = pos
        self.r = r
        self.score = score
        self.kick = kick
        self.color = color
        self.flash = 0.0

    def collide(self, game, ball):
        d = (ball.p[0]-self.pos[0], ball.p[1]-self.pos[1])
        dist = vlen(d)
        if dist < (ball.r + self.r):
            n = vnorm(d) if dist > 1e-6 else (0.0, -1.0)
            push = (ball.r + self.r) - dist + 0.5
            ball.p[0] += n[0]*push
            ball.p[1] += n[1]*push
            ball.v = list(reflect(ball.v, n, 1.02))
            ball.v[0] += n[0]*self.kick
            ball.v[1] += n[1]*self.kick
            self.flash = 0.12
            game.add_score(self.score)

    def draw(self, surf):
        col = ACCENT if self.flash > 0 else self.color
        pygame.draw.circle(surf, col, (int(self.pos[0]), int(self.pos[1])), self.r, 0)
        pygame.draw.circle(surf, DARK, (int(self.pos[0]), int(self.pos[1])), self.r, 2)

class SlingShot:
    def __init__(self, p1, p2, p3, kick=SLING_KICK, score=SLING_SCORE):
        self.pts = [p1, p2, p3]
        self.edges = [Wall(p1, p2), Wall(p2, p3), Wall(p3, p1)]
        self.kick = kick
        self.score = score
        self.flash = 0.0

    def collide(self, game, ball):
        hit = False
        for e in self.edges:
            q, t = proj_point_on_segment(ball.p, e.a, e.b)
            d = (ball.p[0]-q[0], ball.p[1]-q[1])
            dist = vlen(d)
            if dist < ball.r + 8:
                n = vnorm(d) if dist > 1e-6 else e.n
                push = (ball.r + 8) - dist + 0.5
                ball.p[0] += n[0]*push
                ball.p[1] += n[1]*push
                ball.v = list(reflect(ball.v, n, 1.0))
                ball.v[0] += n[0]*self.kick
                ball.v[1] += n[1]*self.kick
                hit = True
        if hit:
            self.flash = 0.1
            game.add_score(self.score)

    def draw(self, surf):
        col = NEON2 if self.flash > 0 else GREY
        pygame.draw.polygon(surf, DARK, self.pts, 0)
        pygame.draw.polygon(surf, col, self.pts, 3)

class Rollover:
    # Sensor circle for scoring top lanes or inlane entries
    def __init__(self, pos, r=18, score=TOP_LANE_SCORE, label=None):
        self.pos = pos
        self.r = r
        self.score = score
        self.label = label
        self.active = False
        self.flash = 0.0

    def sense(self, game, ball):
        d = (ball.p[0]-self.pos[0], ball.p[1]-self.pos[1])
        if d[0]*d[0] + d[1]*d[1] < (ball.r + self.r)*(ball.r + self.r):
            if not self.active:
                self.active = True
                game.add_score(self.score)
                self.flash = 0.18

    def reset(self):
        self.active = False

    def draw(self, surf):
        col = NEON1 if (self.flash > 0 or self.active) else GREY
        pygame.draw.circle(surf, col, (int(self.pos[0]), int(self.pos[1])), self.r, 3)
        if self.label:
            draw_text_center(surf, self.label, UI_FONT, col, (int(self.pos[0]), int(self.pos[1])-28))

class StandupTarget:
    # Short vertical segment that scores and bounces
    def __init__(self, a, b, score=TARGET_SCORE):
        self.wall = Wall(a, b, restitution=1.0)
        self.score = score
        self.flash = 0.0

    def collide(self, game, ball):
        before = (ball.v[0], ball.v[1])
        self.wall.collide(ball)
        # If velocity meaningfully changed, award score
        if (abs(ball.v[0]-before[0]) + abs(ball.v[1]-before[1])) > 5.0:
            self.flash = 0.12
            game.add_score(self.score)

    def draw(self, surf):
        color = YELLOW if self.flash > 0 else GREY
        self.wall.draw(surf, color=color, width=5)

class Flipper:
    def __init__(self, pivot, length, base_angle_deg, swing_deg, side='L'):
        self.pivot = pivot
        self.length = length
        self.base = math.radians(base_angle_deg)
        self.swing = math.radians(swing_deg)
        self.side = side
        self.keydown = False
        self.ang = self.base
        self.ang_vel = 0.0
        self.max_speed = 16.0
        self.return_speed = 10.0
        self.width = 18

    def update(self, dt):
        target = self.base - (self.swing if self.keydown else 0.0)
        diff = target - self.ang
        speed = self.max_speed if self.keydown else self.return_speed
        self.ang_vel = clamp(diff/dt, -speed, speed) if abs(diff) > 1e-3 else 0.0
        self.ang += self.ang_vel * dt

    def tip(self):
        return (self.pivot[0] + math.cos(self.ang)*self.length,
                self.pivot[1] + math.sin(self.ang)*self.length)

    def segment(self):
        return self.pivot, self.tip()

    def collide(self, ball):
        a, b = self.segment()
        q, t = proj_point_on_segment(ball.p, a, b)
        d = (ball.p[0]-q[0], ball.p[1]-q[1])
        dist = vlen(d)
        effective_r = ball.r + self.width*0.5
        if dist < effective_r:
            n = vnorm(d) if dist > 1e-6 else seg_normal(a, b)
            push = effective_r - dist + 0.5
            ball.p[0] += n[0]*push
            ball.p[1] += n[1]*push
            # Add flipper angular velocity influence
            tangential = self.ang_vel * self.length
            add = ( -math.sin(self.ang)*tangential, math.cos(self.ang)*tangential )
            v_rel = (ball.v[0] - add[0], ball.v[1] - add[1])
            vr = reflect(v_rel, n, FLIPPER_RESTITUTION)
            ball.v = [vr[0] + add[0], vr[1] + add[1]]
            # Ensure reasonable upward action
            speed = vlen(ball.v)
            if speed < 380:
                ball.v[0] += n[0]*260
                ball.v[1] += n[1]*260

    def draw(self, surf, color=WHITE):
        a, b = self.segment()
        pygame.draw.line(surf, color, a, b, self.width)
        pygame.draw.circle(surf, color, (int(a[0]), int(a[1])), self.width//2)
        pygame.draw.circle(surf, color, (int(b[0]), int(b[1])), self.width//2)

class Ball:
    def __init__(self, x, y):
        self.p = [x, y]
        self.v = [0.0, 0.0]
        self.r = BALL_RADIUS
        self.alive = True

    def update(self, dt):
        self.v[1] += GRAVITY * dt
        self.p[0] += self.v[0]*dt
        self.p[1] += self.v[1]*dt
        self.v[0] *= AIR_FRICTION
        self.v[1] *= AIR_FRICTION

    def draw(self, surf):
        draw_silver_ball(surf, self.p, self.r)

# -------------------------------
# Game/Table
# -------------------------------
class Game:
    def __init__(self):
        self.reset_table()
        self.new_game()

    def reset_table(self):
        self.walls = []
        self.oneways = []
        self.slings = []
        self.bumpers = []
        self.rollovers = []
        self.targets = []

        margin = 20

        # Playfield polygon (closed) with angled top corners
        # (Counter-clockwise so left-hand normals face inward)
        self.playfield_poly = [
            (margin+40, 170), (W-140, 120), (W-100, 180),  # angled right-top
            (W-100, H-260), (W-150, H-40),
            (margin+150, H-40), (margin+100, H-260),
            (margin+100, 180)
        ]
        for i in range(len(self.playfield_poly)):
            a = self.playfield_poly[i]
            b = self.playfield_poly[(i+1) % len(self.playfield_poly)]
            self.walls.append(Wall(a, b))

        # Shooter lane (right)
        self.lane_x_right = W - margin - 20
        self.lane_x_left = W - margin - 70
        top_lane_y = 150
        bottom_lane_y = H - 240
        self.walls.append(Wall((self.lane_x_left, top_lane_y), (self.lane_x_left, bottom_lane_y)))
        self.walls.append(Wall((self.lane_x_right, top_lane_y), (self.lane_x_right, bottom_lane_y)))

        # One-way gate at top of shooter lane (diagonal toward playfield)
        gate_y = 210
        gate_a = (self.lane_x_left, gate_y)
        gate_b = (self.lane_x_right, gate_y - 30)
        # Normal should block motion from playfield into lane (i.e., pointing into playfield)
        # With left-hand normal of (a->b), we choose direction so normal faces +x (approx).
        self.oneways.append(OneWayWall(gate_b, gate_a, restitution=1.0))

        # Drain line (bottom arch)
        self.drain_y = H - margin - 10
        self.drain_left = (margin+190, self.drain_y)
        self.drain_right = (W - margin - 190, self.drain_y)
        self.walls.append(Wall((margin+110, self.drain_y), (W - margin - 110, self.drain_y)))

        # Slingshots (above flippers)
        y = H - 250
        self.slings.append(SlingShot((margin+190, y+60), (margin+300, y+20), (margin+260, y+90)))
        self.slings.append(SlingShot((W-margin-190, y+60), (W-margin-300, y+20), (W-margin-260, y+90)))

        # Bumper cluster (triangle mid-top) + side bumpers
        self.bumpers.append(CircleBumper((W*0.36, H*0.34)))
        self.bumpers.append(CircleBumper((W*0.64, H*0.32)))
        self.bumpers.append(CircleBumper((W*0.50, H*0.44)))
        self.bumpers.append(CircleBumper((W*0.26, H*0.52), r=30))
        self.bumpers.append(CircleBumper((W*0.74, H*0.52), r=30))

        # Top rollovers (3 lanes)
        self.rollovers_top = [
            Rollover((W*0.30, 180), r=20, score=TOP_LANE_SCORE, label="P"),
            Rollover((W*0.50, 150), r=20, score=TOP_LANE_SCORE, label="B"),
            Rollover((W*0.70, 180), r=20, score=TOP_LANE_SCORE, label="P"),
        ]
        self.rollovers.extend(self.rollovers_top)

        # Inlanes / Outlanes (sensors + wall channels)
        # Left side
        self.inlane_left = Rollover((margin+170, H-200), r=22, score=INLANE_SCORE, label=None)
        self.outlane_left = Rollover((margin+100, H-200), r=22, score=OUTLANE_PENALTY, label=None)
        # Right side
        self.inlane_right = Rollover((W-margin-170, H-200), r=22, score=INLANE_SCORE, label=None)
        self.outlane_right = Rollover((W-margin-100, H-200), r=22, score=OUTLANE_PENALTY, label=None)
        self.rollovers += [self.inlane_left, self.inlane_right, self.outlane_left, self.outlane_right]

        # Channel walls shaping inlanes/outlanes (simple line guides)
        # Left guides
        self.walls.append(Wall((margin+120, H-300), (margin+85, H-170)))
        self.walls.append(Wall((margin+200, H-300), (margin+165, H-170)))
        # Right guides
        self.walls.append(Wall((W-margin-120, H-300), (W-margin-85, H-170)))
        self.walls.append(Wall((W-margin-200, H-300), (W-margin-165, H-170)))

        # Stand-up targets (left bank of 3)
        tx = margin + 250
        self.targets.append(StandupTarget((tx, 480), (tx, 520)))
        self.targets.append(StandupTarget((tx+26, 470), (tx+26, 510)))
        self.targets.append(StandupTarget((tx+52, 460), (tx+52, 500)))

        # Flippers (pivot from inside corners, angled slightly upward toward center)
        fy = H - 140
        self.left_flipper  = Flipper((W*0.33, fy), 140, 200, 40, 'L')
        self.right_flipper = Flipper((W*0.67, fy), 140, -20, 40, 'R')

        # Plunger
        self.plunger = 0.0
        self.plunger_charging = False
        self.PLUNGER_MAX = 950.0
        self.PLUNGER_CHARGE_RATE = 1700.0

    def new_game(self):
        self.score = 0
        self.mult = 1
        self.balls_left = BALLS_PER_GAME
        self.extra_awarded = False
        self.reset_rollovers()
        self.spawn_ball()

    def reset_rollovers(self):
        for r in self.rollovers:
            r.reset()

    def spawn_ball(self):
        # Spawn ball in shooter lane
        self.ball = Ball(self.lane_x_left + 25, H - 260)
        self.ball.v = [0.0, 0.0]
        self.in_shooter = True
        self.plunger = 0.0
        self.plunger_charging = False

    def lose_ball(self):
        self.balls_left -= 1
        if self.balls_left >= 1:
            self.spawn_ball()
        else:
            # Signal game over handled by outer state
            pass

    def add_score(self, points):
        self.score += points * self.mult
        # Extra ball threshold
        if not self.extra_awarded and self.score >= EXTRA_BALL_THRESHOLD:
            self.balls_left += 1
            self.extra_awarded = True

    # Collisions ----------------------------------------------------
    def collide_walls(self, ball):
        for w in self.walls:
            w.collide(ball)
        for ow in self.oneways:
            ow.collide(ball)

    def collide_flippers(self, ball):
        self.left_flipper.collide(ball)
        self.right_flipper.collide(ball)

    def collide_slings(self, ball):
        for s in self.slings:
            s.collide(self, ball)

    def collide_bumpers(self, ball):
        for b in self.bumpers:
            b.collide(self, ball)

    def collide_targets(self, ball):
        for t in self.targets:
            t.collide(self, ball)

    def sense_rollovers(self, ball):
        # Top lanes
        all_active = True
        for r in self.rollovers_top:
            r.sense(self, ball)
            if not r.active:
                all_active = False
        if all_active:
            # Award once per completion; then reset top lanes
            self.add_score(ROLL_OVER_BONUS)
            for r in self.rollovers_top:
                r.active = False

        # Inlanes/outlanes
        self.inlane_left.sense(self, ball)
        self.inlane_right.sense(self, ball)
        self.outlane_left.sense(self, ball)
        self.outlane_right.sense(self, ball)

    # Update & Draw -------------------------------------------------
    def update(self, dt, inputs_locked=False):
        # Update flippers regardless (so they settle)
        self.left_flipper.update(dt)
        self.right_flipper.update(dt)

        if inputs_locked:
            # e.g., pause
            return

        # Plunger hold influences only while in shooter lane
        if self.in_shooter and self.plunger_charging:
            self.plunger = clamp(self.plunger + self.PLUNGER_CHARGE_RATE*dt, 0.0, self.PLUNGER_MAX)
            # Pin ball at bottom of shooter lane
            self.ball.p[0] = clamp(self.ball.p[0], self.lane_x_left + BALL_RADIUS + 8, self.lane_x_right - BALL_RADIUS - 8)
            self.ball.p[1] = H - 240 - BALL_RADIUS - 1

        # Update ball physics
        self.ball.update(dt)

        # Apply collisions/sensors
        self.collide_bumpers(self.ball)
        self.collide_slings(self.ball)
        self.collide_targets(self.ball)
        self.collide_walls(self.ball)
        self.collide_flippers(self.ball)
        self.sense_rollovers(self.ball)

        # Prevent escape off top/left/right
        if self.ball.p[0] < BALL_RADIUS + 4:
            self.ball.p[0] = BALL_RADIUS + 4
            self.ball.v[0] = abs(self.ball.v[0]) * 0.8
        if self.ball.p[0] > W - BALL_RADIUS - 4:
            self.ball.p[0] = W - BALL_RADIUS - 4
            self.ball.v[0] = -abs(self.ball.v[0]) * 0.8
        if self.ball.p[1] < BALL_RADIUS + 4:
            self.ball.p[1] = BALL_RADIUS + 4
            self.ball.v[1] = abs(self.ball.v[1]) * 0.8

        # Drain detection
        if self.ball.p[1] > self.drain_y + 30:
            self.lose_ball()

        # Decay flashes
        for s in self.slings:
            if s.flash > 0: s.flash -= dt
        for b in self.bumpers:
            if b.flash > 0: b.flash -= dt
        for r in self.rollovers:
            if r.flash > 0: r.flash -= dt
        for t in self.targets:
            if t.flash > 0: t.flash -= dt

    def launch(self):
        # Convert plunger to vertical launch velocity
        power = clamp(self.plunger, 0.0, self.PLUNGER_MAX)
        self.ball.v[1] = -(760 + power * 0.9)
        self.ball.v[0] = -40.0  # slight left bias to enter playfield
        self.in_shooter = False
        self.plunger_charging = False
        self.plunger = 0.0

    def draw(self, surf, show_hud=True):
        # Background
        surf.fill(BG)

        # Subtle horizontal stripes
        for i in range(0, H, 42):
            a = 30 + (i//42)%2*10
            pygame.draw.line(surf, (a, a, a), (28, i), (W-28, i), 1)

        # Shooter lane area
        pygame.draw.rect(surf, (28, 30, 36), (self.lane_x_left, 150, self.lane_x_right - self.lane_x_left, H - 370))
        pygame.draw.line(surf, GREY, (self.lane_x_left, 150), (self.lane_x_left, H - 220), 3)
        pygame.draw.line(surf, GREY, (self.lane_x_right, 150), (self.lane_x_right, H - 220), 3)

        # Gate
        for ow in self.oneways:
            ow.draw(surf, color=(160, 220, 160), width=4)

        # Playfield polygon
        pygame.draw.polygon(surf, (26, 28, 33), self.playfield_poly, 0)
        for w in self.walls:
            w.draw(surf)

        # Slings, bumpers, targets
        for s in self.slings: s.draw(surf)
        for b in self.bumpers: b.draw(surf)
        for t in self.targets: t.draw(surf)
        for r in self.rollovers: r.draw(surf)

        # Flippers
        self.left_flipper.draw(surf, color=WHITE)
        self.right_flipper.draw(surf, color=WHITE)

        # Ball
        self.ball.draw(surf)

        # Bottom arch
        pygame.draw.line(surf, GREY, (28, self.drain_y), (W-28, self.drain_y), 2)

        if show_hud:
            self.draw_hud(surf)

    def draw_hud(self, surf):
        # HUD bar
        hud_h = 78
        pygame.draw.rect(surf, (14, 14, 18), (0, 0, W, hud_h))
        pygame.draw.line(surf, (50, 50, 60), (0, hud_h), (W, hud_h), 2)

        s1 = UI_FONT_HUGE.render(f"{self.score:,}", True, WHITE)
        surf.blit(s1, (24, 8))
        s2 = UI_FONT.render(f"Balls: {max(self.balls_left, 0)}", True, (220,220,230))
        surf.blit(s2, (W - 200, 22))
        s3 = UI_FONT.render(f"v{VERSION}", True, GREY)
        surf.blit(s3, (W - 110, 52))

        # Plunger meter (only when in shooter)
        if self.in_shooter:
            meter_w = 12
            meter_h = 240
            x = self.lane_x_right + 24
            y = H - 240 - meter_h
            pygame.draw.rect(surf, (40,40,50), (x, y, meter_w, meter_h), 2)
            pct = clamp(self.plunger / self.PLUNGER_MAX, 0.0, 1.0)
            fill_h = int(pct * (meter_h-4))
            pygame.draw.rect(surf, ACCENT, (x+2, y + (meter_h-2 - fill_h), meter_w-4, fill_h))

# -------------------------------
# Scenes / App
# -------------------------------
class App:
    def __init__(self):
        self.scene = SCENE_MENU
        self.game = Game()
        self.menu_index = 0
        self.menu_items = ["Start Game", "High Scores", "Quit"]
        self.pause_index = 0
        self.pause_items = ["Resume", "Restart", "Main Menu", "Quit"]
        self.gameover_index = 0
        self.gameover_items = ["Play Again", "Main Menu", "High Scores", "Quit"]

        self.name_entry_chars = []
        self.name_prompt_time = 0.0
        self.flash_timer = 0.0
        self.pending_final_score = 0

    # --- Scene Helpers ---
    def switch(self, new_scene):
        self.scene = new_scene
        self.flash_timer = 0.0
        self.name_prompt_time = 0.0

    # --- Input Handling ---
    def handle_keydown(self, key):
        if self.scene == SCENE_MENU:
            if key in (pygame.K_UP, pygame.K_LEFT):
                self.menu_index = (self.menu_index - 1) % len(self.menu_items)
            elif key in (pygame.K_DOWN, pygame.K_RIGHT):
                self.menu_index = (self.menu_index + 1) % len(self.menu_items)
            elif key == pygame.K_RETURN:
                self.select_menu()
            elif key == pygame.K_ESCAPE:
                pygame.event.post(pygame.event.Event(pygame.QUIT))

        elif self.scene == SCENE_HISCORES:
            if key in (pygame.K_ESCAPE, pygame.K_RETURN):
                self.switch(SCENE_MENU)

        elif self.scene == SCENE_PLAY:
            if key == pygame.K_ESCAPE:
                self.switch(SCENE_PAUSE)
            if key == pygame.K_LEFT:
                self.game.left_flipper.keydown = True
            if key == pygame.K_RIGHT:
                self.game.right_flipper.keydown = True
            if key == pygame.K_SPACE and self.game.in_shooter:
                self.game.plunger_charging = True

        elif self.scene == SCENE_PAUSE:
            if key in (pygame.K_UP, pygame.K_LEFT):
                self.pause_index = (self.pause_index - 1) % len(self.pause_items)
            elif key in (pygame.K_DOWN, pygame.K_RIGHT):
                self.pause_index = (self.pause_index + 1) % len(self.pause_items)
            elif key == pygame.K_RETURN:
                self.select_pause()
            elif key == pygame.K_ESCAPE:
                self.switch(SCENE_PLAY)

        elif self.scene == SCENE_GAMEOVER:
            if key in (pygame.K_UP, pygame.K_LEFT):
                self.gameover_index = (self.gameover_index - 1) % len(self.gameover_items)
            elif key in (pygame.K_DOWN, pygame.K_RIGHT):
                self.gameover_index = (self.gameover_index + 1) % len(self.gameover_items)
            elif key == pygame.K_RETURN:
                self.select_gameover()
            elif key == pygame.K_ESCAPE:
                self.switch(SCENE_MENU)

        elif self.scene == SCENE_NAMEENTRY:
            # Only 3 letters (A-Z)
            if pygame.K_a <= key <= pygame.K_z:
                if len(self.name_entry_chars) < 3:
                    ch = chr(key).upper()
                    self.name_entry_chars.append(ch)
            elif key == pygame.K_BACKSPACE:
                if self.name_entry_chars:
                    self.name_entry_chars.pop()
            elif key == pygame.K_RETURN:
                if len(self.name_entry_chars) == 3:
                    name = "".join(self.name_entry_chars)
                    HS.add(name, self.pending_final_score)
                    self.switch(SCENE_HISCORES)

    def handle_keyup(self, key):
        if self.scene == SCENE_PLAY:
            if key == pygame.K_LEFT:
                self.game.left_flipper.keydown = False
            if key == pygame.K_RIGHT:
                self.game.right_flipper.keydown = False
            if key == pygame.K_SPACE and self.game.in_shooter:
                self.game.launch()

    # --- Menu Selectors ---
    def select_menu(self):
        sel = self.menu_items[self.menu_index]
        if sel == "Start Game":
            self.game.new_game()
            self.switch(SCENE_PLAY)
        elif sel == "High Scores":
            self.switch(SCENE_HISCORES)
        elif sel == "Quit":
            pygame.event.post(pygame.event.Event(pygame.QUIT))

    def select_pause(self):
        sel = self.pause_items[self.pause_index]
        if sel == "Resume":
            self.switch(SCENE_PLAY)
        elif sel == "Restart":
            self.game.new_game()
            self.switch(SCENE_PLAY)
        elif sel == "Main Menu":
            self.switch(SCENE_MENU)
        elif sel == "Quit":
            pygame.event.post(pygame.event.Event(pygame.QUIT))

    def select_gameover(self):
        sel = self.gameover_items[self.gameover_index]
        if sel == "Play Again":
            self.game.new_game()
            self.switch(SCENE_PLAY)
        elif sel == "Main Menu":
            self.switch(SCENE_MENU)
        elif sel == "High Scores":
            self.switch(SCENE_HISCORES)
        elif sel == "Quit":
            pygame.event.post(pygame.event.Event(pygame.QUIT))

    # --- Update ---
    def update(self, dt):
        self.flash_timer += dt

        if self.scene == SCENE_PLAY:
            self.game.update(dt)
            # Detect game over transition
            if self.game.balls_left <= 0 and self.game.ball.p[1] > self.game.drain_y + 30:
                final_score = self.game.score
                if HS.qualifies(final_score):
                    self.pending_final_score = final_score
                    self.name_entry_chars = []
                    self.switch(SCENE_NAMEENTRY)
                else:
                    self.switch(SCENE_GAMEOVER)

        elif self.scene == SCENE_PAUSE:
            # freeze game visuals but still draw table underneath
            pass

        elif self.scene == SCENE_NAMEENTRY:
            self.name_prompt_time += dt

    # --- Drawing ---
    def draw(self, surf):
        if self.scene in (SCENE_PLAY, SCENE_PAUSE):
            self.game.draw(surf, show_hud=True)
            if self.scene == SCENE_PAUSE:
                self.draw_pause_overlay(surf)
        elif self.scene == SCENE_MENU:
            self.draw_menu(surf)
        elif self.scene == SCENE_HISCORES:
            self.draw_highscores(surf)
        elif self.scene == SCENE_GAMEOVER:
            self.draw_gameover(surf)
        elif self.scene == SCENE_NAMEENTRY:
            self.draw_nameentry(surf)

    def draw_menu(self, surf):
        surf.fill(DARK)
        draw_text_center(surf, GAME_TITLE, UI_FONT_HUGE, WHITE, (W//2, 180))
        draw_text_center(surf, "A Neon Arcade by You", UI_FONT, GREY, (W//2, 240))
        # Fancy divider
        pygame.draw.line(surf, NEON3, (W*0.2, 280), (W*0.8, 280), 3)

        for i, item in enumerate(self.menu_items):
            y = 380 + i*70
            sel = (i == self.menu_index)
            col = ACCENT if sel else WHITE
            draw_text_center(surf, f"{item}", UI_FONT_BIG, col, (W//2, y))
            if sel:
                pygame.draw.circle(surf, col, (W//2 - 160, y), 6)

        draw_text_center(surf, f"Version {VERSION}", UI_FONT, GREY, (W//2, H-80))
        draw_text_center(surf, "ENTER=Select  •  ESC=Quit", UI_FONT, GREY, (W//2, H-50))

    def draw_highscores(self, surf):
        surf.fill(DARK)
        draw_text_center(surf, f"{GAME_TITLE} — HIGH SCORES", UI_FONT_HUGE, WHITE, (W//2, 160))
        pygame.draw.line(surf, NEON1, (W*0.2, 210), (W*0.8, 210), 3)

        if not HS.records:
            draw_text_center(surf, "No scores yet. Be the first!", UI_FONT_BIG, GREY, (W//2, 380))
        else:
            for i, rec in enumerate(HS.records):
                rank = i + 1
                name = rec["name"]
                score = rec["score"]
                date = rec.get("date", "")
                y = 280 + i*60
                draw_text_center(surf, f"{rank:2d}. {name:<3}   {score:>8,}   {date}", UI_FONT_BIG, WHITE if i < 3 else GREY, (W//2, y))

        draw_text_center(surf, "ESC/ENTER: Back", UI_FONT, GREY, (W//2, H-60))

    def draw_pause_overlay(self, surf):
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        surf.blit(overlay, (0, 0))
        draw_text_center(surf, "PAUSED", UI_FONT_HUGE, WHITE, (W//2, H//2 - 140))

        for i, item in enumerate(self.pause_items):
            y = H//2 - 40 + i*60
            sel = (i == self.pause_index)
            col = ACCENT if sel else WHITE
            draw_text_center(surf, item, UI_FONT_BIG, col, (W//2, y))

        draw_text_center(surf, "ENTER=Select • ESC=Resume", UI_FONT, GREY, (W//2, H//2 + 180))

    def draw_gameover(self, surf):
        surf.fill(DARK)
        draw_text_center(surf, "GAME OVER", UI_FONT_HUGE, RED, (W//2, 200))
        draw_text_center(surf, f"Final Score: {self.game.score:,}", UI_FONT_BIG, WHITE, (W//2, 280))
        pygame.draw.line(surf, NEON2, (W*0.2, 320), (W*0.8, 320), 3)

        for i, item in enumerate(self.gameover_items):
            y = 420 + i*70
            sel = (i == self.gameover_index)
            col = ACCENT if sel else WHITE
            draw_text_center(surf, item, UI_FONT_BIG, col, (W//2, y))

        draw_text_center(surf, "ENTER=Select • ESC=Menu", UI_FONT, GREY, (W//2, H-80))

    def draw_nameentry(self, surf):
        surf.fill(DARK)
        draw_text_center(surf, "NEW HIGH SCORE!", UI_FONT_HUGE, YELLOW, (W//2, 180))
        draw_text_center(surf, f"Your Score: {self.pending_final_score:,}", UI_FONT_BIG, WHITE, (W//2, 250))
        pygame.draw.line(surf, NEON1, (W*0.2, 300), (W*0.8, 300), 3)

        draw_text_center(surf, "ENTER YOUR INITIALS", UI_FONT_BIG, WHITE, (W//2, 360))
        # Entry slots
        x0 = W//2 - 120
        letters = "".join(self.name_entry_chars)
        for i in range(3):
            x = x0 + i*120
            rect = pygame.Rect(x-40, 410, 80, 100)
            pygame.draw.rect(surf, (32, 34, 42), rect, border_radius=12)
            pygame.draw.rect(surf, GREY, rect, 2, border_radius=12)
            ch = letters[i] if i < len(letters) else ""
            # flash cursor on next slot
            if i == len(letters) and (int(self.flash_timer*2) % 2 == 0) and len(letters) < 3:
                draw_text_center(surf, "_", UI_FONT_HUGE, ACCENT, rect.center)
            draw_text_center(surf, ch, UI_FONT_HUGE, ACCENT if ch else WHITE, rect.center)

        draw_text_center(surf, "Type A–Z • BACKSPACE=Delete • ENTER=Confirm", UI_FONT, GREY, (W//2, 560))

    # --- Main per-frame ---
    def frame(self, dt):
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return False
            elif e.type == pygame.KEYDOWN:
                self.handle_keydown(e.key)
            elif e.type == pygame.KEYUP:
                self.handle_keyup(e.key)

        self.update(dt)
        self.draw(screen)
        pygame.display.flip()
        return True

# -------------------------------
# Main
# -------------------------------
def main():
    app = App()
    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        running = app.frame(dt)

        # If in PLAY and true game over occurred (no balls), route after drain
        if app.scene == SCENE_PLAY and app.game.balls_left <= 0 and app.game.ball.p[1] > app.game.drain_y + 30:
            final_score = app.game.score
            if HS.qualifies(final_score):
                app.pending_final_score = final_score
                app.name_entry_chars = []
                app.switch(SCENE_NAMEENTRY)
            else:
                app.switch(SCENE_GAMEOVER)

if __name__ == "__main__":
    main()
