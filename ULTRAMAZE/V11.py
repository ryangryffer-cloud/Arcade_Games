import pygame
import random
import time
import sys

# Initialize Pygame
pygame.init()

# Screen dimensions
screen_width, screen_height = 1400, 900
ui_height = 50  # Reserved area at the top for UI
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Super hard maze game")

# Colors
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
BLUE = (0, 0, 255)

# Player and goal settings
player_size = 20  # Player size
goal_size = 20  # Goal size
player_speed = 2  # Speed at which the player moves

# Flags and counters
running = True
game_over = False
main_menu = True
level = 1
start_time = 0
elapsed_time = 0
maze = []
coins_collected = 0  # Count of coins collected

# Maze settings
cell_size = 40 - level  # Size of each cell in the maze
maze_width = screen_width // cell_size  # Number of cells horizontally
maze_height = (screen_height - ui_height) // cell_size  # Number of cells vertically

# Safe zone radius
player_safe_zone_radius = 2  # Safe zone around the player
goal_safe_zone_radius = 1  # Safe zone around the goal

# Font for UI
font = pygame.font.SysFont(None, 36)

# Main menu and game over menu text
main_menu_texts = [
    "Welcome to ULTRA'S Hard Maze Game!",
    "Press Space to Start a New Game",
    "Press Q to Quit",
    "--------------------",
    "The goal of the game",
    "is to reach the goal 100 times.",
    "Do it in the shortest time possible.",
    "--------------------",
    "Created by ULTRAEDGE",
]
game_over_menu_texts = [
    "Game Over!",
    "Press Space to Start a New Game",
    "Press M to Return to Main Menu",
]

# Coin settings
coin_x, coin_y = None, None  # Coin position
coin_present = False  # Whether a coin is present on the level

# Barrier settings
barrier_active = False
barrier_cost = 5
barrier_rect = None

# Random square settings
random_square_x, random_square_y = None, None
random_square_active = False
random_square_speed = player_speed


def generate_maze():
    """Generate a new maze with safe zones around the player and goal."""
    maze = [[1] * maze_width for _ in range(maze_height)]

    def carve_path(x, y):
        """Recursive function to carve paths in the maze."""
        maze[y][x] = 0
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        random.shuffle(directions)
        for dx, dy in directions:
            nx, ny = x + dx * 2, y + dy * 2
            if 0 <= nx < maze_width and 0 <= ny < maze_height and maze[ny][nx] == 1:
                maze[ny][nx] = 0
                maze[ny - dy][nx - dx] = 0
                carve_path(nx, ny)

    carve_path(1, 1)

    # Create safe zone around the player
    player_start_x, player_start_y = 1, 1
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


