import pygame
import random
import time
import sys

# Initialize Pygame
pygame.init()

# Screen dimensions
width, height = 1400, 900
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Square Escape with Maze")

# Colors
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)

# Player and goal settings
player_size = 30
goal_size = 30
player_x, player_y = width // 2, height // 2
player_speed = 5

# Maze settings
cell_size = 40
maze_width = width // cell_size
maze_height = height // cell_size

# Safe zone radius
player_safe_zone_radius = 3  # Safe zone around the player
goal_safe_zone_radius = 2  # Safe zone around the goal

# Movement keys
controls = {
    "wasd": [pygame.K_w, pygame.K_a, pygame.K_s, pygame.K_d],
    "arrows": [pygame.K_UP, pygame.K_LEFT, pygame.K_DOWN, pygame.K_RIGHT],
}

# Font for UI
font = pygame.font.SysFont(None, 36)

# Main menu and game over menu text
main_menu_texts = [
    "Welcome to Square Escape!",
    "Press Space to Start a New Game",
    "Press Q to Quit",
]
game_over_menu_texts = [
    "Game Over!",
    "Press Space to Start a New Game",
    "Press M to Return to Main Menu",
]

# Flags and counters
running = True
game_over = False
main_menu = True
level = 1
start_time = 0
elapsed_time = 0
maze = []


def generate_maze():
    """Generate a new maze with safe zones around the player and goal."""
    maze = [[1] * maze_width for _ in range(maze_height)]

    def carve_path(x, y):
        maze[y][x] = 0
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        random.shuffle(directions)
        for dx, dy in directions:
            nx, ny = x + dx * 2, y + dy * 2
            if 0 <= nx < maze_width and 0 <= ny < maze_height and maze[ny][nx] == 1:
                maze[ny][nx] = 0
                maze[ny - dy][nx - dx] = 0
                carve_path(nx, ny)

    # Start carving from the top left corner
    carve_path(1, 1)

    # Create safe zone around the player
    player_start_x, player_start_y = player_x // cell_size, player_y // cell_size
    for y in range(player_start_y - player_safe_zone_radius, player_start_y + player_safe_zone_radius + 1):
        for x in range(player_start_x - player_safe_zone_radius, player_start_x + player_safe_zone_radius + 1):
            if 0 <= x < maze_width and 0 <= y < maze_height:
                maze[y][x] = 0

    # Place goal in a safe zone
    while True:
        goal_start_x = random.randint(0, maze_width - 1)
        goal_start_y = random.randint(0, maze_height - 1)

        if maze[goal_start_y][goal_start_x] == 0:
            for y in range(goal_start_y - goal_safe_zone_radius, goal_start_y + goal_safe_zone_radius + 1):
                for x in range(goal_start_x - goal_safe_zone_radius, goal_start_x + goal_safe_zone_radius + 1):
                    if 0 <= x < maze_width and 0 <= y < maze_height:
                        maze[y][x] = 0
            break

    return maze, goal_start_x * cell_size, goal_start_y * cell_size


def draw_text(text, x, y):
    """Render text on the screen."""
    text_surface = font.render(text, True, WHITE)
    screen.blit(text_surface, (x, y))


def main_menu_screen():
    """Display the main menu."""
    for i, line in enumerate(main_menu_texts):
        draw_text(line, width // 2 - 150, height // 3 + 50 * i)
    pygame.display.flip()


def game_over_screen():
    """Display the game over screen."""
    for i, line in enumerate(game_over_menu_texts):
        draw_text(line, width // 2 - 150, height // 3 + 50 * i)
    level_text = font.render(f"Level Reached: {level}", True, WHITE)
    time_text = font.render(f"Time: {elapsed_time} seconds", True, WHITE)
    screen.blit(level_text, (width // 2 - 100, height // 3 + 150))
    screen.blit(time_text, (width // 2 - 100, height // 3 + 200))
    pygame.display.flip()


# Main game loop
while running:
    screen.fill(BLACK)

    if main_menu:
        main_menu_screen()
    elif game_over:
        game_over_screen()
    else:
        # Get keys pressed
        keys = pygame.key.get_pressed()
        if keys[controls["wasd"][0]] or keys[controls["arrows"][0]]:  # Up
            player_y -= player_speed
        if keys[controls["wasd"][1]] or keys[controls["arrows"][1]]:  # Left
            player_x -= player_speed
        if keys[controls["wasd"][2]] or keys[controls["arrows"][2]]:  # Down
            player_y += player_speed
        if keys[controls["wasd"][3]] or keys[controls["arrows"][3]]:  # Right
            player_x += player_speed

        # Clamp player within the screen
        player_x = max(0, min(player_x, width - player_size))
        player_y = max(0, min(player_y, height - player_size))

        # Check for wall collision
        if maze[player_y // cell_size][player_x // cell_size] == 1:
            game_over = True
            elapsed_time = int(time.time() - start_time)

        # Check if player reached the goal
        if (player_x < goal_x + goal_size and player_x + player_size > goal_x) and \
           (player_y < goal_y + goal_size and player_y + player_size > goal_y):
            level += 1
            maze, goal_x, goal_y = generate_maze()

        # Draw maze, player, and goal
        for y in range(maze_height):
            for x in range(maze_width):
                if maze[y][x] == 1:
                    pygame.draw.rect(screen, WHITE, (x * cell_size, y * cell_size, cell_size, cell_size))

        pygame.draw.rect(screen, GREEN, (player_x, player_y, player_size, player_size))
        pygame.draw.rect(screen, RED, (goal_x, goal_y, goal_size, goal_size))

        # Display level and time
        elapsed_time = int(time.time() - start_time)
        draw_text(f"Level: {level}", 10, 10)
        draw_text(f"Time: {elapsed_time} seconds", 10, 50)

        pygame.display.flip()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if main_menu and event.key == pygame.K_SPACE:
                main_menu = False
                start_time = time.time()
                level = 1
                player_x, player_y = width // 2, height // 2
                maze, goal_x, goal_y = generate_maze()
            elif game_over and event.key == pygame.K_SPACE:
                game_over = False
                start_time = time.time()
                level = 1
                player_x, player_y = width // 2, height // 2
                maze, goal_x, goal_y = generate_maze()
            elif game_over and event.key == pygame.K_m:
                game_over = False
                main_menu = True

    pygame.time.Clock().tick(60)

pygame.quit()
sys.exit()
