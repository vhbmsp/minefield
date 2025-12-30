import math
import pygame
import random
import sys
import copy

# Constants
TOP_BAR_HEIGHT = 100

WIDTH, HEIGHT = 1000 , 560  + TOP_BAR_HEIGHT
CELL_SIZE = 40
BOARD_ROWS = 12  # Playable rows (excluding top and bottom safe zones)
BOARD_COLS = 19
TOTAL_ROWS = BOARD_ROWS + 2  # +2 for top and bottom safe zones
MINES_PER_ROW = 3  # For the first level

FONT_SIZE = 36

POINTS_PER_CELL = 10
VISITED_CELL = -2  # Value for cells that have been visited and points collected

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
LIGHT_GRAY = (200, 200, 200)
DARK_GRAY = (100, 100, 100)
SAFE_ZONE_COLOR = (220, 220, 220)
NUMBER_COLORS = {
    1: (0, 0, 255),  # Blue
    2: (0, 128, 0),  # Green
    3: (255, 0, 0),  # Red
    4: (128, 0, 128),  # Purple
    5: (128, 0, 0),  # Dark red
    6: (0, 128, 128),  # Cyan
    7: (0, 0, 0),  # Black
    8: (128, 128, 128)  # Gray
}

RESET_BOARD = [[10 for _ in range(BOARD_COLS)] for _ in range(TOTAL_ROWS)]


pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("MineField")
font = pygame.font.SysFont("arial", FONT_SIZE)
small_font = pygame.font.SysFont("arial", 24)

clock = pygame.time.Clock()

def ensure_safe_path(board, mines_per_row):
    """
    Ensures there is at least one column without any mines across all playable rows.
    This guarantees a full vertical safe path exists (a possible solution).
    """

    # Safe zones
    for col in range(BOARD_COLS):
        board[0][col] = 0
        board[TOTAL_ROWS - 1][col] = 0

    num_attempts = 0
    while num_attempts < 100:  # Prevent infinite loop
        # Place mines
        for row in range(1, TOTAL_ROWS - 1):  # Only playable rows
            cols = list(range(BOARD_COLS))
            random.shuffle(cols)
            mine_cols = cols[:mines_per_row]
            for col in mine_cols:
                board[row][col] = -1  # -1 represents mine

        # Check for a safe column
        for col in range(BOARD_COLS):
            safe = True
            for row in range(1, TOTAL_ROWS - 1):
                if board[row][col] == -1:
                    safe = False
                    break
            if safe:
                return  # Found a safe column, board is valid

        # If no safe column, reset mines and try again
        for row in range(1, TOTAL_ROWS - 1):
            for col in range(BOARD_COLS):
                if board[row][col] == -1:
                    board[row][col] = POINTS_PER_CELL
        num_attempts += 1

    print("Warning: Could not find a guaranteed safe path after many attempts.")

