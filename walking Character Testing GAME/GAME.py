"""
One-file Pygame game + improved character generator + enemies + HP system.

Features:
- Main Menu: Start Game, Options, Quit
- Loading Screen with green progress bar while generating a detailed sprite
- Auto-saves each generated character with a unique filename in ./characters/
- Options Menu: Back, Select Character (shows previews)
- In-Game: WASD movement, Esc to pause (Resume, Quit to Main Menu)
- HP system: player starts with 3 hearts
- Small slow-moving red dots (enemies) bounce; touching them costs a heart
- Rare heart pickups can spawn to restore 1 heart (up to a cap)
- Invulnerability window after being hit to avoid immediate repeated damage

Requirements:
    pip install pygame pillow
Run:
    python game_with_enemies.py
"""

import os, sys, math, time, uuid, random, datetime
import pygame
from pygame import Rect
from PIL import Image, ImageDraw

# ----------------------------- CONFIG ---------------------------------
SCREEN_W, SCREEN_H = 960, 540
FPS = 60
ASSETS_DIR = "characters"
SHEET_COLS, SHEET_ROWS = 3, 4
BASE_SIZE = 16
SCALE = 8
MOVE_SPEED = 180  # pixels per second
FONT_NAME = None
BG_COLOR = (30, 30, 40)
UI_ACCENT = (80, 200, 120)
BTN_BG = (48, 56, 69)
BTN_BG_HOVER = (68, 86, 99)
BTN_TEXT = (230, 235, 240)
PANEL_BG = (20, 22, 28)

DIR_DOWN, DIR_LEFT, DIR_RIGHT, DIR_UP = 0, 1, 2, 3

# Gameplay enemy/pickup rates (tune for "rare")
ENEMY_SPAWN_PER_SECOND = 0.04    # approx one enemy every 25 sec on average
HEART_SPAWN_PER_SECOND = 0.02    # very rare heart spawn (approx 1 every 50s)
ENEMY_MIN_SPEED = 20             # px/sec (slow)
ENEMY_MAX_SPEED = 60             # px/sec
ENEMY_RADIUS = 10                # px
HEART_RADIUS = 10                # px
INVULN_MS = 1000                 # invulnerability duration after hit (1 second)
STARTING_HEARTS = 3
MAX_HEARTS = 5

# ----------------------------- UTILITIES -------------------------------
def ensure_dirs():
    os.makedirs(ASSETS_DIR, exist_ok=True)

def unique_name(prefix="character"):
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    uid = uuid.uuid4().hex[:6]
    return f"{prefix}_{ts}_{uid}"

def list_saved_characters():
    items = []
    if not os.path.isdir(ASSETS_DIR):
        return items
    for fn in os.listdir(ASSETS_DIR):
        if fn.endswith("_sheet.png"):
            base = fn[:-10]
            sheet = os.path.join(ASSETS_DIR, fn)
            preview = os.path.join(ASSETS_DIR, base + "_preview.png")
            if os.path.isfile(preview):
                mtime = os.path.getmtime(sheet)
                items.append({"base": base, "sheet": sheet, "preview": preview, "mtime": mtime})
    items.sort(key=lambda x: x["mtime"], reverse=True)
    return items

# ---------------------- DETAILED SPRITE GENERATOR ----------------------
def darker(color, factor=0.8):
    r,g,b = color
    return (max(0, int(r*factor)), max(0, int(g*factor)), max(0, int(b*factor)))

def choose_palette(rnd):
    palettes = [
        ((233,196,106),(42,157,143),(38,70,83)),
        ((244,162,97),(231,111,81),(38,70,83)),
        ((129,178,154),(61,90,128),(41,50,65)),
        ((255,183,3),(0,119,182),(33,37,41)),
        ((170,213,255),(89,89,208),(34,34,59)),
        ((223,249,251),(126,214,223),(47,53,66)),
    ]
    prim, sec, acc = rnd.choice(palettes)
    skin_tones = [
        (255,224,189),(242,198,167),(224,172,105),
        (198,134,66),(141,85,36)
    ]
    return {
        "primary": prim, "secondary": sec, "accent": acc,
        "skin": rnd.choice(skin_tones),
        "outline": (28,28,28),
        "hair": rnd.choice([(20,20,20),(120,60,20),(200,180,50),(255,255,255),(60,90,160)])
    }

