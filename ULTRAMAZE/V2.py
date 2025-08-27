import pygame
import random
import sys

# Initialize Pygame
pygame.init()

# Screen dimensions
width, height = 1200, 800
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
goal_x, goal_y = random.randint(0, width - goal_size), random.randint(0, height - goal_size)
player_speed = 5

# Maze settings
cell_size = 40
maze_width = width // cell_size
maze_height = height // cell_size

# Movement keys
controls = {
    "wasd": [pygame.K_w, pygame.K_a, pygame.K_s, pygame.K_d],
    "arrows": [pygame.K_UP, pygame.K_LEFT, pygame.K_DOWN, pygame.K_RIGHT]
}

# Game loop flag
running = True

# Font for level display
font = pygame.font.SysFont(None, 36)

# Game level
level = 1

# Maze generation algorithm (simplified)
def generate_maze():
    # Create an empty grid (0 = open space, 1 = wall)
    maze = [[1] * maze_width for _ in range(maze_height)]

    # Randomly carve out paths (simple algorithm)
    for y in range(maze_height):
        for x in range(maze_width):
            if random.random() > 0.7:
                maze[y][x] = 0  # Make this an open space
    maze[0][0] = 0  # Ensure start is open
    maze[maze_height - 1][maze_width - 1] = 0  # Ensure goal is open

    return maze

# Initialize maze
maze = generate_maze()

# Main game loop
while running:
    screen.fill(BLACK)
    
    # Check for events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Get keys pressed
    keys = pygame.key.get_pressed()
    if keys[controls["wasd"][0]]:  # W key or UP arrow
        player_y -= player_speed
    if keys[controls["wasd"][1]]:  # A key or LEFT arrow
        player_x -= player_speed
    if keys[controls["wasd"][2]]:  # S key or DOWN arrow
        player_y += player_speed
    if keys[controls["wasd"][3]]:  # D key or RIGHT arrow
        player_x += player_speed

    # Prevent player from going out of bounds (within the arena size)
    player_x = max(0, min(player_x, width - player_size))
    player_y = max(0, min(player_y, height - player_size))

    # Check if player reached the goal
    if (player_x < goal_x + goal_size and player_x + player_size > goal_x) and \
       (player_y < goal_y + goal_size and player_y + player_size > goal_y):
        # Increase level and generate new goal and maze
        level += 1
        maze = generate_maze()
        goal_x, goal_y = random.randint(0, width - goal_size), random.randint(0, height - goal_size)

    # Draw maze (walls)
    for y in range(maze_height):
        for x in range(maze_width):
            if maze[y][x] == 1:  # Wall
                pygame.draw.rect(screen, WHITE, (x * cell_size, y * cell_size, cell_size, cell_size))

    # Draw player and goal
    pygame.draw.rect(screen, GREEN, (player_x, player_y, player_size, player_size))
    pygame.draw.rect(screen, RED, (goal_x, goal_y, goal_size, goal_size))

    # Display the current level
    level_text = font.render(f"Level: {level}", True, WHITE)
    screen.blit(level_text, (10, 10))

    # Update display
    pygame.display.flip()

    # Frame rate
    pygame.time.Clock().tick(60)

# Quit Pygame
pygame.quit()
sys.exit()
