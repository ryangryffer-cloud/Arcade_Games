import pygame
import sys
import random

# Initialize Pygame
pygame.init()
WIDTH, HEIGHT = 720, 1280  # Portrait screen
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Turn-Based Game")
clock = pygame.time.Clock()

# Fonts
FONT = pygame.font.SysFont("arial", 28)
SMALL_FONT = pygame.font.SysFont("arial", 22)

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (180, 180, 180)
RED = (220, 50, 50)
GREEN = (50, 200, 50)
BLUE = (50, 50, 220)
YELLOW = (240, 240, 50)
PURPLE = (180, 50, 200)

# Game Stats
class Character:
    def __init__(self, name, max_hp, attack, mana=100, level=1):
        self.name = name
        self.max_hp = max_hp
        self.hp = max_hp
        self.base_attack = attack
        self.attack = attack
        self.mana = mana
        self.max_mana = 100
        self.level = level
        self.exp = 0
        self.heal_amount = 15

    def is_alive(self):
        return self.hp > 0

    def take_damage(self, amount):
        self.hp = max(self.hp - amount, 0)

    def heal(self):
        self.hp = min(self.hp + self.heal_amount, self.max_hp)

    def add_exp(self, amount):
        self.exp += amount
        if self.exp >= 100:
            self.exp -= 100
            self.level += 1
            return True
        return False

    def fireball(self):
        if self.mana >= 50:
            self.mana -= 50
            return 100
        return 0

    def meditate(self):
        self.mana = min(self.max_mana, self.mana + 40)

# Button Class
class Button:
    def __init__(self, text, x, y, w, h, action):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.action = action

    def draw(self, surface):
        pygame.draw.rect(surface, GRAY, self.rect)
        pygame.draw.rect(surface, BLACK, self.rect, 2)
        txt = FONT.render(self.text, True, BLACK)
        surface.blit(txt, (self.rect.x + 10, self.rect.y + 10))

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)

# Log
log_messages = []
log_scroll = 0
def log(text, color=WHITE):
    log_messages.append((text, color))

