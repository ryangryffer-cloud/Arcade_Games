"""
Space Survivor - single-file Python game using pygame

Requirements:
- Python 3.8+
- pygame (pip install pygame)

Controls:
- Arrow keys / A,D: move left/right
- Up / W: move up
- Down / S: move down
- Space: shoot
- P: pause
- Esc or close window: quit

Features:
- Player ship controlled with keyboard
- Enemies spawn with increasing difficulty
- Power-ups (rapid fire, shield)
- Score, lives, and high score persistence (highscore.txt)
- Simple particle explosion effects
- Smooth framerate cap

Save this file and run: python space_survivor.py
Enjoy!
"""

import pygame
import random
import math
import os
from collections import deque

# --------- Configuration ---------
WIDTH, HEIGHT = 800, 600
FPS = 60
PLAYER_SPEED = 300  # pixels per second
BULLET_SPEED = 600
ENEMY_SPEED_BASE = 100
SPAWN_INTERVAL = 1.0  # seconds between enemy spawns (will decrease)
POWERUP_DURATION = 6.0
HIGH_SCORE_FILE = 'highscore.txt'

# Colors
WHITE = (255,255,255)
BLACK = (0,0,0)
GREY = (140,140,140)

# --------- Helper functions ---------

def load_highscore():
    try:
        with open(HIGH_SCORE_FILE, 'r') as f:
            return int(f.read().strip() or 0)
    except Exception:
        return 0


def save_highscore(score):
    try:
        with open(HIGH_SCORE_FILE, 'w') as f:
            f.write(str(score))
    except Exception:
        pass


def clamp(x, a, b):
    return max(a, min(b, x))

# --------- Game objects ---------

