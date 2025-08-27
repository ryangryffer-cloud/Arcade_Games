import pygame
import random
import time
import sys
import os

# Initialize Pygame
pygame.init()
# Screen dimensions
width, height = 800, 600
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("ULTRA RED DOT")
# Colors
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
# Player and goal settings
player_size = 20
goal_size = 20
player_x, player_y = width // 2, height // 2
goal_x, goal_y = random.randint(0, width - goal_size), random.randint(0, height - goal_size)
player_speed = 4  # Increased player speed
# Game loop flag
running = True
main_menu = True  # Main menu flag
game_started = False  # Game started flag
game_over = False  # Game over flag
# Font for level display
font = pygame.font.SysFont(None, 36)
HIGHSCORE_FILE = "Highscores.txt"
# Example of defining the main_menu_texts
main_menu_texts = ["Start Game", "Options", "Exit"]
# Game level
level = 1
start_time = 0
white_tile = None  # Holds coordinates of the white tile, if any

# Maze settings
cell_size = 20
maze_width = width // cell_size
maze_height = height // cell_size
maze = [[0 for _ in range(maze_width)] for _ in range(maze_height)]  # Simple maze initialization

def draw_text(text, x, y):
    font = pygame.font.Font(None, 36)
    text_surface = font.render(text, True, (255, 255, 255))  # White color for text
    screen = pygame.display.get_surface()
    screen.blit(text_surface, (x, y))

# Main menu text
main_menu_texts = [
    "Welcome to Square Escape!",
    "Press Space to Start a New Game",
    "Press Q to Quit"
]

# Game Over menu text
game_over_menu_texts = [
    "Game Over!",
    "Press Space to Start a New Game",
    "Press M to Return to Main Menu"
]

# Main Menu
def main_menu_screen():
    """Display the main menu."""
    for i, line in enumerate(main_menu_texts):
        draw_text(line, 50, 100 + 40 * i)  # Updated position: closer to the top-left
    pygame.display.flip()

