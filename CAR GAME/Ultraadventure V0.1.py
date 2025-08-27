import pygame
import sys
import time
import os
import random
from pygame.locals import *


# Initialize pygame
pygame.init()

# Constants
WINDOW_WIDTH = 1800 
screen_width = 1800
WIDTH = 1800
WINDOW_HEIGHT = 900
screen_height = 900
HEIGHT = 900
INFO_BAR_HEIGHT = 100
ARENA_WIDTH = WINDOW_WIDTH
ARENA_HEIGHT = WINDOW_HEIGHT - (2 * INFO_BAR_HEIGHT)
FPS = 120
TILE_SIZE = 40
last_gear_change_time = 0  # Track the last time a gear change occurred
DEBUG = False  # Set to False to disable debug output

highscore_file = "Highscores.txt"
# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLACK1 = (45, 45, 45)
BLACK2 = (100, 100, 100)
GRAY = (200, 200, 200)
BLUE = (50, 50, 255)
RED = (255, 0, 0)
PURPLE = (174,55,255)
LIGHT_GRAY = (220, 220, 220)
DARK_GRAY = (180, 180, 180)
YELLOW = (255, 255, 0)
# Player constants
PLAYER_WIDTH = 50
PLAYER_HEIGHT = 30
PLAYER_COLOR = BLUE
PLAYER_SPEED = 2
SHIFT_SPEED = 4
GEAR_CHANGE_DELAY = 1  # Delay in seconds between gear changes
speed = 10  # Initial speed
distance = 0  # Distance traveled
SPEED_INCREMENT = 0.2  # Speed increment per frame
MAX_SPEED = 242  # Maximum speed for gear 6
game_start_time = time.time() # To track when the game starts


# Create window
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("ULTRAEDGE PRESENTS: CAR Adventure")

# Load the grass texture (ensure the texture seamlessly tiles horizontally)
grass_texture = pygame.image.load("grass_texture.png")  # Replace with your texture file

# Clock
clock = pygame.time.Clock()
# Gears
GEARS = {
    "N": (5, 4),   # Neutral: 
    1: (6, 5),     # Gear 1: 
    2: (7, 6),     # Gear 2: Slightly faster
    3: (9, 8),     # Gear 3: Faster
    4: (11, 10),   # Gear 4: Even faster
    5: (13, 12),   # Gear 5: Very fast
    6: (15, 14)    # Gear 6: Maximum speed
}
current_gear = "N"  # Start in Neutral

# Player initial position
# Player starting position (example)
player_x = 1000
player_y = 500
x2 = 3000
y2 = 3000
player_tilt = 0
username = "GingerKid_1"
player_2_active = False
username1= "ULTRAEDGE"
Random_colors = [
    (255, 0, 0),    # Red
    (0, 255, 0),    # Green
    (0, 0, 255),    # Blue
    (255, 255, 0),  # Yellow
    (0, 255, 255),  # Cyan
    (255, 0, 255),  # Magenta
    (255, 165, 0),  # Orange
]
show_4k_message = False
random_choice = random.choice(Random_colors)
oncoming_cars = []
slow_blue_cars = []
# Load car images from the "cars" folder
car_images = []
car_image_folder = "cars"
for i in range(1, 6):
    car_images.append(pygame.image.load(os.path.join(car_image_folder, f"car_right_{i}.png")))


# Info bar scroll variables
bar_scroll_speed = 5
line_scroll_speed = 4
line_offset = 1
hitbox = pygame.Rect(player_x - PLAYER_WIDTH // 2, 
                     player_y - PLAYER_HEIGHT // 2, 
                     PLAYER_WIDTH, 
                     PLAYER_HEIGHT)

game_over_menu_texts = [
    "Game Over!",
    "Press R to Start a New Game",
]
#functions
def get_top_highscores():
    """Retrieve the top 5 highscores."""
    if not os.path.exists(highscore_file):
        return []

    with open(highscore_file, "r") as file:
        highscores = file.readlines()

    return [(float(line.split(",")[0]), float(line.split(",")[1])) for line in highscores if line.strip()]

def append_highscore(distance, speed):
    """Append the player's score to the highscores file."""
    if not os.path.exists(highscore_file):
        open(highscore_file, "w").close()  # Ensure the file exists

    # Read existing scores
    highscores = get_top_highscores()

    # Add new score
    highscores.append((distance, speed))

    # Sort properly by distance (desc), then speed (desc)
    highscores.sort(key=lambda x: (-x[0], -x[1]))

    # Keep only top 5
    highscores = highscores[:5]

    # Write updated scores to the file
    with open(highscore_file, "w") as file:
        file.writelines([f"{d:.2f},{s:.2f}\n" for d, s in highscores])
def draw_arena_border():
    """Draw a border around the arena."""
    pygame.draw.rect(screen, BLACK, (0, INFO_BAR_HEIGHT, WINDOW_WIDTH, ARENA_HEIGHT), 2)