def spawn_coin():
    """Spawn a coin randomly in the maze."""
    while True:
        coin_x = random.randint(0, maze_width - 1) * cell_size
        coin_y = random.randint(0, maze_height - 1) * cell_size + ui_height

        # Ensure the coin does not overlap walls or the goal
        if maze[(coin_y - ui_height) // cell_size][coin_x // cell_size] == 0 and (coin_x, coin_y) != (goal_x, goal_y):
            return coin_x, coin_y


def draw_text(text, x, y):
    """Render text on the screen."""
    text_surface = font.render(text, True, WHITE)
    screen.blit(text_surface, (x, y))


def main_menu_screen():
    """Display the main menu."""
    for i, line in enumerate(main_menu_texts):
        draw_text(line, 50, 100 + 40 * i)  # Updated position: closer to the top-left
    pygame.display.flip()


def game_over_screen():
    """Display the game over screen."""
    for i, line in enumerate(game_over_menu_texts):
        draw_text(line, screen_width // 2 - 150, screen_height // 3 + 50 * i)
    level_text = font.render(f"Level Reached: {level}", True, WHITE)
    time_text = font.render(f"Time: {elapsed_time} seconds", True, WHITE)
    screen.blit(level_text, (screen_width // 2 - 100, screen_height // 3 + 150))
    screen.blit(time_text, (screen_width // 2 - 100, screen_height // 3 + 200))
    pygame.display.flip()


# Main game loop
while running:
    screen.fill(BLACK)

    if main_menu:
        main_menu_screen()
    elif game_over:
        game_over_screen()
    else:
        # Update player movement
        keys = pygame.key.get_pressed()
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            player_y -= player_speed
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            player_y += player_speed
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            player_x -= player_speed
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            player_x += player_speed
        if keys[pygame.K_RSHIFT] or keys[pygame.K_LSHIFT]:
            player_speed = 3
        else: 
            player_speed = 2

        # Keep player within bounds
        player_x = max(0, min(player_x, screen_width - player_size))
        player_y = max(ui_height, min(player_y, screen_height - player_size))

        # Check for collision with walls
        if maze[(player_y - ui_height) // cell_size][player_x // cell_size] == 1:
            game_over = True
            elapsed_time = int(time.time() - start_time)

        # Check if the player reaches the goal
        if (
            player_x < goal_x + goal_size
            and player_x + player_size > goal_x
            and player_y < goal_y + goal_size
            and player_y + player_size > goal_y
        ):
            # Move to the next level
            level += 1  # level count goes up.
            player_speed = 2  # Reset player speed
            player_x, player_y = cell_size, ui_height + cell_size  # Reset player position
            maze, goal_x, goal_y = generate_maze()  # Generate a new maze
            goal_y += ui_height  # Adjust for the UI height

            # Spawn coin for levels 6-10
            if 6 <= level <= 10:
                coin_x, coin_y = spawn_coin()
                coin_present = True
            else:
                coin_present = False

            # Activate barrier at level 13
            barrier_active = level = 13

            # Activate random square after level 14
            random_square_active = level >= 14
            if random_square_active:
                random_square_x, random_square_y = goal_x, goal_y

        # Check if the player collects a coin
        if coin_present and (
            player_x < coin_x + player_size
            and player_x + player_size > coin_x
            and player_y < coin_y + player_size
            and player_y + player_size > coin_y
        ):
            coins_collected += 1
            coin_present = False

        # Handle barrier collision
        if barrier_active and (
            player_x < goal_x + goal_size
            and player_x + player_size > goal_x
            and player_y < goal_y + goal_size
            and player_y + player_size > goal_y
        ):
            if coins_collected >= 5:
                coins_collected -= 5
                barrier_active = False
            else:
                game_over = True

        # Update random square movement
        if random_square_active:
            directions = [(0, -1), (0, 1), (-1, 0), (1, 0)]
            random.shuffle(directions)
            for dx, dy in directions:
                new_x = random_square_x + dx * cell_size
                new_y = random_square_y + dy * cell_size
                if 0 <= new_x < screen_width and 0 <= new_y < screen_height:
                    if maze[(new_y - ui_height) // cell_size][new_x // cell_size] == 0:
                        random_square_x, random_square_y = new_x, new_y
                        break

            # Check if random square touches player
            if (
                random_square_x < player_x + player_size
                and random_square_x + player_size > player_x
                and random_square_y < player_y + player_size
                and random_square_y + player_size > player_y
            ):
                game_over = True

        # Draw maze
        for y in range(maze_height):
            for x in range(maze_width):
                if maze[y][x] == 1:
                    pygame.draw.rect(screen, WHITE, (x * cell_size, y * cell_size + ui_height, cell_size, cell_size))

        # Draw player and goal
        pygame.draw.rect(screen, GREEN, (player_x, player_y, player_size, player_size))
        pygame.draw.rect(screen, RED, (goal_x, goal_y, goal_size, goal_size))

        # Draw barrier
        if barrier_active:
            pygame.draw.rect(screen, BLUE, (goal_x - 5, goal_y - 5, goal_size + 10, goal_size + 10), 3)

        # Draw random square
        if random_square_active:
            pygame.draw.rect(screen, WHITE, (random_square_x, random_square_y, player_size, player_size))

        # Draw coin
        if coin_present:
            pygame.draw.circle(screen, YELLOW, (coin_x + player_size // 2, coin_y + player_size // 2), player_size // 2)

        # Update and display elapsed time
        elapsed_time = int(time.time() - start_time)
        draw_text(f"Level: {level}", 10, 10)
        draw_text(f"Time: {elapsed_time} seconds", 10, 30)
        draw_text(f"Coins: {coins_collected}", screen_width - 150, 10)  # Display coin count

    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if main_menu and event.key == pygame.K_SPACE:
                main_menu = False
                start_time = time.time()
                level = 1
                player_speed = 2
                player_x, player_y = cell_size, ui_height + cell_size
                maze, goal_x, goal_y = generate_maze()
                goal_y += ui_height  # Adjust for UI height
                coins_collected = 0  # Reset coin count
                coin_present = False
                barrier_active = False
                random_square_active = False
            elif game_over and event.key == pygame.K_SPACE:
                game_over = False
                start_time = time.time()
                level = 1
                player_speed = 2
                player_x, player_y = cell_size, ui_height + cell_size
                maze, goal_x, goal_y = generate_maze()
                goal_y += ui_height  # Adjust for UI height
                coins_collected = 0  # Reset coin count
                coin_present = False
                barrier_active = False
                random_square_active = False
            elif game_over and event.key == pygame.K_m:
                game_over = False
                main_menu = True

    # Refresh display
    pygame.display.flip()
    pygame.time.Clock().tick(60)

pygame.quit()
sys.exit()