class Entity(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.pos = pygame.math.Vector2(x,y)
        self.vel = pygame.math.Vector2(0,0)
        self.image = pygame.Surface((10,10), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(x,y))

    def update(self, dt):
        self.pos += self.vel * dt
        self.rect.center = (round(self.pos.x), round(self.pos.y))

class Player(Entity):
    def __init__(self, x, y):
        super().__init__(x,y)
        self.size = 34
        self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        self._draw_ship()
        self.rect = self.image.get_rect(center=(x,y))
        self.shoot_cooldown = 0.2
        self.shoot_timer = 0
        self.lives = 3
        self.score = 0
        self.rapid_fire = 0.0
        self.shield = 0.0

    def _draw_ship(self):
        surf = self.image
        surf.fill((0,0,0,0))
        w,h = surf.get_size()
        # triangle ship
        pygame.draw.polygon(surf, (50,200,255), [(w/2, 4),(4,h-4),(w-4,h-4)])
        pygame.draw.polygon(surf, (20,120,150), [(w/2, 6),(6,h-6),(w-6,h-6)], 2)

    def update(self, dt, keys):
        vx = 0
        vy = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            vx = -1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            vx = 1
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            vy = -1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            vy = 1
        v = pygame.math.Vector2(vx, vy)
        if v.length_squared() > 0:
            v = v.normalize()
        self.vel = v * PLAYER_SPEED
        super().update(dt)
        # clamp inside screen margins
        margin = 8
        self.pos.x = clamp(self.pos.x, margin, WIDTH - margin)
        self.pos.y = clamp(self.pos.y, margin, HEIGHT - 80)  # reserve bottom HUD
        self.rect.center = (round(self.pos.x), round(self.pos.y))
        # timers
        self.shoot_timer = max(0.0, self.shoot_timer - dt)
        if self.rapid_fire > 0:
            self.rapid_fire = max(0.0, self.rapid_fire - dt)
        if self.shield > 0:
            self.shield = max(0.0, self.shield - dt)

    def can_shoot(self):
        cooldown = 0.06 if self.rapid_fire > 0 else self.shoot_cooldown
        return self.shoot_timer <= 0.0 and self.lives > 0

    def shoot(self):
        self.shoot_timer = 0.06 if self.rapid_fire > 0 else self.shoot_cooldown
        bullet = Bullet(self.pos.x, self.pos.y - self.size/2 - 4, -BULLET_SPEED)
        return bullet

class Bullet(Entity):
    def __init__(self, x, y, vy):
        super().__init__(x,y)
        self.image = pygame.Surface((4,10), pygame.SRCALPHA)
        pygame.draw.rect(self.image, (255,240,100), (0,0,4,10))
        self.rect = self.image.get_rect(center=(x,y))
        self.vel = pygame.math.Vector2(0, vy)

    def update(self, dt):
        super().update(dt)
        # remove if off-screen will be handled by group checks

class Enemy(Entity):
    def __init__(self, x, y, speed, hp=1):
        super().__init__(x,y)
        self.size = 28
        self.image = pygame.Surface((self.size,self.size), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (255,120,120), (self.size//2, self.size//2), self.size//2)
        pygame.draw.circle(self.image, (180,60,60), (self.size//2, self.size//2), self.size//2, 2)
        self.rect = self.image.get_rect(center=(x,y))
        self.vel = pygame.math.Vector2(0, speed)
        self.hp = hp

    def update(self, dt):
        super().update(dt)

class PowerUp(Entity):
    TYPES = ['rapid', 'shield', 'score']
    def __init__(self, x, y, kind=None):
        super().__init__(x,y)
        self.kind = kind or random.choice(PowerUp.TYPES)
        self.size = 20
        self.image = pygame.Surface((self.size,self.size), pygame.SRCALPHA)
        if self.kind == 'rapid':
            pygame.draw.rect(self.image, (200,255,100), (0,0,self.size,self.size))
        elif self.kind == 'shield':
            pygame.draw.rect(self.image, (100,200,255), (0,0,self.size,self.size))
        else:
            pygame.draw.rect(self.image, (255,220,120), (0,0,self.size,self.size))
        self.rect = self.image.get_rect(center=(x,y))
        self.vel = pygame.math.Vector2(0, 90)

    def apply(self, player):
        if self.kind == 'rapid':
            player.rapid_fire = POWERUP_DURATION
        elif self.kind == 'shield':
            player.shield = POWERUP_DURATION
        elif self.kind == 'score':
            player.score += 100

class Particle:
    def __init__(self, x, y, vx, vy, life):
        self.pos = pygame.math.Vector2(x,y)
        self.vel = pygame.math.Vector2(vx,vy)
        self.life = life
        self.maxlife = life

    def update(self, dt):
        self.pos += self.vel * dt
        self.life -= dt

# --------- Game class ---------

class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption('Space Survivor')
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont('dejavusans', 18)
        self.bigfont = pygame.font.SysFont('dejavusans', 36, bold=True)
        self.reset()

    def reset(self):
        self.player = Player(WIDTH/2, HEIGHT - 140)
        self.bullets = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.powerups = pygame.sprite.Group()
        self.all_sprites = pygame.sprite.Group()
        self.spawn_timer = 0.0
        self.spawn_interval = SPAWN_INTERVAL
        self.enemy_speed = ENEMY_SPEED_BASE
        self.running = True
        self.paused = False
        self.particles = []
        self.highscore = load_highscore()
        self.game_over = False
        self.level = 1
        self.time_elapsed = 0.0

    def spawn_enemy(self):
        x = random.uniform(20, WIDTH-20)
        hp = 1 if random.random() < 0.85 else 2
        e = Enemy(x, -30, self.enemy_speed, hp=hp)
        self.enemies.add(e)

    def spawn_powerup(self, x, y):
        p = PowerUp(x,y)
        self.powerups.add(p)

    def create_explosion(self, x, y, amount=12):
        for _ in range(amount):
            ang = random.random()*math.tau
            speed = random.uniform(80, 280)
            vx = math.cos(ang)*speed
            vy = math.sin(ang)*speed
            life = random.uniform(0.4, 1.2)
            self.particles.append(Particle(x,y,vx,vy,life))

    def handle_collisions(self):
        # bullets vs enemies
        for b in list(self.bullets):
            hit = pygame.sprite.spritecollideany(b, self.enemies)
            if hit:
                b.kill()
                hit.hp -= 1
                if hit.hp <= 0:
                    self.player.score += 10 * self.level
                    if random.random() < 0.12:
                        self.spawn_powerup(hit.pos.x, hit.pos.y)
                    self.create_explosion(hit.pos.x, hit.pos.y)
                    hit.kill()
                else:
                    # small damage effect
                    self.create_explosion(hit.pos.x, hit.pos.y, amount=6)

        # enemies vs player
        for e in list(self.enemies):
            if e.rect.colliderect(self.player.rect):
                if self.player.shield > 0:
                    self.create_explosion(e.pos.x, e.pos.y, amount=8)
                    e.kill()
                    self.player.score += 5 * self.level
                else:
                    e.kill()
                    self.create_explosion(self.player.pos.x, self.player.pos.y, amount=24)
                    self.player.lives -= 1
                    if self.player.lives <= 0:
                        self.game_over = True

        # player vs powerups
        for p in list(self.powerups):
            if p.rect.colliderect(self.player.rect):
                p.apply(self.player)
                p.kill()

    def update(self, dt):
        if self.paused or self.game_over:
            return
        keys = pygame.key.get_pressed()
        self.time_elapsed += dt
        # dynamic difficulty
        self.spawn_timer += dt
        if self.spawn_timer >= self.spawn_interval:
            self.spawn_timer = 0.0
            self.spawn_enemy()
        # slowly increase difficulty
        if self.time_elapsed > 10 and self.spawn_interval > 0.35:
            self.spawn_interval = max(0.35, self.spawn_interval - dt*0.002)
        self.enemy_speed = ENEMY_SPEED_BASE + int(self.time_elapsed//10)*8
        # update entities
        self.player.update(dt, keys)
        for s in list(self.bullets):
            s.update(dt)
            if s.pos.y < -20 or s.pos.y > HEIGHT + 20:
                s.kill()
        for e in list(self.enemies):
            e.vel.y = self.enemy_speed
            e.update(dt)
            if e.pos.y > HEIGHT + 40:
                e.kill()
                # penalty for missing
                self.player.lives = max(0, self.player.lives - 0)
        for p in list(self.powerups):
            p.update(dt)
            if p.pos.y > HEIGHT + 20:
                p.kill()
        # spawn occasional bonus enemy waves
        if random.random() < 0.008:
            # swarm
            cx = random.uniform(80, WIDTH-80)
            for i in range(3):
                ex = cx + (i-1)*36
                e = Enemy(ex, -40 - i*10, self.enemy_speed + 30, hp=1)
                self.enemies.add(e)
        # handle shooting
        if (keys[pygame.K_SPACE] or keys[pygame.K_z]) and self.player.can_shoot():
            b = self.player.shoot()
            self.bullets.add(b)
        # collisions
        self.handle_collisions()
        # particles
        for p in list(self.particles):
            p.update(dt)
            if p.life <= 0:
                self.particles.remove(p)
        # level up occasionally
        new_level = 1 + int(self.time_elapsed//25)
        if new_level != self.level:
            self.level = new_level
            # small reward
            self.player.score += 50 * self.level

    def draw_hud(self):
        # bottom HUD strip
        hud_h = 80
        rect = pygame.Rect(0, HEIGHT-hud_h, WIDTH, hud_h)
        pygame.draw.rect(self.screen, (20,20,20), rect)
        pygame.draw.line(self.screen, GREY, (0, HEIGHT-hud_h), (WIDTH, HEIGHT-hud_h), 2)
        # lives
        life_text = self.font.render(f'Lives: {self.player.lives}', True, WHITE)
        self.screen.blit(life_text, (12, HEIGHT-hud_h+10))
        score_text = self.font.render(f'Score: {self.player.score}', True, WHITE)
        self.screen.blit(score_text, (12, HEIGHT-hud_h+36))
        level_text = self.font.render(f'Level: {self.level}', True, WHITE)
        self.screen.blit(level_text, (150, HEIGHT-hud_h+10))
        high_text = self.font.render(f'High: {self.highscore}', True, WHITE)
        self.screen.blit(high_text, (260, HEIGHT-hud_h+10))
        # powerup timers
        if self.player.rapid_fire > 0:
            t = round(self.player.rapid_fire,1)
            rf = self.font.render(f'Rapid: {t}s', True, WHITE)
            self.screen.blit(rf, (360, HEIGHT-hud_h+10))
        if self.player.shield > 0:
            t = round(self.player.shield,1)
            sf = self.font.render(f'Shield: {t}s', True, WHITE)
            self.screen.blit(sf, (460, HEIGHT-hud_h+10))
        # controls small
        ctrl = self.font.render('Arrows/WASD move  Space shoot  P pause', True, GREY)
        self.screen.blit(ctrl, (WIDTH-380, HEIGHT-hud_h+12))

    def draw(self):
        self.screen.fill((5,8,20))
        # stars background
        for i in range(40):
            x = (i*73 + int(self.time_elapsed*30)) % WIDTH
            y = (i*47 % (HEIGHT-80))
            self.screen.fill((255,255,255), (x,y,1,1))
        # draw sprites
        for s in self.enemies:
            self.screen.blit(s.image, s.rect)
        for s in self.bullets:
            self.screen.blit(s.image, s.rect)
        for s in self.powerups:
            self.screen.blit(s.image, s.rect)
        # player with shield overlay
        self.screen.blit(self.player.image, self.player.rect)
        if self.player.shield > 0:
            r = self.player.rect.inflate(20,20)
            pygame.draw.ellipse(self.screen, (100,180,255), r, 3)
        # particles
        for p in self.particles:
            alpha = max(0, min(255, int(255 * (p.life/p.maxlife))))
            r = max(1, int(3 * (p.life/p.maxlife)))
            surf = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (255,200,120,alpha), (r,r), r)
            self.screen.blit(surf, (p.pos.x-r, p.pos.y-r))
        # HUD
        self.draw_hud()
        if self.paused:
            txt = self.bigfont.render('PAUSED', True, (240,240,240))
            self.screen.blit(txt, txt.get_rect(center=(WIDTH/2, HEIGHT/2 - 20)))
        if self.game_over:
            over = self.bigfont.render('GAME OVER', True, (255,80,80))
            sub = self.font.render('Press R to restart    Esc to quit', True, WHITE)
            self.screen.blit(over, over.get_rect(center=(WIDTH/2, HEIGHT/2 - 20)))
            self.screen.blit(sub, sub.get_rect(center=(WIDTH/2, HEIGHT/2 + 24)))

        pygame.display.flip()

    def run(self):
        dt = 0
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                    elif event.key == pygame.K_p:
                        self.paused = not self.paused
                    elif event.key == pygame.K_r and self.game_over:
                        # restart
                        if self.player.score > self.highscore:
                            self.highscore = self.player.score
                            save_highscore(self.highscore)
                        self.reset()
                    elif event.key == pygame.K_RETURN and self.game_over:
                        # also restart with enter
                        if self.player.score > self.highscore:
                            self.highscore = self.player.score
                            save_highscore(self.highscore)
                        self.reset()
            if not self.paused and not self.game_over:
                # allow instant shooting on key held via update
                pass
            self.update(dt)
            self.draw()
        # before exit save highscore
        if self.player.score > self.highscore:
            save_highscore(self.player.score)
        pygame.quit()


if __name__ == '__main__':
    Game().run()