def put(px, w, h, x, y, c):
    if 0 <= x < w and 0 <= y < h:
        px[x, y] = c

def mirror(px, w, h, x, y, c, symmetric=True):
    put(px,w,h,x,y,c)
    if symmetric:
        put(px,w,h,w-1-x,y,c)

def circle_points(cx, cy, r):
    pts = []
    for a in range(0, 360, 6):
        x = int(round(cx + r*math.cos(math.radians(a))))
        y = int(round(cy + r*math.sin(math.radians(a))))
        pts.append((x,y))
    return list({(x,y) for x,y in pts})

def make_detailed_base(size=BASE_SIZE, seed=None, symmetric=True):
    rnd = random.Random(seed)
    pal = choose_palette(rnd)
    img = Image.new("RGBA", (size, size), (0,0,0,0))
    px = img.load()
    w,h = img.size

    # HEAD placement moved down so it sits on torso:
    head_top = 2
    head_bottom = 7  # exclusive bottom y coordinate
    head_r = 3
    cx = w//2
    cy = head_top + (head_bottom - head_top)//2

    # HEAD (skin)
    head_col = pal["skin"]
    for y in range(head_top, head_bottom):
        for x in range(w//2 + (0 if symmetric else w//2)):
            if (x-cx)**2 + (y-cy)**2 <= head_r**2:
                mirror(px, w, h, x, y, head_col, symmetric)

    # HAIR (styles)
    if rnd.random() < 0.95:
        hair_col = pal["hair"]
        style = rnd.choice(["short","long","bangs","mohawk","buzz"])
        for (x,y) in circle_points(cx, cy-1, head_r):
            if style in ("short","bangs","buzz"):
                if y <= cy: mirror(px,w,h,x,y,hair_col,symmetric)
            elif style == "long":
                if y <= cy+1: mirror(px,w,h,x,y,hair_col,symmetric)
            elif style == "mohawk":
                if abs(x-cx) <= 1 and y <= cy+1:
                    mirror(px,w,h,x,y,hair_col,False)
        if style == "bangs":
            for x in range(cx-2, cx+3):
                mirror(px,w,h,x, cy-1, darker(hair_col, 0.9), False)

    # Eyes & mouth
    eye_y = cy
    eye_dx = 1
    mirror(px,w,h,cx-eye_dx, eye_y, (10,10,10,255), True)
    if rnd.random() < 0.9:
        mirror(px,w,h,cx, eye_y+2, (80,0,0,255), False)

    # TORSO (shirt) positioned just under head (no floating)
    torso_top = head_bottom
    torso_h = 6
    torso_w = rnd.randint(6, 8)
    torso_x0 = cx - torso_w//2
    torso_col = pal["primary"]
    for y in range(torso_top, min(h-1, torso_top + torso_h)):
        for x in range(torso_x0, torso_x0 + torso_w//2 + 1):
            mirror(px,w,h,x,y,torso_col,symmetric)

    # Vertical arms (no T-pose)
    sleeve = rnd.random() < 0.8
    arm_col = torso_col if sleeve else pal["skin"]
    arm_top = torso_top + 1
    arm_h = max(3, torso_h - 2)
    left_arm_x = torso_x0 - 1
    right_arm_x = torso_x0 + torso_w
    for y in range(arm_top, min(h-2, arm_top + arm_h)):
        put(px,w,h,left_arm_x,y,arm_col)
        put(px,w,h,right_arm_x,y,arm_col)

    # Belt / accent
    if rnd.random() < 0.6:
        by = torso_top + torso_h//2
        for x in range(torso_x0, torso_x0+torso_w):
            put(px,w,h,x,by,pal["accent"])

    # Legs / pants
    leg_top = torso_top + torso_h
    leg_w = rnd.randint(2,3)
    leg_h = rnd.randint(3,5)
    leg_gap = rnd.randint(0,2)
    left_leg_x0 = cx - leg_gap//2 - leg_w
    right_leg_x0 = cx + (leg_gap+1)//2
    leg_col = pal["secondary"]
    for y in range(leg_top, min(h, leg_top + leg_h)):
        for x in range(left_leg_x0, left_leg_x0 + leg_w):
            put(px,w,h,x,y,leg_col)
        for x in range(right_leg_x0, right_leg_x0 + leg_w):
            put(px,w,h,x,y,leg_col)

    # Shoes
    boot_col = darker(leg_col, 0.6)
    yb = min(h-1, leg_top + leg_h - 1)
    for x in range(left_leg_x0, left_leg_x0 + leg_w):
        put(px,w,h,x,yb,boot_col)
    for x in range(right_leg_x0, right_leg_x0 + leg_w):
        put(px,w,h,x,yb,boot_col)

    # Outline + shading
    base = img.copy().load()
    out = pal["outline"]
    for y in range(h):
        for x in range(w):
            if base[x,y][3] != 0:
                # shading: right half slightly darker
                if x > w//2:
                    r,g,b,a = px[x,y]
                    px[x,y] = darker((r,g,b), 0.85) + (a,)
                # outline where touching transparent
                for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
                    nx,ny = x+dx, y+dy
                    if 0<=nx<w and 0<=ny<h and base[nx,ny][3] == 0:
                        put(px,w,h,x,y,out)
                        break

    return img

def scale_nearest(img, factor=SCALE):
    w,h = img.size
    return img.resize((w*factor, h*factor), Image.NEAREST)

def nudge(img, dx=0, dy=0):
    w,h = img.size
    out = Image.new("RGBA", (w,h), (0,0,0,0))
    out.paste(img, (dx,dy))
    return out

def make_walk_sheet(base_img):
    w,h = base_img.size
    # We'll split head and body so head moves less than body.
    head_h = 7
    head = base_img.crop((0, 0, w, head_h))
    body = base_img.crop((0, head_h, w, h))
    sheet = Image.new("RGBA", (w * SHEET_COLS, h * SHEET_ROWS), (0,0,0,0))

    body_offsets = [-1, 0, 1]
    for row in range(SHEET_ROWS):
        for col in range(SHEET_COLS):
            b_ofs = body_offsets[col % len(body_offsets)]
            h_ofs = int(round(b_ofs * 0.35))  # head moves less
            frame = Image.new("RGBA", (w, h), (0,0,0,0))
            frame.paste(head, (0, max(0, 0 + h_ofs)), head)
            frame.paste(body, (0, max(0, head_h + b_ofs)), body)
            sheet.paste(frame, (col * w, row * h))
    return sheet

def generate_and_save_character(progress_cb=None):
    ensure_dirs()
    steps = 4
    step = 0
    def tick():
        nonlocal step
        step += 1
        if progress_cb:
            progress_cb(step, steps)

    seed = random.randint(0, 10**9)
    tick()
    base = make_detailed_base(size=BASE_SIZE, seed=seed, symmetric=True)
    tick()
    sheet = make_walk_sheet(base)
    tick()
    sheet_big = scale_nearest(sheet, SCALE)
    preview_big = scale_nearest(base, SCALE)
    tick()

    base_name = unique_name("character")
    sheet_path = os.path.join(ASSETS_DIR, base_name + "_sheet.png")
    preview_path = os.path.join(ASSETS_DIR, base_name + "_preview.png")
    sheet_big.save(sheet_path, "PNG")
    preview_big.save(preview_path, "PNG")
    return {"base": base_name, "sheet": sheet_path, "preview": preview_path}

# ----------------------------- UI / Game -------------------------------
class Button:
    def __init__(self, rect, text, on_click):
        self.rect = Rect(rect)
        self.text = text
        self.on_click = on_click
        self.hover = False
    def draw(self, surf, font):
        color = BTN_BG_HOVER if self.hover else BTN_BG
        pygame.draw.rect(surf, color, self.rect, border_radius=12)
        label = font.render(self.text, True, BTN_TEXT)
        surf.blit(label, label.get_rect(center=self.rect.center))
    def handle(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hover = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.on_click()

STATE_MAIN = "main"
STATE_OPTIONS = "options"
STATE_SELECT = "select"
STATE_LOADING = "loading"
STATE_PLAY = "play"
STATE_PAUSE = "pause"
STATE_GAMEOVER = "gameover"

class Enemy:
    def __init__(self, x, y, vx, vy, radius=ENEMY_RADIUS):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.r = radius
    def update(self, dt):
        # dt in milliseconds
        self.x += self.vx * (dt / 1000.0)
        self.y += self.vy * (dt / 1000.0)
        # bounce off edges
        if self.x - self.r < 0:
            self.x = self.r
            self.vx *= -1
        if self.x + self.r > SCREEN_W:
            self.x = SCREEN_W - self.r
            self.vx *= -1
        if self.y - self.r < 0:
            self.y = self.r
            self.vy *= -1
        if self.y + self.r > SCREEN_H:
            self.y = SCREEN_H - self.r
            self.vy *= -1
    def draw(self, surf):
        pygame.draw.circle(surf, (200,30,30), (int(self.x), int(self.y)), self.r)
        pygame.draw.circle(surf, (120,0,0), (int(self.x), int(self.y)), self.r, 2)

class HeartPickup:
    def __init__(self, x, y, r=HEART_RADIUS):
        self.x = x
        self.y = y
        self.r = r
    def draw(self, surf, font):
        # draw small heart glyph centered
        txt = font.render("♥", True, (220,60,90))
        surf.blit(txt, txt.get_rect(center=(int(self.x), int(self.y))))

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption("Character Walk Game")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(FONT_NAME, 28)
        self.font_small = pygame.font.Font(FONT_NAME, 18)
        self.state = STATE_MAIN
        self.running = True
        self.buttons = []
        self.sheet_surface = None
        self.frames = None
        self.frame_w = self.frame_h = 0
        self.player_x = SCREEN_W//2
        self.player_y = SCREEN_H//2
        self.direction = DIR_DOWN
        self.anim_idx = 1
        self.anim_timer = 0
        self.current_character = None
        self.player_hp = STARTING_HEARTS
        self.max_hp = max(STARTING_HEARTS, MAX_HEARTS)
        self.invuln_timer = 0
        self.enemies = []
        self.heart_pickups = []
        ensure_dirs()
        self.build_main_menu()

    def build_main_menu(self):
        self.state = STATE_MAIN
        cx = SCREEN_W//2
        y0 = SCREEN_H//2 - 60
        pad = 70
        self.buttons = [
            Button((cx-150, y0, 300, 56), "Start Game", self.start_loading_generate),
            Button((cx-150, y0+pad, 300, 56), "Options", self.go_options),
            Button((cx-150, y0+2*pad, 300, 56), "Quit", self.quit_game),
        ]

    def go_options(self):
        self.state = STATE_OPTIONS
        cx = SCREEN_W//2
        y0 = SCREEN_H//2 - 60
        pad = 70
        self.buttons = [
            Button((cx-150, y0, 300, 56), "Select Character", self.go_select_character),
            Button((cx-150, y0+pad, 300, 56), "Back", self.build_main_menu),
        ]

    def go_select_character(self):
        self.state = STATE_SELECT
        self.buttons = []
        self.gallery = list_saved_characters()
        self.gallery_scroll = 0

    def start_loading_generate(self):
        self.state = STATE_LOADING
        self.loading_progress = 0.0
        self.loading_text = "Generating character..."
        def progress_cb(step, total):
            self.loading_progress = step/total
            self.draw_loading()
            pygame.display.flip()
        self.current_character = generate_and_save_character(progress_cb)
        self.load_sheet(self.current_character["sheet"])
        self.reset_player(full_reset=True)
        self.state = STATE_PLAY

    def load_sheet(self, sheet_path):
        img = pygame.image.load(sheet_path).convert_alpha()
        self.sheet_surface = img
        self.frame_w = img.get_width() // SHEET_COLS
        self.frame_h = img.get_height() // SHEET_ROWS
        self.frames = []
        for row in range(SHEET_ROWS):
            row_frames = []
            for col in range(SHEET_COLS):
                rect = Rect(col*self.frame_w, row*self.frame_h, self.frame_w, self.frame_h)
                row_frames.append(img.subsurface(rect))
            self.frames.append(row_frames)

    def reset_player(self, full_reset=False):
        self.player_x = SCREEN_W//2
        self.player_y = SCREEN_H//2
        self.direction = DIR_DOWN
        self.anim_idx = 1
        self.anim_timer = 0
        if full_reset:
            self.player_hp = STARTING_HEARTS
            self.max_hp = MAX_HEARTS
            self.invuln_timer = 0
            self.enemies = []
            self.heart_pickups = []

    def quit_game(self):
        self.running = False

    # ---------------- Drawing helpers ----------------
    def draw_header(self, title):
        pygame.draw.rect(self.screen, PANEL_BG, (0,0,SCREEN_W,90))
        label = self.font.render(title, True, BTN_TEXT)
        self.screen.blit(label, label.get_rect(midleft=(30, 45)))

    def draw_buttons(self):
        for b in self.buttons:
            b.draw(self.screen, self.font)

    def draw_main_menu(self):
        self.screen.fill(BG_COLOR)
        self.draw_header("Main Menu")
        self.draw_buttons()

    def draw_options(self):
        self.screen.fill(BG_COLOR)
        self.draw_header("Options")
        self.draw_buttons()

    def draw_loading(self):
        self.screen.fill(BG_COLOR)
        self.draw_header("Loading")
        panel = Rect(SCREEN_W//2-300, SCREEN_H//2-40, 600, 80)
        pygame.draw.rect(self.screen, (40,45,55), panel, border_radius=12)
        bar_bg = panel.inflate(-30, -26)
        pygame.draw.rect(self.screen, (80,85,95), bar_bg, border_radius=10)
        pct = max(0.0, min(1.0, self.loading_progress))
        bar_fg = Rect(bar_bg.x, bar_bg.y, int(bar_bg.w*pct), bar_bg.h)
        pygame.draw.rect(self.screen, UI_ACCENT, bar_fg, border_radius=10)
        text = self.font_small.render(self.loading_text, True, BTN_TEXT)
        self.screen.blit(text, text.get_rect(center=(SCREEN_W//2, panel.bottom+18)))

    def draw_select(self):
        self.screen.fill(BG_COLOR)
        self.draw_header("Select Character (click a preview)")
        back_btn = Button((20, 100, 140, 44), "Back", self.go_options)
        back_btn.hover = Rect(20,100,140,44).collidepoint(pygame.mouse.get_pos())
        back_btn.draw(self.screen, self.font_small)

        padding = 16
        cols = 6
        thumb_w = (SCREEN_W - padding*(cols+1)) // cols
        thumb_h = thumb_w
        y_start = 160 - self.gallery_scroll
        self.select_click_targets = []

        for idx, item in enumerate(self.gallery):
            col = idx % cols
            row = idx // cols
            x = padding + col*(thumb_w + padding)
            y = y_start + row*(thumb_h + 48)
            card = Rect(x, y, thumb_w, thumb_h+36)
            pygame.draw.rect(self.screen, (40,45,55), card, border_radius=12)
            if os.path.isfile(item["preview"]):
                try:
                    img = pygame.image.load(item["preview"]).convert_alpha()
                    img = pygame.transform.smoothscale(img, (thumb_w-12, thumb_h-12))
                    self.screen.blit(img, img.get_rect(center=(x+thumb_w//2, y+thumb_h//2)))
                except Exception:
                    pass
            name_text = self.font_small.render(item["base"], True, BTN_TEXT)
            self.screen.blit(name_text, name_text.get_rect(center=(x+thumb_w//2, y+thumb_h+18)))
            self.select_click_targets.append((card, item))

    def draw_hud(self):
        # draw hearts at top-left using glyphs
        hearts_text = " ".join(["♥" for _ in range(self.player_hp)])
        hearts_surf = self.font_small.render(hearts_text, True, (220,60,90))
        self.screen.blit(hearts_surf, (20, 20))
        # show max hearts small
        max_surf = self.font_small.render(f"/{self.max_hp}", True, BTN_TEXT)
        self.screen.blit(max_surf, (20 + hearts_surf.get_width() + 8, 20))

    def draw_play(self):
        self.screen.fill((50,50,60))
        for i in range(0, SCREEN_W, 40):
            pygame.draw.line(self.screen, (60,60,75), (i,0),(i,SCREEN_H))
        for j in range(0, SCREEN_H, 40):
            pygame.draw.line(self.screen, (60,60,75), (0,j),(SCREEN_W,j))

        # draw enemies
        for e in self.enemies:
            e.draw(self.screen)

        # draw heart pickups
        for hp in self.heart_pickups:
            hp.draw(self.screen, self.font_small)

        # draw player (with invuln blink)
        if self.frames:
            now = pygame.time.get_ticks()
            show_player = True
            if self.invuln_timer > 0:
                # blink: toggle visibility every 120ms
                if (now // 120) % 2 == 0:
                    show_player = False
            if show_player:
                frame = self.frames[self.direction][self.anim_idx]
                rect = frame.get_rect(center=(int(self.player_x), int(self.player_y)))
                self.screen.blit(frame, rect)

        self.draw_hud()
        hud = self.font_small.render("WASD to move  •  Esc to pause", True, (220,220,230))
        self.screen.blit(hud, (20, SCREEN_H-36))

    def draw_pause(self):
        self.draw_play()
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0,0,0,140))
        self.screen.blit(overlay, (0,0))
        panel = Rect(SCREEN_W//2-200, SCREEN_H//2-120, 400, 240)
        pygame.draw.rect(self.screen, PANEL_BG, panel, border_radius=16)
        title = self.font.render("Paused", True, BTN_TEXT)
        self.screen.blit(title, title.get_rect(center=(panel.centerx, panel.y+40)))
        self.pause_buttons = [
            Button((panel.centerx-140, panel.y+90, 280, 52), "Resume", self.resume_game),
            Button((panel.centerx-140, panel.y+160, 280, 52), "Quit to Main Menu", self.quit_to_main),
        ]
        for b in self.pause_buttons:
            b.hover = b.rect.collidepoint(pygame.mouse.get_pos())
            b.draw(self.screen, self.font)

    def draw_gameover(self):
        self.screen.fill((20,20,30))
        txt = self.font.render("You Died", True, (220,60,60))
        self.screen.blit(txt, txt.get_rect(center=(SCREEN_W//2, SCREEN_H//2 - 40)))
        sub = self.font_small.render("Press Enter to go to Main Menu", True, BTN_TEXT)
        self.screen.blit(sub, sub.get_rect(center=(SCREEN_W//2, SCREEN_H//2 + 16)))

    # ---------------- Actions ----------------
    def resume_game(self):
        self.state = STATE_PLAY

    def quit_to_main(self):
        self.build_main_menu()

    def spawn_enemy(self):
        # spawn away from player (min distance)
        min_dist = 120
        for _ in range(40):
            x = random.uniform(ENEMY_RADIUS, SCREEN_W - ENEMY_RADIUS)
            y = random.uniform(ENEMY_RADIUS, SCREEN_H - ENEMY_RADIUS)
            if math.hypot(x - self.player_x, y - self.player_y) >= min_dist:
                break
        angle = random.uniform(0, 2*math.pi)
        speed = random.uniform(ENEMY_MIN_SPEED, ENEMY_MAX_SPEED)
        vx = math.cos(angle) * speed
        vy = math.sin(angle) * speed
        self.enemies.append(Enemy(x, y, vx, vy, ENEMY_RADIUS))

    def spawn_heart_pickup(self):
        # spawn away from player
        min_dist = 120
        for _ in range(40):
            x = random.uniform(HEART_RADIUS, SCREEN_W - HEART_RADIUS)
            y = random.uniform(HEART_RADIUS, SCREEN_H - HEART_RADIUS)
            if math.hypot(x - self.player_x, y - self.player_y) >= min_dist:
                break
        self.heart_pickups.append(HeartPickup(x, y, HEART_RADIUS))

    # ---------------- Event handling ----------------
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit_game()
            elif self.state in (STATE_MAIN, STATE_OPTIONS):
                for b in self.buttons:
                    b.handle(event)
            elif self.state == STATE_SELECT:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    pos = event.pos
                    if Rect(20, 100, 140, 44).collidepoint(pos):
                        self.go_options(); return
                    for rect, item in getattr(self, "select_click_targets", []):
                        if rect.collidepoint(pos):
                            self.current_character = item
                            self.load_sheet(item["sheet"])
                            self.reset_player(full_reset=True)
                            self.state = STATE_PLAY
                            return
                elif event.type == pygame.MOUSEWHEEL:
                    self.gallery_scroll -= event.y * 40
                    self.gallery_scroll = max(0, self.gallery_scroll)
            elif self.state == STATE_PAUSE:
                for b in getattr(self, "pause_buttons", []):
                    b.handle(event)
            elif self.state == STATE_PLAY:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.state = STATE_PAUSE
            elif self.state == STATE_GAMEOVER:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                    self.build_main_menu()

            if event.type == pygame.MOUSEMOTION:
                if self.state in (STATE_MAIN, STATE_OPTIONS):
                    for b in self.buttons:
                        b.hover = b.rect.collidepoint(event.pos)

    # ---------------- Update loop ----------------
    def update_play(self, dt):
        # dt in milliseconds
        keys = pygame.key.get_pressed()
        moving = False
        speed = MOVE_SPEED
        dx = dy = 0.0
        if keys[pygame.K_w]:
            dy -= speed * (dt/1000.0); self.direction = DIR_UP; moving = True
        if keys[pygame.K_s]:
            dy += speed * (dt/1000.0); self.direction = DIR_DOWN; moving = True
        if keys[pygame.K_a]:
            dx -= speed * (dt/1000.0); self.direction = DIR_LEFT; moving = True
        if keys[pygame.K_d]:
            dx += speed * (dt/1000.0); self.direction = DIR_RIGHT; moving = True

        self.player_x += dx
        self.player_y += dy

        self.player_x = max(0, min(SCREEN_W, self.player_x))
        self.player_y = max(0, min(SCREEN_H, self.player_y))

        if moving:
            self.anim_timer += dt
            if self.anim_timer >= 120:
                self.anim_timer = 0
                self.anim_idx = (self.anim_idx + 1) % SHEET_COLS
        else:
            self.anim_idx = 1

        # invulnerability countdown
        if self.invuln_timer > 0:
            self.invuln_timer = max(0, self.invuln_timer - dt)

        # spawn enemies rarely
        if random.random() < ENEMY_SPAWN_PER_SECOND * (dt / 1000.0):
            self.spawn_enemy()

        # spawn heart pickups very rarely
        if random.random() < HEART_SPAWN_PER_SECOND * (dt / 1000.0):
            # only spawn if player not at max
            if self.player_hp < self.max_hp:
                self.spawn_heart_pickup()

        # update enemies
        for e in list(self.enemies):
            e.update(dt)
            # collision with player (circular approx)
            pr = max(self.frame_w, self.frame_h) * 0.35 if self.frame_w else 12
            dist = math.hypot(e.x - self.player_x, e.y - self.player_y)
            if dist <= (e.r + pr):
                if self.invuln_timer <= 0:
                    self.player_hp -= 1
                    self.invuln_timer = INVULN_MS
                    # remove this enemy on hit to avoid repeat hits
                    try:
                        self.enemies.remove(e)
                    except ValueError:
                        pass
                    if self.player_hp <= 0:
                        self.state = STATE_GAMEOVER
                        return

        # update heart pickup pickups & collision
        for hp in list(self.heart_pickups):
            dist = math.hypot(hp.x - self.player_x, hp.y - self.player_y)
            pr = max(self.frame_w, self.frame_h) * 0.35 if self.frame_w else 12
            if dist <= (hp.r + pr):
                if self.player_hp < self.max_hp:
                    self.player_hp += 1
                try:
                    self.heart_pickups.remove(hp)
                except ValueError:
                    pass

    # ---------------- Main Loop ----------------
    def run(self):
        while self.running:
            dt = self.clock.tick(FPS)
            self.handle_events()
            if self.state == STATE_MAIN:
                self.draw_main_menu()
            elif self.state == STATE_OPTIONS:
                self.draw_options()
            elif self.state == STATE_SELECT:
                self.draw_select()
            elif self.state == STATE_LOADING:
                self.draw_loading()
            elif self.state == STATE_PLAY:
                self.update_play(dt)
                self.draw_play()
            elif self.state == STATE_PAUSE:
                self.draw_pause()
            elif self.state == STATE_GAMEOVER:
                self.draw_gameover()
            pygame.display.flip()
        pygame.quit()
        sys.exit()

# ----------------------------- ENTRY -----------------------------------
if __name__ == "__main__":
    Game().run()
