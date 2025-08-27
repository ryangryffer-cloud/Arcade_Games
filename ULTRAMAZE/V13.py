import pygame
import random
import time
import sys
import os

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
player_size = 10  # Player size
goal_size = 20  # Goal size
player_speed = 1  # Speed at which the player moves

# Other global variables 
random_square_size = 10 
player_safe_zone_radius = 2  
goal_safe_zone_radius = 1  # Safe zone around the goal
HIGHSCORE_FILE = "Highscores.txt"

# Flags and counters
running = True
game_over = False
main_menu = True
player_moving = False 
level = 1
start_time = 0
elapsed_time = 0
maze = []
Ycoins_collected = 0  # Count of Ycoins collected
Bcoins_collected = 0 # count of Bcoins collected 
level_initialized = False
level_message = ""

#enemy variables
stationary_enemy_active = False
stationary_enemy_x, stationary_enemy_y = None, None
projectile_active = False
projectile_x, projectile_y = None, None
projectile_speed = 5  # Speed of the projectile#projectile_direction = (0, 0)  # Direction of projectile movement
#Random square settings
random_square_target_x, random_square_target_y = None, None
random_square_x, random_square_y = None, None
random_square_active = False
# Random square enemies
num_enemies = 0
random_squares = []  # List to store enemy attributes
random_square_speed = 1  # Speed for all random squares


# Maze settings
cell_size = 40 # Size of each cell in the maze
maze_width = screen_width // cell_size  # Number of cells horizontally
maze_height = (screen_height - ui_height) // cell_size  # Number of cells vertically

# Font for UI
font = pygame.font.SysFont(None, 30)