def draw_arena_tiles():
    """Draw a tiled floor for the arena."""
    for row in range(INFO_BAR_HEIGHT, INFO_BAR_HEIGHT + ARENA_HEIGHT, TILE_SIZE):
        for col in range(0, ARENA_WIDTH, TILE_SIZE):
            if (row // TILE_SIZE + col // TILE_SIZE) % 2 == 0:
                color = BLACK2
            else:
                color = BLACK2
            pygame.draw.rect(screen, color, (col, row, TILE_SIZE, TILE_SIZE))
# Initialize the flag for showing the 4K message
def draw_info_bars():
    """Draw the top and bottom information bars with scrolling grass effect."""
    global line_offset, show_4k_message

    # Adjust scrolling position
    line_offset = (line_offset + bar_scroll_speed) % grass_texture.get_width()

    # Draw top bar (grass scrolling effect)
    for i in range(-1, (WINDOW_WIDTH // grass_texture.get_width()) + 2):  # -1 ensures proper coverage for negative offset
        screen.blit(grass_texture, (i * grass_texture.get_width() - line_offset, 0))

    # Draw bottom bar (grass scrolling effect)
    for i in range(-1, (WINDOW_WIDTH // grass_texture.get_width()) + 2):
        screen.blit(grass_texture, (i * grass_texture.get_width() - line_offset, WINDOW_HEIGHT - INFO_BAR_HEIGHT))

    # Display text on the top right corner if the flag is True
    if show_4k_message:
        font = pygame.font.Font(None, 36)
        text = font.render("4K resolution enabled", True, WHITE)
        screen.blit(text, (WINDOW_WIDTH - text.get_width() - 10, 10))  # Adjust position for right top corner
def handle_input():
    """Handle key input to toggle the 4K message visibility."""
    global show_4k_message
    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_g:  # Toggle message visibility when 'G' is pressed
                show_4k_message = not show_4k_message
def draw_text(text, x, y):
    """Render text on the screen."""
    text_surface = font.render(text, True, WHITE)
    screen.blit(text_surface, (x, y))
# Function to calculate and update speed and distance for the information bar and Score. 
def update_speed_and_distance():
    global speed, distance, current_gear

    # Define the maximum speed limits for each gear
    gear_speed_limits = {
        "N": 10,
        1: 40,
        2: 60,
        3: 100,
        4: 150,
        5: 200,
        6: 242
    }
    
    max_speed_for_gear = gear_speed_limits.get(current_gear, 0)

    # Adjust speed based on gear and enforce limits
    if current_gear == "N":
        speed = max(max_speed_for_gear, speed - 1)  # Gradually slow down to 30 km/h in Neutral
    elif current_gear in gear_speed_limits:
        if speed > max_speed_for_gear:
            speed = max(max_speed_for_gear, speed - 0.1)  # Slowly decrease speed if above max for gear
        else:
            # Determine the increment rate
            increment = {
                1: SPEED_INCREMENT,
                2: 0.1,
                3: 0.01,
                4: 0.01,
                5: 0.01,
                6: 0.001
            }.get(current_gear, 0)

            # Modify increment based on key presses
            if keys[pygame.K_a]:  # "A" key prevents acceleration
                increment = 0
            elif keys[pygame.K_d]:  # "D" key doubles acceleration
                increment *= 2

            # Update speed
            speed = min(max_speed_for_gear, speed + increment)
    
    # Update the distance traveled
    if speed > 0:
        distance += (speed / 3600) / FPS  # Convert speed (km/h) to km/s, then calculate distance for this frame
# Function to display the main menu
def main_menu():
    font = pygame.font.SysFont(None, 72)
    title_text = "Game Title"
    start_text = "Press SPACE to Start"
    quit_text = "Press Q to Quit"

    # Render the text
    title_surface = font.render(title_text, True, WHITE)
    start_surface = font.render(start_text, True, WHITE)
    quit_surface = font.render(quit_text, True, WHITE)

    # Draw the text to the screen
    screen.fill(BLACK)
    screen.blit(title_surface, (WIDTH // 2 - title_surface.get_width() // 2, HEIGHT // 4))
    screen.blit(start_surface, (WIDTH // 2 - start_surface.get_width() // 2, HEIGHT // 2))
    screen.blit(quit_surface, (WIDTH // 2 - quit_surface.get_width() // 2, HEIGHT // 2 + 50))

    pygame.display.flip()
# Function to handle menu input
#def handle_input():
#   """Handle key input to toggle the 4K message visibility."""
#    global show_4k_message
#    for event in pygame.event.get():
#        if event.type == pygame.KEYDOWN:
#            if event.key == pygame.K_g:  # Toggle message visibility when 'G' is pressed
#                show_4k_message = not show_4k_message
def handle_main_menu():
    keys = pygame.key.get_pressed()

    if keys[pygame.K_SPACE]:
        return "start"
    elif keys[pygame.K_q]:
        return "quit"
    return "menu"
# Function to display the game over screen
def game_over_screen():
    """Display the game over screen and top 10 highscores."""
    global in_game_over
    screen.fill(BLACK)  # Clear the screen

    # Draw the game over messages
    font = pygame.font.SysFont(None, 72)
    for i, line in enumerate(game_over_menu_texts):
        draw_text(line, screen_width // 2 - 150, screen_height // 3 + 50 * i)

    # Draw the player's final stats
    level_text = font.render(f"Distance Reached: {distance:.2f}km", True, WHITE)
    screen.blit(level_text, (screen_width // 2 - level_text.get_width() // 2, screen_height // 3 + 150))

    # Draw the top 5 highscores
    draw_text("Top 5 Scores", screen_width // 2 - 100, screen_height // 3 + 250)
    top_scores = get_top_highscores()
    for i, (dist, spd) in enumerate(top_scores):
        draw_text(
            f"{i + 1}. Distance {dist} km, Speed {spd} km/h",
            screen_width // 2 - 150,
            screen_height // 3 + 280 + 30 * i,
        )
    append_highscore(distance,speed)

    pygame.display.flip()  # Update the display
    if in_game_over :
        return
def check_game_over(player_x):
    if player_x <= 0:  # Left-most barrier condition
        return True
    return False

    # Update the distance traveled
    #distance += speed / FPS  # Distance = speed * time, time is 1/FPS per frame
def check_player2_falls_behind(player2_hitbox):
    global player_2_active
    if player_2_active:
        if x2 <= -100: #little past left-most barrier. 
            return True
        return False 
def draw_speed_and_distance():
    font = pygame.font.SysFont(None, 36)
    
    # Format speed and distance for display
    speed_text = f"Speed: {int(speed)} km/h"
    distance_text = f"Distance: {distance:.4f} km"
    
    # Render text
    speed_surface = font.render(speed_text, True, WHITE)
    distance_surface = font.render(distance_text, True, WHITE)
    
    # Draw text in the top info bar
    screen.blit(speed_surface, (20, INFO_BAR_HEIGHT // 2 - 50))
    screen.blit(distance_surface, (20, INFO_BAR_HEIGHT // 2 + 25))
def draw_middle_line():
    """Draw the fast-moving yellow and white middle dashed lines."""
    global line_offset 

    # Adjust scrolling position
    line_offset = (line_offset + line_scroll_speed) % (WINDOW_WIDTH + 100)  # Add extra buffer for smooth looping

    # Settings for dashed lines
    line_width = 67
    line_spacing = 30


     # Draw the first solid yellow line (center of the road, fixed)
    pygame.draw.rect(screen, YELLOW, (0, INFO_BAR_HEIGHT + ARENA_HEIGHT // 2 - 2 + 5, WINDOW_WIDTH, 4))

    # Draw the second solid yellow line (slightly below the first, fixed)
    pygame.draw.rect(screen, YELLOW, (0, INFO_BAR_HEIGHT + ARENA_HEIGHT // 2 + 2 - 5, WINDOW_WIDTH, 4))

    # Draw two white dashed lines above the yellow lines
    for i in range(-1, (WINDOW_WIDTH // (line_width + line_spacing)) + 2):
        x = i * (line_width + line_spacing) - line_offset
        pygame.draw.rect(screen, WHITE, (x, INFO_BAR_HEIGHT + ARENA_HEIGHT // 2 - 2 - 50, line_width, 4))

    # Draw two white dashed lines below the yellow lines
    for i in range(-1, (WINDOW_WIDTH // (line_width + line_spacing)) + 2):
        x = i * (line_width + line_spacing) - line_offset
        pygame.draw.rect(screen, WHITE, (x, INFO_BAR_HEIGHT + ARENA_HEIGHT // 2 - 2 + 50, line_width, 4))

    # Draw white dashed lines on the left side of the yellow lines
    for i in range(-1, (WINDOW_WIDTH // (line_width + line_spacing)) + 2):
        x = i * (line_width + line_spacing) - line_offset
        pygame.draw.rect(screen, WHITE, (x, INFO_BAR_HEIGHT + ARENA_HEIGHT // 2 - 2 - 100, line_width, 4))

    # Draw white dashed lines on the right side of the yellow lines
    for i in range(-1, (WINDOW_WIDTH // (line_width + line_spacing)) + 2):
        x = i * (line_width + line_spacing) - line_offset
        pygame.draw.rect(screen, WHITE, (x, INFO_BAR_HEIGHT + ARENA_HEIGHT // 2 - 2 + 100, line_width, 4))

    # Draw white dashed lines on the left side of the yellow lines
    for i in range(-1, (WINDOW_WIDTH // (line_width + line_spacing)) + 2):
        x = i * (line_width + line_spacing) - line_offset
        pygame.draw.rect(screen, WHITE, (x, INFO_BAR_HEIGHT + ARENA_HEIGHT // 2 - 2 - 150, line_width, 4))

    # Draw white dashed lines on the right side of the yellow lines
    for i in range(-1, (WINDOW_WIDTH // (line_width + line_spacing)) + 2):
        x = i * (line_width + line_spacing) - line_offset
        pygame.draw.rect(screen, WHITE, (x, INFO_BAR_HEIGHT + ARENA_HEIGHT // 2 - 2 + 150, line_width, 4))
    # Draw white dashed lines on the left side of the yellow lines
    for i in range(-1, (WINDOW_WIDTH // (line_width + line_spacing)) + 2):
        x = i * (line_width + line_spacing) - line_offset
        pygame.draw.rect(screen, WHITE, (x, INFO_BAR_HEIGHT + ARENA_HEIGHT // 2 - 2 - 200, line_width, 4))

    # Draw white dashed lines on the right side of the yellow lines
    for i in range(-1, (WINDOW_WIDTH // (line_width + line_spacing)) + 2):
        x = i * (line_width + line_spacing) - line_offset
        pygame.draw.rect(screen, WHITE, (x, INFO_BAR_HEIGHT + ARENA_HEIGHT // 2 - 2 + 200, line_width, 4))

    for i in range(-1, (WINDOW_WIDTH // (line_width + line_spacing)) + 2):
        x = i * (line_width + line_spacing) - line_offset
        pygame.draw.rect(screen, WHITE, (x, INFO_BAR_HEIGHT + ARENA_HEIGHT // 2 - 2 - 250, line_width, 4))

    # Draw white dashed lines on the right side of the yellow lines
    for i in range(-1, (WINDOW_WIDTH // (line_width + line_spacing)) + 2):
        x = i * (line_width + line_spacing) - line_offset
        pygame.draw.rect(screen, WHITE, (x, INFO_BAR_HEIGHT + ARENA_HEIGHT // 2 - 2 + 250, line_width, 4))

    for i in range(-1, (WINDOW_WIDTH // (line_width + line_spacing)) + 2):
        x = i * (line_width + line_spacing) - line_offset
        pygame.draw.rect(screen, WHITE, (x, INFO_BAR_HEIGHT + ARENA_HEIGHT // 2 - 2 - 300, line_width, 4))

    # Draw white dashed lines on the right side of the yellow lines
    for i in range(-1, (WINDOW_WIDTH // (line_width + line_spacing)) + 2):
        x = i * (line_width + line_spacing) - line_offset
        pygame.draw.rect(screen, WHITE, (x, INFO_BAR_HEIGHT + ARENA_HEIGHT // 2 - 2 + 300, line_width, 4))

    # Draw Highway shoulder 
    pygame.draw.rect(screen, WHITE, (0, INFO_BAR_HEIGHT + ARENA_HEIGHT // 2 - 2 +340, WINDOW_WIDTH, 1))
    pygame.draw.rect(screen, WHITE, (0, INFO_BAR_HEIGHT + ARENA_HEIGHT // 2 + 2 +343, WINDOW_WIDTH, 1))

    # Draw the second Highway Shoulder.
    pygame.draw.rect(screen, WHITE, (0, INFO_BAR_HEIGHT + ARENA_HEIGHT // 2 + 2 -3 -330, WINDOW_WIDTH, 1))
    pygame.draw.rect(screen, WHITE, (0, INFO_BAR_HEIGHT + ARENA_HEIGHT // 2 + 2 -3 -335, WINDOW_WIDTH, 1))

    # Draw Highway barrier 
    pygame.draw.rect(screen, GRAY, (0, INFO_BAR_HEIGHT + ARENA_HEIGHT // 2 - 2 +350, WINDOW_WIDTH, 10))

    # Draw the second Highway barrier.
    pygame.draw.rect(screen, GRAY, (0, INFO_BAR_HEIGHT + ARENA_HEIGHT // 2 + 2 -357, WINDOW_WIDTH, 7))
def draw_gear():
    font = pygame.font.SysFont(None, 36)  # Set font size and style
    text = font.render(f"Gear: {current_gear}", True, WHITE)  # Render gear as text
    screen.blit(text, (20, 20))  # Draw it at the top-left corner
def handle_player_movement(keys, x, y):
    global player_tilt 
    # Fixed movement speed for manual keys
    speed = 2

    # Manual movement
    if keys[pygame.K_w] and y - PLAYER_HEIGHT // 2 > INFO_BAR_HEIGHT:
        y -= speed
        player_tilt = 3
    elif keys[pygame.K_s] and y + PLAYER_HEIGHT // 2 < INFO_BAR_HEIGHT + ARENA_HEIGHT:
        y += speed
        player_tilt = -3
    else:
        player_tilt = 0

    if keys[pygame.K_a] and x - PLAYER_WIDTH // 2 > 0:
        x -= speed
        player_tilt = -3
    elif current_gear != "N" and keys[pygame.K_d] and x + PLAYER_WIDTH // 2 < WINDOW_WIDTH:
        x += speed
        player_tilt = 4
    elif keys[pygame.K_s] and keys[pygame.K_d] and y + PLAYER_HEIGHT // 2 < INFO_BAR_HEIGHT + ARENA_HEIGHT:
        y += speed
        player_tilt = -3        
    else:
        player_tilt = 0

    # Automatic backward movement in Neutral gear
    if in_game and not (keys[pygame.K_w] or keys[pygame.K_a] or keys[pygame.K_s] or keys[pygame.K_d]):
        x -= 1  # Move backward at the lowest speed
        player_tilt = 0  # Reset tilt when moving backward automatically

    return x, y
def draw_player(x, y, tilt):
    """Draw the player as a detailed muscle car with tilt and a spoiler."""
    # Car dimensions
    car_body_width = PLAYER_WIDTH
    car_body_height = PLAYER_HEIGHT
    wheel_radius = 8
    # Add taillights (side view perspective)
    Taillight_radius = 3
    Taillight_center = (x - car_body_width // 2 + 10-9, y - car_body_height * 0.1)
    pygame.draw.circle(screen, RED, Taillight_center, Taillight_radius)

     # Add taillights (side view perspective)
    headlight_radius = 2
    headlight_center = (x - car_body_width // 2 + 50, y - car_body_height * - 0.2)
    pygame.draw.circle(screen, YELLOW, headlight_center, headlight_radius)


    # Draw car body (without player color fill, just a similar rectangle at the bottom)
    body_surface = pygame.Surface((car_body_width, car_body_height), pygame.SRCALPHA)
    body_surface.fill((0, 0, 0, 0))  # Make the surface transparent

    # Create a rectangle in the place of the player body, but limited by the taillight height
    rectangle_height = car_body_height // 2  # Set the height to the taillight's height
    pygame.draw.rect(body_surface, PURPLE, (0, car_body_height - rectangle_height, car_body_width, rectangle_height))

    # Move the triangle to the bottom-left corner with right angle at bottom left
    cutout_height = car_body_height * 0.9  # Adjust as needed for size of the cutout
    pygame.draw.polygon(body_surface, PURPLE, [
        (0, car_body_height),  # Bottom left corner (right angle)
        (cutout_height, car_body_height),  # Bottom side of the triangle
        (0, car_body_height - cutout_height)  # Left side of the triangle
    ])

    # Draw the bottom trim as a separate, shorter rectangle
    trim_height = car_body_height * 0.3  # Adjust height of the bottom trim
    pygame.draw.rect(body_surface, DARK_GRAY, (0, car_body_height - trim_height, car_body_width, trim_height))

    # Rotate the body surface with the trim included
    rotated_body = pygame.transform.rotate(body_surface, tilt)
    screen.blit(rotated_body, rotated_body.get_rect(center=(x, y)))

    # Draw rotated and smaller windows
    window_width = car_body_width * 0.5
    window_height = car_body_height * 0.2
    window_surface = pygame.Surface((window_width, window_height), pygame.SRCALPHA)
    window_surface.fill(LIGHT_GRAY)
    pygame.draw.rect(window_surface, PURPLE, window_surface.get_rect(), 1 )  # Add window border
    rotated_window = pygame.transform.rotate(window_surface, tilt)
    screen.blit(rotated_window, rotated_window.get_rect(center=(x, y - car_body_height * 0.1)))

    # Draw wheels
    wheel_offsets = [
        (-car_body_width // 2 + 10, car_body_height // 2 - 1),  # REAR-left
        (car_body_width // 2 - 10, car_body_height // 2 - 1),   # FRONT-right
    ]
    for offset in wheel_offsets:
        wheel_center = (x + offset[0], y + offset[1])
        pygame.draw.circle(screen, BLACK1, wheel_center, wheel_radius)
        pygame.draw.circle(screen, LIGHT_GRAY, wheel_center, wheel_radius // 2)  # Inner rim
def handle_player2_movement(keys, x2, y2):
    global player_tilt2, player_2_active

    # Fixed movement speed for Player 2
    speed = 2

    # Manual movement logic
    if keys[pygame.K_UP] and y2 - PLAYER_HEIGHT // 2 > INFO_BAR_HEIGHT:
        y2 -= speed
        player_tilt2 = 2
    elif keys[pygame.K_DOWN] and y2 + PLAYER_HEIGHT // 2 < INFO_BAR_HEIGHT + ARENA_HEIGHT:
        y2 += speed
        player_tilt2 = -4
    else:
        player_tilt2 = 0

    if keys[pygame.K_LEFT] and x2 - PLAYER_WIDTH // 2 > 0:
        x2 -= speed
        player_tilt2 = -3
    elif keys[pygame.K_RIGHT] and x2 + PLAYER_WIDTH // 2 < WINDOW_WIDTH:
        x2 += speed
        player_tilt2 = 2
    else:
        player_tilt2 = 0

 # Automatic backward movement in Neutral gear
    if in_game and not (keys[pygame.K_w] or keys[pygame.K_a] or keys[pygame.K_s] or keys[pygame.K_d]):
        x2 -= 1  # Move backward at the lowest speed
        player_tilt = 0  # Reset tilt when moving backward automatically
    # Activate Player 2 on pressing "L"
    if not player_2_active and keys[pygame.K_l]:
        player_2_active = True
        x2, y2 = 1800, 500  # Initial spawn position for Player 2

    return x2, y2  # Return updated position
def handle_gear_change(keys):
    global current_gear, last_gear_change_time, bar_scroll_speed, line_scroll_speed, speed
    current_time = time.time()

    # Define the maximum speed limits for each gear
    gear_speed_limits = {
        "N": 10,
        1: 40,
        2: 60,
        3: 100,
        4: 150,
        5: 200,
        6: 242
    }
    
    max_speed_for_gear = gear_speed_limits.get(current_gear, 0)

    if current_time - last_gear_change_time >= GEAR_CHANGE_DELAY:  # Check if the delay has passed
        max_speed_for_gear = gear_speed_limits.get(current_gear, 0)

        if keys[pygame.K_q]:  # Downshift
            if current_gear == 1:
                current_gear = "N"
            elif current_gear != "N":
                current_gear -= 1
            last_gear_change_time = current_time
        elif keys[pygame.K_e]:  # Upshift
            if (current_gear == "N" or speed >= max_speed_for_gear):  # Can upshift from N or if at max speed for current gear
                if current_gear == "N":
                    current_gear = 1
                elif current_gear < 6:
                    current_gear += 1
                last_gear_change_time = current_time

        # Update scroll speeds based on the current gear
        bar_scroll_speed, line_scroll_speed = GEARS[current_gear]
def spawn_square(username, X2, Y2, ):
    """Draw the player as a detailed muscle car with tilt and a spoiler."""
    # Car dimensions
    car_body_width = PLAYER_WIDTH
    car_body_height = PLAYER_HEIGHT
    wheel_radius = 8

    # Add taillights (side view perspective)
    Taillight_radius = 3
    Taillight_center = (X2 - car_body_width // 2 + 10-9, Y2 - car_body_height * 0.1)
    pygame.draw.circle(screen, RED, Taillight_center, Taillight_radius)

     # Add taillights (side view perspective)
    headlight_radius = 2
    headlight_center = (X2 - car_body_width // 2 + 50, Y2 - car_body_height * - 0.2)
    pygame.draw.circle(screen, YELLOW, headlight_center, headlight_radius)


    # Draw car body (without player color fill, just a similar rectangle at the bottom)
    body_surface = pygame.Surface((car_body_width, car_body_height), pygame.SRCALPHA)
    body_surface.fill((0, 0, 0, 0))  # Make the surface transparent

    # Create a rectangle in the place of the player body, but limited by the taillight height
    rectangle_height = car_body_height // 2  # Set the height to the taillight's height
    pygame.draw.rect(body_surface, BLUE, (0, car_body_height - rectangle_height, car_body_width, rectangle_height))

    # Move the triangle to the bottom-left corner with right angle at bottom left
    cutout_height = car_body_height * 0.9  # Adjust as needed for size of the cutout
    pygame.draw.polygon(body_surface, BLUE, [
        (0, car_body_height),  # Bottom left corner (right angle)
        (cutout_height, car_body_height),  # Bottom side of the triangle
        (0, car_body_height - cutout_height)  # Left side of the triangle
    ])

    # Draw the bottom trim as a separate, shorter rectangle
    trim_height = car_body_height * 0.3  # Adjust height of the bottom trim
    pygame.draw.rect(body_surface, DARK_GRAY, (0, car_body_height - trim_height, car_body_width, trim_height))

    # Rotate the body surface with the trim included
    rotated_body = pygame.transform.rotate(body_surface, 0)
    screen.blit(rotated_body, rotated_body.get_rect(center=(X2, Y2)))

    # Draw rotated and smaller windows
    window_width = car_body_width * 0.5
    window_height = car_body_height * 0.2
    window_surface = pygame.Surface((window_width, window_height), pygame.SRCALPHA)
    window_surface.fill(LIGHT_GRAY)
    pygame.draw.rect(window_surface, BLUE, window_surface.get_rect(), 1 )  # Add window border
    rotated_window = pygame.transform.rotate(window_surface, 0)
    screen.blit(rotated_window, rotated_window.get_rect(center=(X2, Y2 - car_body_height * 0.1)))

    # Draw wheels
    wheel_offsets = [
        (-car_body_width // 2 + 10, car_body_height // 2 - 1),  # REAR-left
        (car_body_width // 2 - 10, car_body_height // 2 - 1),   # FRONT-right
    ]
    for offset in wheel_offsets:
        wheel_center = (X2 + offset[0], Y2 + offset[1])
        pygame.draw.circle(screen, BLACK1, wheel_center, wheel_radius)
        pygame.draw.circle(screen, LIGHT_GRAY, wheel_center, wheel_radius // 2)  # Inner rim
            # Draw the nametag (username)
    text = font.render(username, True, (255, 255, 255))  # White text
    screen.blit(text, (X2 -30 , Y2 +20 ))
def oncoming_traffic(player_hitbox, player2_hitbox):
    """
    Spawns and updates the oncoming traffic cars, and checks for collisions with the player.
    If a collision is detected, the game transitions to the game over screen.
    """
    global oncoming_cars, in_game, in_game_over, current_gear
    wheel_radius = 8
    # Speed of oncoming cars relative to gear
    car_speed = {
        "N": 5,
        1: 12,
        2: 16,
        3: 20,
        4: 30,
        5: 30,
        6: 30
    }.get(current_gear, 0)

    # Define car properties
    car_width, car_height = 50, 30  # Wider dimensions for a more car-like look
    spawn_chance = 0.05  # Probability of spawning a car each frame
    spawn_positions = [125, 170, 223, 275, 325, 375, 411]  # 7 static vertical positions

    # List of possible car colors
    colors = [
        (255, 0, 0),    # Red
        (0, 255, 0),    # Green
        (0, 0, 255),    # Blue
        (255, 255, 0),  # Yellow
        (0, 255, 255),  # Cyan
        (255, 0, 255),  # Magenta
        (255, 165, 0)   # Orange
    ]

    # Spawning multiple cars
    if random.random() < spawn_chance:
        for _ in range(random.randint(1, 3)):  # Spawn between 1 and 3 cars each time
            spawn_y = random.choice(spawn_positions)
            car_color = random.choice(colors)  # Random color for each car
            
            # Ensure no car spawns too close to another
            if all(abs(spawn_y - car[1]) >= car_height for car in oncoming_cars):
                oncoming_cars.append([1800, spawn_y, car_color])  # Add car with color

    # Update positions of all oncoming cars
    for car in oncoming_cars:
        car[0] -= car_speed  # Move left by car_speed

    # Remove cars that are off-screen
    oncoming_cars = [car for car in oncoming_cars if car[0] + car_width > 0]

    # Draw each oncoming car with a side-view profile
    for car in oncoming_cars:
        car_x, car_y, car_color = car[0], car[1], car[2]
        
        # Draw car body
        car_body = pygame.Rect(car_x, car_y, car_width, car_height // 2)
        pygame.draw.rect(screen, car_color, car_body)

        # Draw roof (slightly smaller than the body)
        roof_height = car_height // 4
        roof_width = car_width * 0.6
        roof_x = car_x + (car_width - roof_width) // 2
        roof_y = car_y - roof_height // 2
        roof = pygame.Rect(roof_x, roof_y, roof_width, roof_height)
        pygame.draw.rect(screen, car_color, roof)

        # Draw windows
        window_color = (200, 200, 200)  # Light gray
        window_width = roof_width // 3
        window_height = roof_height * 0.7
        for i in range(3):  # Draw 3 windows
            window_x = roof_x + i * (window_width + 2)
            window_y = roof_y + (roof_height - window_height) // 2
            pygame.draw.rect(screen, window_color, (window_x, window_y, window_width, window_height))

        wheel_offsets = [
            (car_width // 4, car_height - wheel_radius - 5),   # Front-right
            (-car_width // 4, car_height - wheel_radius - 5)   # Rear-left
        ]
        for offset in wheel_offsets:
            wheel_center = (car_x + car_width // 2 + offset[0], car_y + offset[1])
            pygame.draw.circle(screen, (0, 0, 0), wheel_center, wheel_radius)  # Outer wheel
            pygame.draw.circle(screen, (LIGHT_GRAY), wheel_center, wheel_radius // 2)  # Inner rim


        # Draw headlights and taillights
        headlight_radius = 3
    

        # Collision detection
        car_hitbox = pygame.Rect(car[0], car[1], car_width, car_height)  # Hitbox for the car
        if player_hitbox.colliderect(car_hitbox) or player2_hitbox.colliderect(car_hitbox):
            print("Collision detected! Game Over.")  # Debug message
            in_game = False
            in_game_over = True

        # Draw headlights (side profile)
        headlight_color = RED  
        headlight_radius = car_height // 8
        pygame.draw.circle(screen, headlight_color, (car_x + car_width - 0, car_y + car_height // 10), headlight_radius)  # Front headlight
        
        # Draw taillights (side profile)
        taillight_color = YELLOW  
        pygame.draw.circle(screen, taillight_color, (car_x + 2, car_y + car_height // 10), headlight_radius)  # Back taillight


        # Check for collision with the players
        if player_hitbox.colliderect(car_hitbox):
            print("Collision detected! Game Over.")  # Debug message
            in_game = False
            in_game_over = True
        if player2_hitbox.colliderect(car_hitbox):
            print("Collision detected! Game Over.")  # Debug message
            in_game = False
            in_game_over = True
def draw_blue_traffic(screen, x, y, car_width, car_height, car_image):
    """
    Draws a car at the specified x and y position using a fixed car image.
    The image is resized to fit the car's hitbox size.
    """
    car_image = pygame.transform.scale(car_image, (car_width, car_height))  # Resize the image
    screen.blit(car_image, (x, y))  # Draw the resized car at the given position
def slow_blue_traffic(player1_hitbox, player2_hitbox):
    """
    Spawns and updates the slow blue traffic cars, and checks for collisions with the player.
    If a collision is detected, the game transitions to the game over screen.
    """
    global slow_blue_cars, in_game, in_game_over, current_gear, distance
    car_speed = {  # Speed of the blue cars (much slower than the original cars)
        "N": -2,
        1: -1,
        2: 1,
        3: 5,
        4: 6,
        5: 7,
        6: 8
    }.get(current_gear, 0)

    # List of possible car colors
    colors = [
        (255, 0, 0),    # Red
        (0, 255, 0),    # Green
        (0, 0, 255),    # Blue
        (255, 255, 0),  # Yellow
        (0, 255, 255),  # Cyan
        (255, 0, 255),  # Magenta
        (255, 165, 0)   # Orange
    ]

    car_width, car_height = 60, 30  # Dimensions of the blue cars
    spawn_chance = 0.03  # Increased chance to spawn a car per frame (higher to get more cars)
    spawn_positions = [455, 515, 565 , 615, 665, 715, 755]  # New set of vertical positions

    # Variables to track speed changes
    random_decrease_time = None
    random_increase_time = None
    decrease_duration = random.choice([3, 4])  # Extended duration for decrease (3 or 4 seconds)
    increase_duration = random.choice([3, 4])  # Extended duration for increase (3 or 4 seconds)

    # Calculate the max number of cars per lane based on the distance traveled
    additional_cars = int(distance // 1000)  # 1 car added per kilometer
    max_cars_per_lane = 1 + additional_cars  # Minimum 1 car per lane, increasing with distance

    # Delay spawning cars for 3 seconds after game starts
    if time.time() - game_start_time > 0:
        # Loop through lanes and spawn cars for each lane
        for spawn_y in spawn_positions:
            # Loop to allow multiple cars in the same lane
            for _ in range(max_cars_per_lane):
                if random.random() < spawn_chance:  # Chance to spawn a car in the current lane
                    # Ensure no car spawns too close to an existing one in the same lane
                    if not any(abs(spawn_y - car[1]) < car_height for car in slow_blue_cars):
                        car_color = random.choice(colors)  # Random color for each car
                        car_image = random.choice(car_images)  # Select a random image for this car
                        slow_blue_cars.append([1800, spawn_y, car_color, car_image])  # Append the car image

    # Update positions of all slow blue cars
    for car in slow_blue_cars:
        # Handle random speed decreases and increases
        if random_decrease_time is None or time.time() - random_decrease_time > decrease_duration:
            if random.random() < 0.05:  # Random chance for decrease
                random_decrease_time = time.time()
                if car_speed > -2:  # Avoid drastic speed decrease on very low speeds
                    car_speed -= random.choice([1, 2])  # Decrease speed by 1 or 2

        if random_increase_time is None or time.time() - random_increase_time > increase_duration:
            if random.random() < 0.04:  # Random chance for increase
                random_increase_time = time.time()
                if car_speed < 8:  # Avoid going overboard with the speed increase
                    car_speed += random.choice([1, 2])  # Increase speed by 1 or 2

        car[0] -= car_speed  # Move left by car_speed

    # Remove cars that are off-screen
    slow_blue_cars = [car for car in slow_blue_cars if car[0] + car_width > 0]

    # Check for collisions and draw the slow blue cars
    for car in slow_blue_cars:
        car_hitbox = pygame.Rect(car[0], car[1], car_width, car_height)  # Hitbox for the car
        draw_blue_traffic(screen, car[0], car[1], car_width, car_height, car[3])  # Draw the car with the fixed image

        # Check for collision with the players
        if player1_hitbox.colliderect(car_hitbox):
            print("Collision detected! Game Over.")  # Debug message
            in_game = False
            in_game_over = True
        if player2_hitbox.colliderect(car_hitbox):
            print("Collision detected! Game Over.")  # Debug message
            in_game = False
            in_game_over = True




# Initialize variables
player_2_active = False  # Ensure this is initialized before the loop
x2, y2 = 1800, 500  # Default spawn position for Player 2
running = True
in_menu = True
in_game = False
in_game_over = False


while running:
    if in_menu:
        # Display the main menu
        screen.fill(BLACK)
        draw_arena_tiles()
        draw_arena_border()
        draw_info_bars()
        draw_middle_line()
        draw_player(player_x, player_y, player_tilt)
        draw_speed_and_distance()
        draw_gear()
        #handle_input()
        
        # Display menu text
        font = pygame.font.SysFont('Arial', 20)
        text = font.render("Press ENTER to Start", True, WHITE)
        screen.blit(text, (screen_width // 2 - 250, screen_height // 2 - 24))

        pygame.display.flip()

        # Handle input for starting or quitting the game
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    in_menu = False
                    in_game = True
                elif event.key == pygame.K_ESCAPE:
                    running = False

    elif in_game:
        # Handle game logic (movement, speed, etc.)
        keys = pygame.key.get_pressed()  # Check keys continuously

        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # Check for "L" key press to activate Player 2
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_l and not player_2_active:
                    player_2_active = True
                    x2, y2 = 1800, 700  # Spawn Player 2 at this position

        # Update game state based on key presses
        player_x, player_y = handle_player_movement(keys, player_x, player_y)
        handle_gear_change(keys)
        update_speed_and_distance()
        # Create player's hitbox
        player_hitbox = pygame.Rect(
            player_x - PLAYER_WIDTH // 2,  # Left
            player_y - PLAYER_HEIGHT // 2,  # Top
            PLAYER_WIDTH,  # Width
            PLAYER_HEIGHT  # Height
        )
        player1_hitbox = pygame.Rect(
            player_x - PLAYER_WIDTH // 2, player_y - PLAYER_HEIGHT // 2,
            PLAYER_WIDTH, PLAYER_HEIGHT
        )
        if player_2_active: 
            player2_hitbox = pygame.Rect(
                x2 - PLAYER_WIDTH // 2, y2 - PLAYER_HEIGHT // 2,
                PLAYER_WIDTH, PLAYER_HEIGHT
            )
        else:
            player2_hitbox = pygame.Rect(-1000, -1000, PLAYER_WIDTH, PLAYER_HEIGHT)  # Place it far off-screen


        # Clear screen and draw everything
        screen.fill(BLACK)
        draw_arena_tiles()
        draw_arena_border()
        draw_info_bars()
        draw_middle_line()
        draw_player(player_x, player_y, player_tilt)
        draw_speed_and_distance()
        draw_gear()
        oncoming_traffic(player_hitbox, player2_hitbox)
        slow_blue_traffic(player1_hitbox, player2_hitbox)
        # Update Player 2 movement if active
        # Draw Player 2 if active
        if player_2_active:
            spawn_square(username, x2, y2)
            x2, y2 = handle_player2_movement(keys, x2, y2)  


        # Check for collision
        if player_2_active and player1_hitbox.colliderect(player2_hitbox):
            in_game = False
            in_game_over = True
            print("Collision detected! Game Over.")  # Debug message

        # Check if game over condition is met
        if check_game_over(player_x):
            in_game = False
            in_game_over = True
        #player 2 deletion  if they fall behind
        if check_player2_falls_behind(player2_hitbox):
            player_2_active = False


        # Debug output (optional)
        if DEBUG:
            print(f"Player 1 Hitbox: {player1_hitbox}")
            print(f"Player 2 Hitbox: {player2_hitbox}")

        pygame.display.flip()
        clock.tick(FPS)

    elif in_game_over:
        # Display the game-over screen
        game_over_screen()

        # Handle user input during game-over screen
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    # Reset and start a new game
                    player_x = 1000
                    player_y = 600
                    in_game_over = False
                    in_game = True
                    player_2_active = False
                    x2, y2 = 1800, 700  # Reset Player 2 position
                    speed = 30
                    distance = 0
                    current_gear = "N"
                    oncoming_cars = []
                    slow_blue_cars = []
                elif event.key == pygame.K_q:
                    running = False

        clock.tick(FPS)

pygame.quit()
sys.exit()