# Game Entities
player = Character("Player", 100, 20)
enemy_count = 0
def spawn_enemy():
    level = (player.level // 2) + 1
    hp = 70 + (level - 1) * 30
    atk = 15 + (level - 1) * 5
    return Character(f"Enemy Lv.{level}", hp, atk)

enemy = spawn_enemy()
turn = "player"
enemy_action_pending = False
enemy_action_timer = 0
level_up_choice = None
game_over = False

# Buttons
buttons = [
    Button("Attack", 50, HEIGHT - 300, 250, 60, "attack"),
    Button("Heal", 420, HEIGHT - 300, 250, 60, "heal"),
    Button("Fireball", 50, HEIGHT - 220, 250, 60, "fireball"),
    Button("Meditate", 420, HEIGHT - 220, 250, 60, "meditate")
]

# Level up UI
upgrade_buttons = [
    Button("Increase Attack", 100, HEIGHT // 2 - 80, 500, 60, "upgrade_attack"),
    Button("Increase Heal", 100, HEIGHT // 2 + 20, 500, 60, "upgrade_heal")
]

# Drawing Functions
def draw_bar(x, y, w, h, current, max_value, color, label):
    pygame.draw.rect(screen, (50, 50, 50), (x, y, w, h))
    fill_width = int((current / max_value) * w)
    pygame.draw.rect(screen, color, (x, y, fill_width, h))
    text = SMALL_FONT.render(f"{label}: {current}/{max_value}", True, WHITE)
    screen.blit(text, (x + 10, y + h // 2 - 10))

def draw_character_stats():
    draw_bar(40, 40, 640, 30, player.hp, player.max_hp, RED, "HP")
    draw_bar(40, 90, 640, 20, player.mana, player.max_mana, BLUE, "Mana")
    draw_bar(40, 130, 640, 20, player.exp, 100, YELLOW, "EXP")

    enemy_hp_width = min(600, enemy.max_hp * 2)
    draw_bar(60, 200, enemy_hp_width, 25, enemy.hp, enemy.max_hp, RED, f"{enemy.name}")

def draw_log():
    area = pygame.Rect(40, 250, WIDTH - 80, 300)
    pygame.draw.rect(screen, (30, 30, 30), area)
    pygame.draw.rect(screen, WHITE, area, 2)
    visible_lines = 10
    start = max(0, len(log_messages) - visible_lines - log_scroll)
    end = len(log_messages) - log_scroll
    displayed = log_messages[start:end]
    for i, (msg, color) in enumerate(displayed):
        txt = SMALL_FONT.render(msg, True, color)
        screen.blit(txt, (area.x + 10, area.y + 10 + i * 28))

# Main Game Loop
while True:
    screen.fill(BLACK)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        # Scroll log
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 4: log_scroll = max(0, log_scroll - 1)
            elif event.button == 5:
                if log_scroll < len(log_messages) - 10:
                    log_scroll += 1

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP: log_scroll = max(0, log_scroll - 1)
            if event.key == pygame.K_DOWN:
                if log_scroll < len(log_messages) - 10:
                    log_scroll += 1

        # Input
        if event.type == pygame.MOUSEBUTTONDOWN and not game_over:
            pos = pygame.mouse.get_pos()

            # Level up
            if level_up_choice:
                for btn in upgrade_buttons:
                    if btn.is_clicked(pos):
                        if btn.action == "upgrade_attack":
                            player.base_attack += 5
                            log("Attack power increased!", GREEN)
                        elif btn.action == "upgrade_heal":
                            player.heal_amount += 5
                            log("Healing power increased!", GREEN)
                        player.attack = player.base_attack
                        level_up_choice = None
                        turn = "enemy"
                        enemy_action_pending = True
                        enemy_action_timer = pygame.time.get_ticks()

            # Actions
            elif turn == "player":
                for btn in buttons:
                    if btn.is_clicked(pos):
                        if btn.action == "attack":
                            enemy.take_damage(player.attack)
                            log(f"You attack for {player.attack} damage!", WHITE)
                            turn = "enemy"
                            enemy_action_pending = True
                            enemy_action_timer = pygame.time.get_ticks()
                        elif btn.action == "heal":
                            player.heal()
                            log(f"You heal for {player.heal_amount} HP!", GREEN)
                            turn = "enemy"
                            enemy_action_pending = True
                            enemy_action_timer = pygame.time.get_ticks()
                        elif btn.action == "fireball":
                            dmg = player.fireball()
                            if dmg > 0:
                                enemy.take_damage(dmg)
                                log(f"You cast Fireball for {dmg} damage!", PURPLE)
                                turn = "enemy"
                                enemy_action_pending = True
                                enemy_action_timer = pygame.time.get_ticks()
                            else:
                                log("Not enough mana!", RED)
                        elif btn.action == "meditate":
                            player.meditate()
                            log("You meditate and restore mana.", BLUE)
                            turn = "enemy"
                            enemy_action_pending = True
                            enemy_action_timer = pygame.time.get_ticks()

    # Enemy Turn
    if turn == "enemy" and enemy_action_pending and not game_over:
        if pygame.time.get_ticks() - enemy_action_timer > 1000:
            player.take_damage(enemy.attack)
            log(f"{enemy.name} attacks for {enemy.attack}!", RED)
            if not player.is_alive():
                log("You have been defeated!", RED)
                game_over = True
            turn = "player"
            enemy_action_pending = False

    # Enemy defeated
    if not enemy.is_alive() and not game_over:
        log(f"{enemy.name} defeated!", YELLOW)
        player_gained_level = player.add_exp(20)
        enemy_count += 1
        if player_gained_level:
            log("You leveled up!", GREEN)
            level_up_choice = True
        else:
            enemy = spawn_enemy()

    # Draw Everything
    draw_character_stats()
    draw_log()

    if level_up_choice:
        for btn in upgrade_buttons:
            btn.draw(screen)
    elif not game_over and turn == "player":
        for btn in buttons:
            btn.draw(screen)

    pygame.display.flip()
    clock.tick(60)