# Yellow Coin settings
Ycoin_x, Ycoin_y = None, None  # YCoin position
Ycoin_present = False  # Whether a Ycoin is present on the level
# Blue coin settings
Bcoin_x, Bcoin_y = None, None  # BCoin position
Bcoin_present = False  # Whether a Bcoin is present on the level
# Barrier settings
Ybarrier_active = False
Ybarrier_cost = 5
Ybarrier_rect = None
Bbarrier_active = False
Bbarrier_cost = 5
Bbarrier_rect = None

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
    draw_text("Top 10 Scores", screen_width // 2 - 100, screen_height // 3 - 50)
    for i, (level, time) in enumerate(top_scores):
        draw_text(f"{i + 1}. Level {level}, Time {time}s", screen_width // 2 - 150, screen_height // 3 + 30 * (i + 1))

def generate_maze_normal(player_start_x, player_start_y):
    """Generate a new maze with safe zones around the player and goal."""
    maze = [[1] * maze_width for _ in range(maze_height)]

    def carve_path(x, y):
        """Recursive function to carve paths in the maze."""
        maze[y][x] = 0
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]  # Down, Right, Up, Left
        random.shuffle(directions)
        for dx, dy in directions:
            nx, ny = x + dx * 2, y + dy * 2
            if 0 <= nx < maze_width and 0 <= ny < maze_height and maze[ny][nx] == 1:
                maze[ny][nx] = 0
                maze[ny - dy][nx - dx] = 0
                carve_path(nx, ny)

    # Start carving from the top-left corner
    carve_path(1, 1)

    # Create a safe zone around the player's start position
    for y in range(player_start_y - player_safe_zone_radius, player_start_y + player_safe_zone_radius + 1):
        for x in range(player_start_x - player_safe_zone_radius, player_start_x + player_safe_zone_radius + 1):
            if 0 <= x < maze_width and 0 <= y < maze_height:
                maze[y][x] = 0

    # Place the goal in a random safe zone
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

def spawn_Ycoin():
    """Spawn a Yellow coin randomly in the maze."""
    while True:
        Ycoin_x = random.randint(0, maze_width - 1) * cell_size
        Ycoin_y = random.randint(0, maze_height - 1) * cell_size + ui_height

        # Ensure the Ycoin does not overlap walls or the goal
        if maze[(Ycoin_y - ui_height) // cell_size][Ycoin_x // cell_size] == 0 and (Ycoin_x, Ycoin_y) != (goal_x, goal_y):
            return Ycoin_x, Ycoin_y
        
def spawn_Bcoin():
    """Spawn a Blue coin randomly in the maze."""
    while True:
        Bcoin_x = random.randint(0, maze_width - 1) * cell_size
        Bcoin_y = random.randint(0, maze_height - 1) * cell_size + ui_height

        # Ensure the Bcoin does not overlap walls or the goal
        if maze[(Bcoin_y - ui_height) // cell_size][Bcoin_x // cell_size] == 0 and (Bcoin_x, Bcoin_y) != (goal_x, goal_y):
            return Bcoin_x, Bcoin_y

def Spawn_Squares(): #enemy square Spawning    
        if num_enemies >=1 :
            for _ in range(num_enemies):
                while True:
                    enemy_x = random.randint(0, maze_width - 1) * cell_size
                    enemy_y = random.randint(0, maze_height - 1) * cell_size + ui_height

                    # Ensure the enemy spawns in an open cell
                    if maze[(enemy_y - ui_height) // cell_size][enemy_x // cell_size] == 0:
                        random_squares.append({
                            "position": (enemy_x, enemy_y),  # Current position
                            "target": (enemy_x, enemy_y),  # Initial target
                        })
                        break

def draw_text(text, x, y):
    """Render text on the screen."""
    text_surface = font.render(text, True, WHITE)
    screen.blit(text_surface, (x, y))

def is_colliding_with_wall(player_x, player_y):
    """Check if any corner of the player is colliding with a wall."""
    # Calculate player's corners
    corners = [
        (player_x, player_y),  # Top-left
        (player_x + player_size - 1, player_y),  # Top-right
        (player_x, player_y + player_size - 1),  # Bottom-left
        (player_x + player_size - 1, player_y + player_size - 1),  # Bottom-right
    ]

    # Check each corner against the maze grid
    for corner_x, corner_y in corners:
        # Convert corner position to maze cell coordinates
        maze_x = corner_x // cell_size
        maze_y = (corner_y - ui_height) // cell_size  # Adjust for UI height

        # Check if the corner is inside a wall
        if (
            0 <= maze_x < maze_width
            and 0 <= maze_y < maze_height
            and maze[maze_y][maze_x] == 1  # 1 indicates a wall
        ):
            return True  # Collision detected

    return False  # No collision

#Main Menu Texts 
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
#Main Menu Screen 
def main_menu_screen():
    """Display the main menu."""
    for i, line in enumerate(main_menu_texts):
        draw_text(line, 50, 100 + 40 * i)  # Updated position: closer to the top-left
    pygame.display.flip()
#Game over TEXT
game_over_menu_texts = [
    "Game Over!",
    "Press Space to Start a New Game",
    "Press M to Return to Main Menu",
]
#Game Over screen 
def game_over_screen():
    """Display the game over screen and top 10 highscores."""
    screen.fill(BLACK)  # Clear the screen

    # Draw the game over messages
    for i, line in enumerate(game_over_menu_texts):
        draw_text(line, screen_width // 2 - 150, screen_height // 3 + 50 * i)

    # Draw the player's final stats
    level_text = font.render(f"Level Reached: {level}", True, WHITE)
    time_text = font.render(f"Time: {elapsed_time} seconds", True, WHITE)
    screen.blit(level_text, (screen_width // 2 - 100, screen_height // 3 + 150))
    screen.blit(time_text, (screen_width // 2 - 100, screen_height // 3 + 200))

    # Draw the top 10 highscores
    draw_text("Top 10 Scores", screen_width // 2 - 100, screen_height // 3 + 250)
    top_scores = get_top_highscores()
    for i, (score_level, score_time) in enumerate(top_scores):
        draw_text(
            f"{i + 1}. Level {score_level}, Time {score_time}s",
            screen_width // 2 - 150,
            screen_height // 3 + 280 + 30 * i,
        )

    pygame.display.flip()  # Update the display

# random square movement
def move_single_random_square(enemy):
    """Move a single random square (enemy) towards its target."""
    # Extract enemy attributes
    random_square_x, random_square_y = enemy["position"]
    random_square_target_x, random_square_target_y = enemy["target"]

    # If the square has reached its target, pick a new target
    if random_square_x == random_square_target_x and random_square_y == random_square_target_y:
        current_x = random_square_x // cell_size
        current_y = (random_square_y - ui_height) // cell_size

        # Possible directions: (dx, dy)
        directions = [(0, -1), (0, 1), (-1, 0), (1, 0)]  # Up, Down, Left, Right
        random.shuffle(directions)  # Shuffle for randomness

        for dx, dy in directions:
            new_x = current_x + dx
            new_y = current_y + dy

            # Ensure the new position is within bounds and not a wall
            if (
                0 <= new_x < maze_width
                and 0 <= new_y < maze_height
                and maze[new_y][new_x] == 0  # Check if the cell is open (not a wall)
            ):
                enemy["target"] = (new_x * cell_size, new_y * cell_size + ui_height)
                break

    # Gradually move towards the target position
    target_x, target_y = enemy["target"]
    if random_square_x < target_x:
        random_square_x += random_square_speed
    elif random_square_x > target_x:
        random_square_x -= random_square_speed

    if random_square_y < target_y:
        random_square_y += random_square_speed
    elif random_square_y > target_y:
        random_square_y -= random_square_speed

    # Update the enemy's position
    enemy["position"] = (random_square_x, random_square_y)

# Main game loop
while running:
    screen.fill(BLACK)  # Clear the screen

    if main_menu:
        main_menu_screen()
    elif game_over:
    # Save the score only once
        if not score_saved:
            append_highscore(level, elapsed_time)
            score_saved = True

        # Display the game over screen
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
        if is_colliding_with_wall(player_x, player_y):
            game_over = True
            elapsed_time = int(time.time() - start_time)
        if stationary_enemy_active and not projectile_active:
            # Check if the player enters the safe zone near the goal
            if (
                player_x >= goal_x - goal_safe_zone_radius * cell_size
                and player_x <= goal_x + goal_safe_zone_radius * cell_size
                and player_y >= goal_y - goal_safe_zone_radius * cell_size
                and player_y <= goal_y + goal_safe_zone_radius * cell_size
            ):
                # Fire the projectile
                projectile_active = True
                projectile_x, projectile_y = stationary_enemy_x, stationary_enemy_y

                # Calculate direction from enemy to player
                dx = player_x - stationary_enemy_x
                dy = player_y - stationary_enemy_y
                distance = (dx**2 + dy**2) ** 0.5
                projectile_direction = (dx / distance, dy / distance)

        # Check if the player reaches the goal
        if (
            player_x < goal_x + goal_size
            and player_x + player_size > goal_x
            and player_y < goal_y + goal_size
            and player_y + player_size > goal_y
        ):
            # Move to the next level
            level += 1  # Increment level
            level_initialized = False
            # Generate a new maze with the player's safe zone at the previous goal
            player_safe_zone_x = goal_x // cell_size
            player_safe_zone_y = (goal_y - ui_height) // cell_size  # Set safe zone to previous goal position
            maze, goal_x, goal_y = generate_maze_normal(player_safe_zone_x, player_safe_zone_y)
            goal_y += ui_height  # Adjust for UI height
           
        # Update and display elapsed time
        elapsed_time = int(time.time() - start_time)
        draw_text(f"Level: {level}", 10, 10)
        draw_text(f"Time: {elapsed_time} seconds", 10, 30)
        #only show yellow coin counter after the first yellow coin appears.
        if level >=5:
            draw_text(f"Yellow Coins: {Ycoins_collected}", screen_width - 150, 10)  # Display coin count yellow
        #only show blue coin counter after first blue coin appears. 
        if level >=13:
            draw_text(f"Blue Coins: {Bcoins_collected}", screen_width -150, 30) #display coin count Blue
        # level-specific messages and settings. 
        if not level_initialized: 
            if level == 1: 
                level_message = "Move to the red square." # in this level it is only a maze
                random_squares = [] # to reset the random squares. 
                num_enemies = 0
                level_initialized = True # Mark the level as initialized
            if level == 2:
                level_message = " The clock is ticking." # in this level it is only a maze 
                level_initialized = True # Mark the level as initialized
            if level == 3:
                level_message = "There is a special surprise at level 6." # in this level it is only a maze 
                level_initialized = True# Mark the level as initialized
            if level == 4:
                level_message = "It's just a simple maze game." # in this level it is only a maze 
                level_initialized = True # Mark the level as initialized
            if level == 5:
                level_message = "Just keep going."
                level_initialized = True# Mark the level as initialized    
            if level == 6:
                level_message = "There it is!" # This level introduces the yellow coin. 
                Ycoin_x, Ycoin_y = spawn_Ycoin() # Spawn the Yellow coin
                Ycoin_present = True
                level_initialized = True #  Mark the level as initialized   
            if level == 7:
                level_message = "You gotta get the coins! Right?" # in this level there is also a Yellow coin 
                Ycoin_x, Ycoin_y = spawn_Ycoin()
                Ycoin_present = True
                level_initialized = True # Mark the level as initialized 
            if level == 8:
                level_message = "I can't remeber... are the coins optional?" # in this level there is also a Yellow coin 
                Ycoin_x, Ycoin_y = spawn_Ycoin()
                Ycoin_present = True
                level_initialized = True # Mark the level as initialized          
            if level == 9:
                level_message = "I guess it is up to you." # in this level there is also a Yellow coin 
                Ycoin_x, Ycoin_y = spawn_Ycoin()
                Ycoin_present = True
                level_initialized = True # Mark the level as initialized        
            if level == 10:
                level_message = "Hope you got all the coins..." # in this level there is also a Yellow coin 
                Ycoin_x, Ycoin_y = spawn_Ycoin()
                Ycoin_present = True
                level_initialized = True # Mark the level as initialized
            if level == 11:
                level_message = "You greedy little gamer." # in this level it is only a maze 
                level_initialized = True # Mark the level as initialized
            if level == 12:
                level_message = "wow, Level 12. Look at you go." #in this level it is only a maze 
                level_initialized = True # Mark the level as initialized
            if level == 13:
                level_message = "This is an unlucky level." # in this level there is a yellow barrier and a blue coin 
                Bcoin_present = True
                Bcoin_x, Bcoin_y = spawn_Bcoin()
                Ybarrier_active = True
                Ybarrier_rect = pygame.Rect(goal_x - 10, goal_y - 10, goal_size + 20, goal_size + 20)
                level_initialized = True # Mark the level as initialized       
            if level == 14:
                level_message = "Better not touch those guys." # in this level there is a blue coin with one enemy 
                Bcoin_present = True
                Bcoin_x, Bcoin_y = spawn_Bcoin()
                random_squares = [] # to reset the random squares. 
                num_enemies = 1
                Spawn_Squares()
                level_initialized = True # Mark the level as initialized
            if level == 15:
                level_message = "I bet you can go faster..." # in this level there is a blue coin with one enemy 
                Bcoin_present = True
                Bcoin_x, Bcoin_y = spawn_Bcoin()
                random_squares = []
                num_enemies = 1
                Spawn_Squares()
                level_initialized = True # Mark the level as initialized       
            if level == 16:
                level_message = "The game ends at Level 100 but you wont make it past Level 50." # in this level there is a blue coin with one enemy 
                Bcoin_present = True
                Bcoin_x, Bcoin_y = spawn_Bcoin()
                random_squares = []
                num_enemies = 1   
                Spawn_Squares()             
                level_initialized = True # Mark the level as initialized       
            if level == 17:
                level_message = "The game gets really hard on level 25." # in this level there is a blue coin with one enemy 
                Bcoin_present = True
                Bcoin_x, Bcoin_y = spawn_Bcoin()
                random_squares = []
                num_enemies = 1    
                Spawn_Squares()            
                level_initialized = True # Mark the level as initialized       
            if level == 18:
                level_message = "Hey! You know you can press SHIFT to go fatser right?" # this level is just a maze with one enemy 
                random_squares = []
                num_enemies = 1
                Spawn_Squares()
                level_initialized = True # Mark the level as initialized              
            if level == 19:
                level_message = "Can you really make it to the end?"  # this level is just a maze with one enemy 
                random_squares = []
                num_enemies = 1
                Spawn_Squares()
                level_initialized = True # Mark the level as initialized             
            if level == 20:
                level_message = "Oh this guy is new." # in this level we introduce the stationary enemy. 
                random_squares = [] # to reset the random squares. 
                num_enemies = 2
                Spawn_Squares()
                stationary_enemy_active = True
                Bbarrier_active = True
                Bbarrier_rect = pygame.Rect(goal_x - 10, goal_y - 10, goal_size + 20, goal_size + 20)
                num_enemies = 2  # Number of random square enemies for this level
                level_initialized = True # Mark the level as initialized           
            if level == 21:
                level_message = "Wow, level 21? I underestimated you." #
                random_squares = []
                num_enemies = 2 
                Spawn_Squares()
                stationary_enemy_active = False
                level_initialized = True # Mark the level as initialized          
            if level == 22:
                level_message = "Are you starting to sweat?" # enemies are faster in this level 
                random_squares = []
                num_enemies = 2 
                Spawn_Squares()
                stationary_enemy_active = False
                level_initialized = True # Mark the level as initialized           
            if level == 23:
                level_message = "Just give up already." #
                random_squares = []
                num_enemies = 2 
                Spawn_Squares()
                stationary_enemy_active = True
                level_initialized = True # Mark the level as initialized          
            if level == 24:
                level_message = "You'll never beat the next level."  #
                random_squares = []
                num_enemies = 2 
                Spawn_Squares()
                stationary_enemy_active = True
                level_initialized = True # Mark the level as initialized          
            if level == 25:
                level_message = "Oh, you made it this far? Must be a fluke."  #
                random_squares = []
                num_enemies = 2 
                Spawn_Squares()
                stationary_enemy_active = True
                level_initialized = True # Mark the level as initialized           
            if level == 26:
                level_message = "Good luck, you'll need it." # something visually distracting is going on. 
                random_squares = []
                num_enemies = 3
                Spawn_Squares()
                stationary_enemy_active = True
                level_initialized = True # Mark the level as initialized            
            if level == 27:
                level_message = "You're just lucky, aren't you?"  # 
                random_squares = []
                num_enemies = 3
                Spawn_Squares()
                stationary_enemy_active = True
                level_initialized = True # Mark the level as initialized            
            if level == 28:
                level_message = "This is where most players quit."  #
                random_squares = []
                num_enemies = 3
                level_initialized = True # Mark the level as initialized            
            if level == 29:
                level_message = "I wouldn't bother if I were you." #
                random_squares = []
                num_enemies = 3
                level_initialized = True # Mark the level as initialized            
            if level == 30:
                level_message = "Admit it, you're impressed with yourself."  #
                random_squares = []
                num_enemies = 4
                level_initialized = True # Mark the level as initialized           
            if level == 31:
                level_message = "Even I didn't think this level was possible." # 
                random_squares = []
                num_enemies = 4
                Spawn_Squares()
                level_initialized = True # Mark the level as initialized          
            if level == 32:
                level_message = "Your keyboard must be crying by now." #
                random_squares = []
                num_enemies = 4
                Spawn_Squares()
                level_initialized = True # Mark the level as initialized            
            if level == 33:
                level_message = "Did you just get lucky or are you skilled?"  #
                random_squares = []
                num_enemies = 4
                Spawn_Squares()
                level_initialized = True # Mark the level as initialized          
            if level == 34:
                level_message = "I hope you saved your game."  #
                random_squares = []
                num_enemies = 4
                Spawn_Squares()
                level_initialized = True # Mark the level as initialized           
            if level == 35:
                level_message = "Get on the floor and bark for me."  # this Level is extra easy.
                random_squares = []
                num_enemies = 5
                Spawn_Squares()
                level_initialized = True # Mark the level as initialized           
            if level == 36:
                level_message = "Just kidding, it's not that kind of game."  #
                random_squares = []
                num_enemies = 5
                Spawn_Squares()
                level_initialized = True # Mark the level as initialized           
            if level == 37:
                random_squares = []
                num_enemies = 5
                Spawn_Squares()
                level_initialized = True # Mark the level as initialized          
            if level == 38:
                level_message = "This is just cruel, even for me." # 
                random_squares = []
                num_enemies = 5
                Spawn_Squares()
                level_initialized = True # Mark the level as initialized            
            if level == 39:
                level_message = "You're making the game look easy."  #
                random_squares = []
                num_enemies = 5
                Spawn_Squares()
                level_initialized = True # Mark the level as initialized            
            if level == 40:
                level_message = "Only a few make it past here."  #
                random_squares = []
                num_enemies = 6
                Spawn_Squares()
                level_initialized = True # Mark the level as initialized            
            if level == 41:
                level_message = "Can you feel the pressure?" #
                random_squares = []
                num_enemies = 6
                Spawn_Squares()
                level_initialized = True # Mark the level as initialized       
            if level == 42:
                level_message = "You're probably cheating, aren't you?"  #
                random_squares = []
                num_enemies = 6
                Spawn_Squares()
                level_initialized = True # Mark the level as initialized       
            if level == 43:
                level_message = "This level is just unfair."  #
                random_squares = []
                num_enemies = 6
                Spawn_Squares()
                level_initialized = True # Mark the level as initialized           
            if level == 44:
                level_message = "Don't blame me, you chose this."  #
                random_squares = []
                num_enemies = 6
                Spawn_Squares()
                level_initialized = True # Mark the level as initialized           
            if level == 45:
                level_message = "Are you even trying anymore?" #
                random_squares = []
                num_enemies = 7
                Spawn_Squares()
                level_initialized = True # Mark the level as initialized             
            if level == 46:
                level_message = "The game won't let you win." #
                random_squares = []
                num_enemies = 7
                Spawn_Squares()
                level_initialized = True # Mark the level as initialized            
            if level == 47:
                level_message = "You're just delaying the inevitable." #                
                random_squares = []
                num_enemies = 7
                Spawn_Squares()
                level_initialized = True # Mark the level as initialized            
            if level == 48:
                level_message = "Even the developers didn't beat this." # enemies are faster than the player 
                random_squares = []
                num_enemies = 7
                Spawn_Squares()
                level_initialized = True # Mark the level as initialized             
            if level == 49:
                level_message = "Remember when I said you wouldn't make it past LVL 50?" #
                random_squares = []
                num_enemies = 7
                Spawn_Squares()
                level_initialized = True # Mark the level as initialized             
            if level == 50:
                level_message = "Perfectly balanced." # in this level there should be a 50% chance to lose instantly. 
                random_squares = []
                num_enemies = 0
                level_initialized = True # Mark the level as initialized           
            if level == 51:
                level_message = "Never bet against a gamer..." #
                random_squares = []
                num_enemies = 8
                Spawn_Squares()
                level_initialized = True # Mark the level as initialized             
            if level == 52:
                level_message = "The clock is Still ticking..." #
                random_squares = []
                num_enemies = 8
                Spawn_Squares()
                level_initialized = True # Mark the level as initialized             
            if level == 53:
                level_message = "There is a special surprise at level 66." #
                random_squares = []
                num_enemies = 8
                Spawn_Squares()
                level_initialized = True # Mark the level as initialized             
            if level == 54:
                level_message = "This level will break you." # in this level it is an extra Hard maze. 
                random_squares = []
                num_enemies = 8
                Spawn_Squares()
                level_initialized = True # Mark the level as initialized             
            if level == 55:
                level_message = "You're still here? Impressive." # in this level it is only a maze 
                random_squares = []
                num_enemies = 8
                Spawn_Squares()
                level_initialized = True # Mark the level as initialized            
            if level == 56:
                level_message = "-" # in this level there is also a Yellow coin 
                random_squares = []
                num_enemies = 9
                Spawn_Squares()
                level_initialized = True # Mark the level as initialized       
            if level == 57:
                level_message = "-" # in this level there is also a Yellow coin 
                random_squares = []
                num_enemies = 9
                Spawn_Squares()
                level_initialized = True # Mark the level as initialized             
            if level == 58:
                level_message = "-?" # in this level there is also a Yellow coin 
                random_squares = []
                num_enemies = 9
                Spawn_Squares()
                level_initialized = True # Mark the level as initialized            
            if level == 59:
                level_message = "-" # in this level there is also a Yellow coin 
                random_squares = []
                num_enemies = 9
                Spawn_Squares()
                level_initialized = True # Mark the level as initialized             
            if level == 60:
                level_message = "-" # in this level there is also a Yellow coin 
                random_squares = []
                num_enemies = 10
                Spawn_Squares()
                level_initialized = True # Mark the level as initialized             
            if level == 61:
                level_message = "You greedy little gamer." # in this level it is only a maze 
                random_squares = []
                num_enemies = 10
                Spawn_Squares()
                level_initialized = True # Mark the level as initialized            
            if level == 62:
                level_message = "wow, Level 12. Look at you go." # in this level it is only a maze 
                random_squares = []
                num_enemies = 10
                Spawn_Squares()
                level_initialized = True # Mark the level as initialized             
            if level == 63:
                level_message = "This is an unlucky level." # in this level there is a yellow barrier and a blue coin 
                random_squares = []
                num_enemies = 10
                Spawn_Squares()
                level_initialized = True # Mark the level as initialized       
            if level == 64:
                level_message = "The game gets really hard on level 25." # in this level there is a blue coin with one enemy 
                random_squares = []
                num_enemies = 10
                Spawn_Squares()
                level_initialized = True # Mark the level as initialized       
            if level == 65:
                level_message = "I bet you can go faster..." # in this level there is a blue coin with one enemy 
                random_squares = []
                num_enemies = 11
                Spawn_Squares()
                level_initialized = True # Mark the level as initialized       
            if level == 66:
                level_message = "The game ends at Level 100 but you wont make it past Level 50." # in this level there is a blue coin with one enemy 
                random_squares = []
                num_enemies = 11
                Spawn_Squares()
                level_initialized = True # Mark the level as initialized      
            if level == 67:
                level_message = "Can you feel the walls getting smaller?" # in this level there is a blue coin with one enemy 
                random_squares = []
                num_enemies = 11
                Spawn_Squares()
                level_initialized = True # Mark the level as initialized      
            if level == 68:
                level_message = "Hey! You know you can press SHIFT to go fatser right?" # this level is just a maze with one enemy 
                random_squares = []
                num_enemies = 11
                Spawn_Squares()
                level_initialized = True # Mark the level as initialized       
            if level == 69:
                level_message = "Nice" # this level is just an easy maze. 
                random_squares = []
                num_enemies = 0
                Spawn_Squares()
                level_initialized = True # Mark the level as initialized       
            if level == 70:
                level_message = "The game should be getting harder now." # in this level there is a Blue barrier 
                random_squares = []
                num_enemies = 12
                Spawn_Squares()
                level_initialized = True # Mark the level as initialized     
            if level == 71:
                level_message = "The game should be getting harder now." #
                random_squares = []
                num_enemies = 12
                Spawn_Squares()
                level_initialized = True # Mark the level as initialized      
            if level == 72:
                level_message = "The game should be getting harder now." #
                random_squares = []
                num_enemies = 12
                Spawn_Squares()
                level_initialized = True # Mark the level as initialized       
            if level == 73:
                level_message = "The game should be getting harder now." #
                random_squares = []
                num_enemies = 12
                Spawn_Squares()
                level_initialized = True # Mark the level as initialized      
            if level == 74:
                level_message = "The game should be getting harder now." #
                random_squares = []
                num_enemies = 12
                Spawn_Squares()
                level_initialized = True # Mark the level as initialized       
            if level == 75:
                level_message = "The game should be getting harder now." #
                random_squares = []
                num_enemies = 13
                Spawn_Squares()
                level_initialized = True # Mark the level as initialized       
            if level == 76:
                level_message = "The game should be getting harder now." #
                random_squares = []
                num_enemies = 13
                Spawn_Squares()
                level_initialized = True # Mark the level as initialized       
            if level == 77:
                level_message = "The game should be getting harder now." #
                random_squares = []
                num_enemies = 13
                Spawn_Squares()
                level_initialized = True # Mark the level as initialized       
            if level == 78:
                level_message = "The game should be getting harder now." #
                random_squares = []
                num_enemies = 13
                Spawn_Squares()
                level_initialized = True # Mark the level as initialized        
            if level == 79:
                level_message = "The game should be getting harder now." #
                random_squares = []
                num_enemies = 13
                Spawn_Squares()
                level_initialized = True # Mark the level as initialized       
            if level == 80:
                level_message = "The game should be getting harder now." #
                random_squares = []
                num_enemies = 14
                Spawn_Squares()
                level_initialized = True # Mark the level as initialized          
            if level == 81:
                level_message = "The game should be getting harder now." #
                random_squares = []
                num_enemies = 14
                Spawn_Squares()
                level_initialized = True # Mark the level as initialized          
            if level == 82:
                level_message = "The game should be getting harder now." #
                random_squares = []
                num_enemies = 14
                Spawn_Squares()
                evel_initialized = True # Mark the level as initialized        
            if level == 83:
                level_message = "The game should be getting harder now." #
                random_squares = []
                num_enemies = 14
                Spawn_Squares()
                level_initialized = True # Mark the level as initialized         
            if level == 84:
                level_message = "The game should be getting harder now." #
                random_squares = []
                num_enemies = 14
                Spawn_Squares()
                level_initialized = True # Mark the level as initialized         
            if level == 85:
                level_message = "The game should be getting harder now." #
                random_squares = []
                num_enemies = 15
                Spawn_Squares()
                level_initialized = True # Mark the level as initialized          
            if level == 86:
                level_message = "The game should be getting harder now." #
                random_squares = []
                num_enemies = 15
                Spawn_Squares()
                level_initialized = True # Mark the level as initialized        
            if level == 87:
                level_message = "The game should be getting harder now." #
                random_squares = []
                num_enemies = 15
                Spawn_Squares()
                level_initialized = True # Mark the level as initialized          
            if level == 88:
                level_message = "The game should be getting harder now." #
                random_squares = []
                num_enemies = 15
                Spawn_Squares()
                level_initialized = True # Mark the level as initialized         
            if level == 89:
                level_message = "The game should be getting harder now." #
                random_squares = []
                num_enemies = 15
                Spawn_Squares()
                level_initialized = True # Mark the level as initialized         
            if level == 90:
                level_message = "The game should be getting harder now." #
                random_squares = []
                num_enemies = 20
                Spawn_Squares()
                level_initialized = True # Mark the level as initialized        
            if level == 91:
                level_message = "The game should be getting harder now." #
                random_squares = []
                num_enemies = 20
                Spawn_Squares()
                level_initialized = True # Mark the level as initialized          
            if level == 92:
                level_message = "The game should be getting harder now." #
                random_squares = []
                num_enemies = 20
                Spawn_Squares()
                level_initialized = True # Mark the level as initialized       
            if level == 93:
                level_message = "The game should be getting harder now." #
                random_squares = []
                num_enemies = 20
                Spawn_Squares()
                level_initialized = True # Mark the level as initialized         
            if level == 94:
                level_message = "The game should be getting harder now." #
                random_squares = []
                num_enemies = 20
                Spawn_Squares()
                level_initialized = True # Mark the level as initialized         
            if level == 95:
                level_message = "The game should be getting harder now." #
                random_squares = []
                num_enemies = 20
                Spawn_Squares()

                level_initialized = True # Mark the level as initialized         
            if level == 96:
                level_message = "The game should be getting harder now." #
                random_squares = []
                num_enemies = 20
                Spawn_Squares()

                level_initialized = True # Mark the level as initialized         
            if level == 97:
                level_message = "The game should be getting harder now." #
                random_squares = []
                num_enemies = 20
                Spawn_Squares()
                level_initialized = True # Mark the level as initialized         
            if level == 98:
                level_message = "only two more levels"#
                random_squares = []
                num_enemies = 20
                Spawn_Squares()
                level_initialized = True # Mark the level as initialized         
            if level == 99:
                level_message = "The game should be getting harder now." #
                random_squares = []
                num_enemies = 20
                Spawn_Squares()
                level_initialized = True # Mark the level as initialized                
            if level == 100:
                level_message = "If you beat this level, you win! Too bad you cant.", #this level should be unique.

                level_initialized = True # Mark the level as initialized  

        # Check if the player collects a Ycoin
        if Ycoin_present and (
            player_x < Ycoin_x + player_size
            and player_x + player_size > Ycoin_x
            and player_y < Ycoin_y + player_size
            and player_y + player_size > Ycoin_y
        ):
            Ycoins_collected += 1
            Ycoin_present = False

        # Check if the player collects a Bcoin
        if Bcoin_present and (
            player_x < Bcoin_x + player_size
            and player_x + player_size > Bcoin_x
            and player_y < Bcoin_y + player_size
            and player_y + player_size > Bcoin_y
        ):
            Bcoins_collected += 1
            Bcoin_present = False

        # Check Ybarrier interaction
        if Ybarrier_active and Ybarrier_rect.colliderect((player_x, player_y, player_size, player_size)):
            if Ycoins_collected >= Ybarrier_cost:
                Ycoins_collected -= Ybarrier_cost
                Ybarrier_active = False
            else:
                game_over = True

        # Check Bbarrier interaction
        if Bbarrier_active and Bbarrier_rect.colliderect((player_x, player_y, player_size, player_size)):
            if Bcoins_collected >= Bbarrier_cost:
                Bcoins_collected -= Bbarrier_cost
                Bbarrier_active = False
            else:
                game_over = True

        if projectile_active:
            # Update projectile position
            projectile_x += projectile_direction[0] * projectile_speed
            projectile_y += projectile_direction[1] * projectile_speed

            # Draw the projectile
            pygame.draw.circle(screen, WHITE, (int(projectile_x), int(projectile_y)), 5)

            # Check for collision with the player
            if (
                projectile_x < player_x + player_size
                and projectile_x > player_x
                and projectile_y < player_y + player_size
                and projectile_y > player_y
            ):
                game_over = True  # Player hit by the projectile

            # Deactivate projectile if it moves out of bounds
            if (
                projectile_x < 0
                or projectile_x > screen_width
                or projectile_y < ui_height
                or projectile_y > screen_height
            ):
                projectile_active = False
            

        # Draw player and goal
        pygame.draw.rect(screen, GREEN, (player_x, player_y, player_size, player_size))
        pygame.draw.rect(screen, RED, (goal_x, goal_y, goal_size, goal_size))
        # Debugging: Draw the player's corners
        #for corner_x, corner_y in [
        #   (player_x, player_y),  # Top-left
        #   (player_x + player_size - 1, player_y),  # Top-right
        #   (player_x, player_y + player_size - 1),  # Bottom-left
        #   (player_x + player_size - 1, player_y + player_size - 1),  # Bottom-right
        #]:
        #   pygame.draw.circle(screen, RED, (corner_x, corner_y), 3)  # Small red circles at corners

        # Draw maze
        for y in range(maze_height):
            for x in range(maze_width):
                if maze[y][x] == 1:
                    pygame.draw.rect(screen, WHITE, (x * cell_size, y * cell_size + ui_height, cell_size, cell_size))

        # Yellow Barrier
        if Ybarrier_active:
            pygame.draw.rect(screen, YELLOW, Ybarrier_rect, 3)  # Thicker barrier
          
        # Blue Barrier
        if Bbarrier_active:
            pygame.draw.rect(screen, BLUE, Bbarrier_rect, 3)  # Thicker barrier

        if random_squares:
            for enemy in random_squares:
                move_single_random_square(enemy)  # Update each enemy's position

                # Draw the enemy
                pygame.draw.rect(
                    screen, (255, 255, 255),  # White color for enemies
                    (enemy["position"][0], enemy["position"][1], random_square_size, random_square_size),
                )

                # Check for collision with the player
                if (
                    enemy["position"][0] < player_x + player_size
                    and enemy["position"][0] + random_square_size > player_x
                    and enemy["position"][1] < player_y + player_size
                    and enemy["position"][1] + random_square_size > player_y
                ):
                    game_over = True  # Player hit by an enemy

        if stationary_enemy_active: #Spawn the stationary enemy. 
            if stationary_enemy_x is None and stationary_enemy_y is None:   
                enemy_cell_x = random.randint(
                    goal_x // cell_size - goal_safe_zone_radius,
                    goal_x // cell_size + goal_safe_zone_radius,
                )
                enemy_cell_y = random.randint(
                    (goal_y - ui_height) // cell_size - goal_safe_zone_radius,
                    (goal_y - ui_height) // cell_size + goal_safe_zone_radius,
                )
                if (
                    0 <= enemy_cell_x < maze_width
                    and 0 <= enemy_cell_y < maze_height
                    and maze[enemy_cell_y][enemy_cell_x] == 0  # Ensure it's not a wall
                    and (enemy_cell_x, enemy_cell_y) != (goal_x // cell_size, (goal_y - ui_height) // cell_size)  # Not overlapping goal
                ):
                    stationary_enemy_x = enemy_cell_x * cell_size
                    stationary_enemy_y = enemy_cell_y * cell_size + ui_height


            pygame.draw.rect( # Draw the stationary enemy
                screen, 
                (WHITE), 
                (stationary_enemy_x, stationary_enemy_y, 10 , 10 ),
                )

  
        # Draw Ycoin
        if Ycoin_present:
            pygame.draw.circle(screen, YELLOW, (Ycoin_x + player_size // 2, Ycoin_y + player_size // 2), player_size // 2)

        # Draw Bcoin
        if Bcoin_present:
            pygame.draw.circle(screen, BLUE, (Bcoin_x + player_size // 2, Bcoin_y + player_size // 2), player_size // 2)

        # Draw the level-specific message on every frame
        if level_message:
            draw_text(level_message, screen_width // 2 - 150, 30)

    # Event handling (Starting the game from the menus and quitting.)
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
                player_start_x, player_start_y = 1, 1  # Initial starting cell
                maze, goal_x, goal_y = generate_maze_normal(player_start_x, player_start_y)
                goal_y += ui_height  # Adjust for UI height
                goal_y += ui_height  # Adjust for UI height
                Ycoins_collected = 0  # Reset coin count
                Bcoins_collected = 0  # Reset coin count
                score_saved = False
                Ybarrier_active = False
                Bbarrier_active = False
                Ycoin_present = False
                Bcoin_present = False
                level_initialized = False
                random_square_active = False
                random_square_x, random_square_y = goal_x, goal_y
            elif game_over and event.key == pygame.K_SPACE:
                game_over = False
                start_time = time.time()
                level = 1
                cell_size = 40 
                player_speed = 2
                player_x, player_y = cell_size, ui_height + cell_size
                player_start_x, player_start_y = 1, 1  # Initial starting cell
                maze, goal_x, goal_y = generate_maze_normal(player_start_x, player_start_y)
                goal_y += ui_height  # Adjust for UI height
                goal_y += ui_height  # Adjust for UI height
                Ycoins_collected = 0  # Reset coin count
                Bcoins_collected = 0  # Reset coin count
                score_saved = False
                Ybarrier_active = False
                Bbarrier_active = False
                Ycoin_present = False
                Bcoin_present = False
                level_initialized = False
                random_square_active = False
                random_square_x, random_square_y = goal_x, goal_y
            elif game_over and event.key == pygame.K_m:
                game_over = False
                main_menu = True

    # Refresh display
    pygame.display.flip()
    pygame.time.Clock().tick(60)

pygame.quit()
sys.exit()