# Game Over Screen
def game_over_screen(elapsed_time):
    """Display the game over screen and top 10 highscores."""
    screen.fill(BLACK)  # Clear the screen

    # Draw the game over messages
    for i, line in enumerate(game_over_menu_texts):
        draw_text(line, width // 2 - 150, height // 3 + 50 * i)

    # Draw the player's final stats
    level_text = font.render(f"Level Reached: {level}", True, WHITE)
    time_text = font.render(f"Time: {elapsed_time} seconds", True, WHITE)
    screen.blit(level_text, (width // 2 - 100, height // 3 + 150))
    screen.blit(time_text, (width // 2 - 100, height // 3 + 200))

    # Draw the top 10 highscores
    draw_text("Top 10 Scores", width // 2 - 100, height // 3 + 250)
    top_scores = get_top_highscores()
    for i, (score_level, score_time) in enumerate(top_scores):
        draw_text(
            f"{i + 1}. Level {score_level}, Time {score_time}s",
            width // 2 - 150,
            height // 3 + 280 + 30 * i,
        )

    pygame.display.flip()  # Update the display

def append_highscore(level, elapsed_time):
    """Append the player's score to the Highscores.txt file."""
    with open(HIGHSCORE_FILE, "a") as file:
        file.write(f"{level},{elapsed_time}\n")

def get_top_highscores(limit=10):
    """Read, sort, and return the top scores from the Highscores.txt file."""
    if not os.path.exists(HIGHSCORE_FILE):
        return []  # If the file doesn't exist, return an empty list

    scores = []
    with open(HIGHSCORE_FILE, "r") as file:
        for line in file:
            try:
                level, time = map(int, line.strip().split(","))
                scores.append((level, time))
            except ValueError:
                continue  # Skip malformed lines

    # Sort by level (descending), then by time (ascending)
    scores.sort(key=lambda x: (-x[0], x[1]))
    return scores[:limit]  # Return the top `limit` scores

def display_highscores():
    """Display the top scores on the game over screen."""
    top_scores = get_top_highscores()
    draw_text("Top 10 Scores", width // 2 - 100, height // 3 - 50)
    for i, (level, time) in enumerate(top_scores):
        draw_text(f"{i + 1}. Level {level}, Time {time}s", width // 2 - 150, height // 3 + 30 * (i + 1))

def generate_white_tile():
    """Generate a white tile after level 5."""
    global white_tile
    if level > 5 and white_tile is None:
        x = random.randint(0, maze_width - 1)
        y = random.randint(0, maze_height - 1)
        white_tile = (x, y)

def check_for_white_tile_collision():
    """Check if the player touches a white tile on any of the sides."""
    global game_over
    if white_tile:
        wx, wy = white_tile
        if (player_x // cell_size == wx and player_y // cell_size == wy) or \
           (player_x // cell_size == wx and (player_y // cell_size - 1) == wy) or \
           ((player_x // cell_size - 1) == wx and player_y // cell_size == wy):
            game_over = True

# Game loop
while running:
    screen.fill(BLACK)

    if main_menu:
        main_menu_screen()
    else:
        if game_over:
            elapsed_time = int(time.time() - start_time)
            game_over_screen(elapsed_time)
        else:
            # Game logic and player controls
            elapsed_time = int(time.time() - start_time)

            # Get keys pressed
            keys = pygame.key.get_pressed()
            if keys[pygame.K_w]:  # W key or UP arrow
                player_y -= player_speed
            if keys[pygame.K_a]:  # A key or LEFT arrow
                player_x -= player_speed
            if keys[pygame.K_s]:  # S key or DOWN arrow
                player_y += player_speed
            if keys[pygame.K_d]:  # D key or RIGHT arrow
                player_x += player_speed

            # Prevent player from going out of bounds
            player_x = max(0, min(player_x, width - player_size))
            player_y = max(0, min(player_y, height - player_size))

            # Check if player reaches the goal
            if (player_x < goal_x + goal_size and player_x + player_size > goal_x) and \
               (player_y < goal_y + goal_size and player_y + player_size > goal_y):
                # Increase level and generate new goal
                level += 1
                goal_x, goal_y = random.randint(0, width - goal_size), random.randint(0, height - goal_size)
                pygame.display.flip() 

            # Generate white tile after level 5
            generate_white_tile()

            # Draw maze with white tile if any
            for y in range(maze_height):
                for x in range(maze_width):
                    if (x, y) == white_tile:
                        pygame.draw.rect(screen, WHITE, (x * cell_size, y * cell_size, cell_size, cell_size))
                    pygame.draw.rect(screen, BLACK, (x * cell_size, y * cell_size, cell_size, cell_size))

            # Draw player and goal
            pygame.draw.rect(screen, GREEN, (player_x, player_y, player_size, player_size))
            pygame.draw.rect(screen, RED, (goal_x, goal_y, goal_size, goal_size))

            # Display the current level and elapsed time
            level_text = font.render(f"Level: {level}", True, WHITE)
            time_text = font.render(f"Time: {elapsed_time} seconds", True, WHITE)
            screen.blit(level_text, (10, 10))
            screen.blit(time_text, (10, 50))

            # Check for white tile collision
            check_for_white_tile_collision()

            pygame.display.flip()

    # Handle user input
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if main_menu:
                if event.key == pygame.K_SPACE:  # Start the game
                    main_menu = False
                    start_time = time.time()
                    level = 1
                    player_x, player_y = width // 2, height // 2
                    goal_x, goal_y = random.randint(0, width - goal_size), random.randint(0, height - goal_size)
                    pygame.display.flip()
                elif event.key == pygame.K_q:  # Quit the game
                    running = False
            elif game_over:
                if event.key == pygame.K_SPACE:  # Restart game
                    game_over = False
                    main_menu = False
                    start_time = time.time()
                    level = 1
                    player_x, player_y = width // 2, height // 2
                    goal_x, goal_y = random.randint(0, width - goal_size), random.randint(0, height - goal_size)
                    pygame.display.flip()
                elif event.key == pygame.K_m:  # Return to main menu
                    game_over = False
                    main_menu = True
                    player_x, player_y = width // 2, height // 2
                    pygame.display.flip()

    pygame.display.flip()
    pygame.time.Clock().tick(60)

# Quit Pygame
pygame.quit()
sys.exit()
