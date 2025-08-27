import pygame
import random
import time

# Constants
WIDTH, HEIGHT = 900, 600  # Extended for the info panel
GRID_SIZE = 8
INFO_PANEL_WIDTH = 200  # Space for displaying ant info
WORKER_COUNT = 2  # Start with 2 workers
WORKER_SPEED = 10
QUEEN_SPEED = 25  # Moves more actively
SPAWN_INTERVAL = 10  # Queen spawns a new worker every 10 minutes
DIG_DELAY = 10  # Digging takes time

# Colors
BROWN = (139, 69, 19)  # Dirt
DARK_BROWN = (100, 50, 20)  # Dug-out area
GLASS_BLUE = (173, 216, 230)  # Light blue glass
BLACK = (0, 0, 0)
RED = (200, 0, 0)
QUEEN_COLOR = (255, 100, 100)
HOLE_COLOR = (150, 100, 50)
WHITE = (255, 255, 255)

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Ant Farm Simulation")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 14)

# Create dirt grid
cols = (WIDTH - INFO_PANEL_WIDTH) // GRID_SIZE
rows = HEIGHT // GRID_SIZE
dirt_grid = [[1 for _ in range(rows)] for _ in range(cols)]  # 1 = dirt, 0 = empty space

# Lower starting area - first few rows are now dirt
for x in range(cols):
    for y in range(3):  # First 3 rows are open for ants to move
        dirt_grid[x][y] = 0

# Ant classes
class WorkerAnt:
    def __init__(self, ant_id):
        self.id = ant_id
        self.x, self.y = random.randint(0, cols - 1), 3  # Start on dirt
        self.carrying_dirt = False
        self.dig_timer = 0
        self.move_timer = 0
        self.health = 100

    def move(self):
        self.move_timer += 1
        if self.move_timer < WORKER_SPEED:
            return
        self.move_timer = 0

        if self.carrying_dirt:
            # Return to the top of the dug-out area
            if self.y > 3 and dirt_grid[self.x][self.y - 1] == 0:
                self.y -= 1
            else:
                # Drop the dirt in a random empty spot
                empty_spots = [(x, y) for x in range(cols) for y in range(rows) if dirt_grid[x][y] == 0]
                if empty_spots:
                    drop_x, drop_y = random.choice(empty_spots)
                    dirt_grid[drop_x][drop_y] = 1  # Place dirt
                self.carrying_dirt = False
        else:
            # Look for a nearby spot to dig
            directions = [(0, 1), (-1, 0), (1, 0)]  # Down, Left, Right
            random.shuffle(directions)

            for dx, dy in directions:
                nx, ny = self.x + dx, self.y + dy
                if 0 <= nx < cols and 0 <= ny < rows:
                    if dirt_grid[nx][ny] == 1:  # Dig if dirt is present
                        self.dig_timer += 1
                        if self.dig_timer >= DIG_DELAY:
                            dirt_grid[nx][ny] = 0
                            self.carrying_dirt = True
                            self.dig_timer = 0
                        return
                    elif dirt_grid[nx][ny] == 0:  # Move into open space
                        self.x, self.y = nx, ny
                        return

    def draw(self, surface):
        pygame.draw.circle(surface, RED, (self.x * GRID_SIZE + GRID_SIZE // 2, self.y * GRID_SIZE + GRID_SIZE // 2), GRID_SIZE // 2)

class QueenAnt:
    def __init__(self):
        self.x = random.randint(0, cols - 1)
        self.y = 3  # Start on dirt
        self.spawn_timer = time.time()
        self.move_timer = 0  # Slow movement
        self.health = 150  # Queen has higher health

    def move(self):
        self.move_timer += 1
        if self.move_timer < QUEEN_SPEED:
            return
        self.move_timer = 0

        # Find the deepest open space
        lowest_y = self.y
        for x in range(cols):
            for y in range(rows):
                if dirt_grid[x][y] == 0 and y > lowest_y:
                    lowest_y = y

        # Move only into open spaces
        if self.y < lowest_y and dirt_grid[self.x][self.y + 1] == 0:
            self.y += 1
        elif self.y > lowest_y and dirt_grid[self.x][self.y - 1] == 0:
            self.y -= 1

    def spawn_worker(self):
        if time.time() - self.spawn_timer >= SPAWN_INTERVAL:
            self.spawn_timer = time.time()
            return WorkerAnt(len(workers) + 1)
        return None

    def draw(self, surface):
        pygame.draw.circle(surface, QUEEN_COLOR, (self.x * GRID_SIZE + GRID_SIZE // 2, self.y * GRID_SIZE + GRID_SIZE // 2), GRID_SIZE // 2 + 2)

# Create initial ants
workers = [WorkerAnt(i) for i in range(WORKER_COUNT)]
queen = QueenAnt()

def draw_info_panel(surface, workers, queen):
    pygame.draw.rect(surface, BLACK, (WIDTH - INFO_PANEL_WIDTH, 0, INFO_PANEL_WIDTH, HEIGHT))
    y_offset = 20

    # Draw Queen info
    queen_text = font.render("Queen Ant", True, WHITE)
    surface.blit(queen_text, (WIDTH - INFO_PANEL_WIDTH + 10, y_offset))
    y_offset += 20

    queen_health_text = font.render(f"Health: {queen.health}", True, WHITE)
    surface.blit(queen_health_text, (WIDTH - INFO_PANEL_WIDTH + 10, y_offset))
    y_offset += 30

    # Draw Worker Ants info
    worker_text = font.render("Worker Ants:", True, WHITE)
    surface.blit(worker_text, (WIDTH - INFO_PANEL_WIDTH + 10, y_offset))
    y_offset += 20

    for worker in workers:
        worker_info = font.render(f"Ant {worker.id} - Health: {worker.health}", True, WHITE)
        surface.blit(worker_info, (WIDTH - INFO_PANEL_WIDTH + 10, y_offset))
        y_offset += 15
        if y_offset > HEIGHT - 20:  # Prevent overflow
            break

running = True
while running:
    screen.fill(GLASS_BLUE)  # Glass background

    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Update workers
    for worker in workers:
        worker.move()

    # Update queen
    queen.move()
    new_worker = queen.spawn_worker()
    if new_worker:
        workers.append(new_worker)

    # Draw dirt grid
    for x in range(cols):
        for y in range(rows):
            color = BROWN if dirt_grid[x][y] == 1 else DARK_BROWN
            pygame.draw.rect(screen, color, (x * GRID_SIZE, y * GRID_SIZE, GRID_SIZE, GRID_SIZE))

    # Draw hole at the top
    pygame.draw.rect(screen, HOLE_COLOR, (0, 0, WIDTH - INFO_PANEL_WIDTH, GRID_SIZE))

    # Draw ants
    for worker in workers:
        worker.draw(screen)
    queen.draw(screen)

    # Draw info panel
    draw_info_panel(screen, workers, queen)

    pygame.display.flip()
    clock.tick(30)

pygame.quit()