def draw_board(board, player_row=1, player_col=0, player_is_dead=False, level = 0, lives = 0, score = 0):
    """Draw the game board, numbers, safe zones, and player position."""
    # Clear screen
    screen.fill(BLACK)

    debug = False

    # Draw top bar (lives, score)
    pygame.draw.rect(screen, DARK_GRAY, (0, 0, WIDTH, TOP_BAR_HEIGHT))
    lives_text = small_font.render("Lives: {}".format(lives), True, WHITE)
    score_text = small_font.render("Score: {}".format(score), True, WHITE)
    screen.blit(lives_text, (20, 15))
    screen.blit(score_text, (WIDTH - 200, 15))

    # Exit Door
    exit_col = math.floor(BOARD_COLS/ 2)
    x = exit_col * CELL_SIZE
    y =  TOP_BAR_HEIGHT - CELL_SIZE+1
    rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)
    pygame.draw.rect(screen, WHITE, rect)

    rect = pygame.Rect(x+1, y+1, CELL_SIZE-2, CELL_SIZE-2)
    pygame.draw.rect(screen, NUMBER_COLORS[2] , rect)


        # Draw board background
    board_y = TOP_BAR_HEIGHT
    for r in range(TOTAL_ROWS):
        for c in range(BOARD_COLS):
            x = c * CELL_SIZE
            y = board_y + r * CELL_SIZE
            rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)

            # Safe zones: light gray
            if board[r][c] == 0 or board[r][c] == -2:
                pygame.draw.rect(screen, SAFE_ZONE_COLOR, rect)
            else:
                pygame.draw.rect(screen, DARK_GRAY, rect)

            # if player is in a mine, show mines map
            if player_is_dead == True and board[r][c] == -1:
                # Draw player position (simple circle for now)
                mine_x = c * CELL_SIZE + CELL_SIZE // 2
                mine_y = board_y + r * CELL_SIZE + CELL_SIZE // 2
                pygame.draw.circle(screen, (255, 0, 0), (mine_x, mine_y), CELL_SIZE // 3)

            # Border
            pygame.draw.rect(screen, WHITE, rect, 1)

            if debug:
                debug_x = c * CELL_SIZE + CELL_SIZE // 2
                debug_y = board_y + r * CELL_SIZE + CELL_SIZE // 2
                debug_text = small_font.render("{}".format(board[r][c]), True, WHITE)
                screen.blit(debug_text, (debug_x, debug_y))

    player_x = (player_col * CELL_SIZE) + (CELL_SIZE // 2)
    player_y = board_y + (player_row * CELL_SIZE) + (CELL_SIZE // 2)

    # Draw player position (simple circle for now)
    if player_is_dead:
        rip_text = small_font.render(f"X", True, BLACK)
        screen.blit(rip_text, (player_x - (rip_text.get_width() // 2), player_y - (rip_text.get_height() // 2)))
        continue_text = small_font.render(f"Continue (Y/n)?", True, WHITE)
        screen.blit(continue_text, (WIDTH // 2 - continue_text.get_width() // 2, 15))
    else:
        pygame.draw.circle(screen, NUMBER_COLORS[2], (player_x, player_y), CELL_SIZE // 3)

        # Draw current adjacent mine count (example at top center)
        current_adj = 0
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]  # top, bottom, left, right only

        for dr, dc in directions:
            nr, nc = player_row + dr, player_col + dc
            if 0 <= nr < TOTAL_ROWS and 0 <= nc < BOARD_COLS and board[nr][nc] == -1:
                current_adj += 1

        adj_text = small_font.render(f"Adjacent mines: {current_adj}", True, WHITE)
        screen.blit(adj_text, (WIDTH // 2 - adj_text.get_width() // 2, 15))

    level_text = small_font.render(f"Level: {level}", True, WHITE)
    screen.blit(level_text, (800, 150))
def main():
    # Initialize board: 0 = safe zone, 10 = points cells, -1 = mine, 100 = lady
    board = copy.deepcopy(RESET_BOARD)

    level = 1
    lives = 3
    score = 0
    mines_per_row = MINES_PER_ROW
    player_is_dead = False

    # Safe zones have no mines or numbers
    ensure_safe_path(board, mines_per_row)

    # Player starts in top safe zone, left side
    player_row = BOARD_ROWS +1
    player_col = math.floor(BOARD_COLS/ 2)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or pygame.key.get_pressed()[pygame.K_ESCAPE]:
                running = False
            # Optional: basic movement for testing (arrow keys)
            if event.type == pygame.KEYDOWN:
                if not player_is_dead:
                    if event.key == pygame.K_LEFT and player_col > 0:
                        player_col -= 1
                    if event.key == pygame.K_RIGHT and player_col < BOARD_COLS - 1:
                        player_col += 1
                    if event.key == pygame.K_DOWN and player_row < TOTAL_ROWS - 1:
                        player_row += 1
                    if event.key == pygame.K_UP:
                            # test if is exit door
                            if player_row > 0 :
                                player_row -= 1
                            elif player_col == math.floor(BOARD_COLS/ 2):
                                level += 1
                                mines_per_row += 1
                                player_row = BOARD_ROWS +1
                                player_col = math.floor(BOARD_COLS/ 2)
                                board = copy.deepcopy(RESET_BOARD)
                                ensure_safe_path(board, mines_per_row)
                else:
                    # continue ?
                    if event.key == pygame.K_y:
                        lives -= 1
                        if lives == -1:
                            level = 1
                            score = 0
                            lives = 3
                            mines_per_row = MINES_PER_ROW
                        # reset player
                        player_is_dead = False
                        player_row = BOARD_ROWS + 1
                        player_col = math.floor(BOARD_COLS / 2)

                        # generate new map
                        board = copy.deepcopy(RESET_BOARD)
                        ensure_safe_path(board, mines_per_row)

                    if event.key == pygame.K_n:
                        # quit game
                        running = False

            if not player_is_dead:
                if board[player_row][player_col] == -1:
                    player_is_dead = True
                else:
                    if board[player_row][player_col] != VISITED_CELL:
                        score += board[player_row][player_col]
                        board[player_row][player_col] = VISITED_CELL  # Mark cell as visited

        draw_board(board, player_row, player_col, player_is_dead, level, lives, score)
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()