import pygame
import sys
import time
import random
from MCTS import GameState, MCTS  

# ---------------- Config ----------------
pygame.init()
FPS = 60

ROWS, COLS = 6, 7
MARGIN = 8
BOTTOM_MARGIN = 40

# Colors
BG_COLOR = (245, 247, 249)
BOARD_BG = (235, 240, 245)
CELL_EMPTY = (255, 255, 255)
PLAYER_COLORS = {
    "You": (49, 189, 160),
    "AI Bot": (50, 60, 80)
}
HOVER_OVERLAY = (200, 205, 210, 120)
HIGHLIGHT = (255, 205, 60)
TEXT_COLOR = (30, 30, 30)
TURN_SCORE_COLOR = (128, 128, 128)
WIN_COLOR = (62, 160, 85)
LOSE_COLOR = (255, 100, 100)
DRAW_COLOR = (255, 205, 0)

# Window
WIDTH, HEIGHT = 1000, 720
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Connect 4")
clock = pygame.time.Clock()

# ---------------- Game state ----------------
board = [["" for _ in range(COLS)] for _ in range(ROWS)]
current_player = "You"
starter_player = "You"
score = {"You": 0, "AI Bot": 0, "Draw": 0}
winner_cells = []
game_over = False
click_anim = None
CLICK_ANIM_MS = 160
computer_delay_start = None
COMPUTER_DELAY = 0.6
last_mouse_pos = (-1, -1)
hover_allowed = True

# ---------------- Helpers ----------------
def other(player):
    return "AI Bot" if player=="You" else "You"

def compute_layout():
    w, h = screen.get_size()
    top_area_ratio = 0.16
    top_area = int(h * top_area_ratio)
    available_h = h - top_area - BOTTOM_MARGIN
    cell_w = (w - (COLS + 1) * MARGIN) / COLS
    cell_h = (available_h - (ROWS + 1) * MARGIN) / ROWS
    cell = int(min(cell_w, cell_h))
    cell = max(28, cell)
    bw = cell * COLS + MARGIN * (COLS + 1)
    bh = cell * ROWS + MARGIN * (ROWS + 1)
    bx = (w - bw) // 2
    by = top_area + max(0, (available_h - bh) // 2)
    return {"cell": cell, "board_x": bx, "board_y": by, "board_w": bw, "board_h": bh,
            "top_area": top_area, "window_w": w, "window_h": h}

def draw_text_with_border(surface, text, font, color, border_color, pos):
    x, y = pos
    offsets = [(-1, -1), (-1,1), (1,-1), (1,1)]
    for ox, oy in offsets:
        surf = font.render(text, True, border_color)
        surface.blit(surf, (x + ox, y + oy))
    surf = font.render(text, True, color)
    surface.blit(surf, pos)

def get_lowest_empty_row(col):
    for r in range(ROWS - 1, -1, -1):
        if board[r][col] == "":
            return r
    return None

def check_winner_and_set():
    global game_over, winner_cells
    winner_cells = []

    for r in range(ROWS):
        for c in range(COLS-3):
            v = board[r][c]
            if v and all(board[r][c+i]==v for i in range(4)):
                winner_cells = [(r, c+i) for i in range(4)]
                score[v] += 1
                game_over = True
                return v

    for c in range(COLS):
        for r in range(ROWS-3):
            v = board[r][c]
            if v and all(board[r+i][c]==v for i in range(4)):
                winner_cells = [(r+i, c) for i in range(4)]
                score[v] += 1
                game_over = True
                return v

    for r in range(ROWS-3):
        for c in range(COLS-3):
            v = board[r][c]
            if v and all(board[r+i][c+i]==v for i in range(4)):
                winner_cells = [(r+i, c+i) for i in range(4)]
                score[v] += 1
                game_over = True
                return v

    for r in range(3, ROWS):
        for c in range(COLS-3):
            v = board[r][c]
            if v and all(board[r-i][c+i]==v for i in range(4)):
                winner_cells = [(r-i, c+i) for i in range(4)]
                score[v] += 1
                game_over = True
                return v

    if all(board[r][c] != "" for r in range(ROWS) for c in range(COLS)):
        score["Draw"] += 1
        game_over = True
        return "Draw"
    return None

def drop_piece(col):
    global current_player, click_anim, game_over, hover_allowed
    if game_over:
        return
    row = get_lowest_empty_row(col)
    if row is None:
        return
    board[row][col] = current_player
    click_anim = {"row": row, "col": col, "start": time.time()*1000, "duration": CLICK_ANIM_MS}
    check_winner_and_set()
    if not game_over:
        current_player = other(current_player)
        hover_allowed = False

def reset_board_for_next_game():
    global board, winner_cells, game_over, click_anim, current_player, starter_player
    board = [["" for _ in range(COLS)] for _ in range(ROWS)]
    winner_cells = []
    click_anim = None
    game_over = False
    starter_player = other(starter_player)
    current_player = starter_player

def draw_board(hover_col=None, show_ghost=True):
    screen.fill(BG_COLOR)
    layout = compute_layout()
    cell = layout["cell"]
    bx, by = layout["board_x"], layout["board_y"]

    panel = pygame.Rect(bx - MARGIN, by - MARGIN,
                        layout["board_w"] + 2*MARGIN, layout["board_h"] + 2*MARGIN)
    pygame.draw.rect(screen, BOARD_BG, panel, border_radius=18)

    if hover_col is not None and not game_over:
        overlay = pygame.Surface((cell + MARGIN, layout["board_h"] + 2*MARGIN), pygame.SRCALPHA)
        overlay.fill(HOVER_OVERLAY)
        col_x = bx + MARGIN + hover_col * (cell + MARGIN) - MARGIN//2
        screen.blit(overlay, (col_x, by - MARGIN))

    rds = int(cell * 0.45)
    for r in range(ROWS):
        for c in range(COLS):
            cx = bx + MARGIN + c * (cell + MARGIN) + cell//2
            cy = by + MARGIN + r * (cell + MARGIN) + cell//2
            val = board[r][c]
            col = PLAYER_COLORS.get(val, CELL_EMPTY)
            pygame.draw.circle(screen, col, (cx, cy), rds)

    if winner_cells:
        for r, c in winner_cells:
            cx = bx + MARGIN + c * (cell + MARGIN) + cell//2
            cy = by + MARGIN + r * (cell + MARGIN) + cell//2
            pygame.draw.circle(screen, HIGHLIGHT, (cx, cy), rds, width=6)

    if hover_col is not None and show_ghost and not game_over:
        lowest = get_lowest_empty_row(hover_col)
        if lowest is not None:
            gx = bx + MARGIN + hover_col * (cell + MARGIN) + cell//2
            gy = by + MARGIN + lowest * (cell + MARGIN) + cell//2
            ghost_color = PLAYER_COLORS[current_player]
            surf = pygame.Surface((rds*2+6, rds*2+6), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*ghost_color, 160), (rds+3, rds+3), rds)
            screen.blit(surf, (gx-rds-3, gy-rds-3))

    if click_anim:
        now = time.time()*1000
        t = (now - click_anim["start"]) / click_anim["duration"]
        if t < 1:
            scale = 1 + 0.22 * (1 - (t-0.5)**2 * 4)
            r = click_anim["row"]
            c = click_anim["col"]
            cx = bx + MARGIN + c*(cell+MARGIN) + cell//2
            cy = by + MARGIN + r*(cell+MARGIN) + cell//2
            val = board[r][c]
            if val:
                col = PLAYER_COLORS[val]
                rr = int(rds * scale)
                pygame.draw.circle(screen, col, (cx, cy), rr)

    fs = max(22, int(cell * 0.35))
    font = pygame.font.SysFont("Segoe UI", fs, bold=True)
    score_font = pygame.font.SysFont("Segoe UI", int(fs*0.75), bold=True)
    score_text = f"You: {score['You']}   |   AI Bot: {score['AI Bot']}   |   Draw: {score['Draw']}"
    score_surf = score_font.render(score_text, True, TURN_SCORE_COLOR)
    sw = layout["window_w"]
    screen.blit(score_surf, ((sw - score_surf.get_width())//2, 20))

    if not game_over:
        turn_text = f"Turn: {current_player}"
        turn_surf = font.render(turn_text, True, TURN_SCORE_COLOR)
        screen.blit(turn_surf, ((sw - turn_surf.get_width())//2, 20 + score_surf.get_height()))

    if game_over:
        if winner_cells:
            winner_name = board[winner_cells[0][0]][winner_cells[0][1]]
            if winner_name == "You":
                msg = "You Win!"
                color = WIN_COLOR
            else:
                msg = "You Lost!"
                color = LOSE_COLOR
        else:
            msg = "Draw!"
            color = DRAW_COLOR
        font_msg = pygame.font.SysFont("Segoe UI", int(cell*1.2), bold=True)
        sw, sh = screen.get_size()
        text_w, text_h = font_msg.size(msg)
        msg_x = (sw - text_w)//2
        msg_y = (sh - text_h)//2
        draw_text_with_border(screen, msg, font_msg, color, (0,0,0), (msg_x, msg_y))

# ---------------- Main Loop ----------------
running = True
game_end_time = None
hover_allowed = True
last_mouse_pos = (-1, -1)

mcts = MCTS(time_limit=0.55, iter_limit=900, c_param=1.4)

while running:
    clock.tick(FPS)
    mouse_pos = pygame.mouse.get_pos()
    mouse_moved = (mouse_pos != last_mouse_pos)
    last_mouse_pos = mouse_pos

    if game_over:
        if game_end_time is None:
            game_end_time = time.time()
        elif time.time() - game_end_time >= 2.3:
            reset_board_for_next_game()
            game_end_time = None


    
    # AI turn handling with delay
    if current_player == "AI Bot" and not game_over:
        if computer_delay_start is None:
            computer_delay_start = time.time()
        elif time.time() - computer_delay_start >= COMPUTER_DELAY:
            # build GameState from current board
            state = GameState(board, current_player)
            # run MCTS search
            chosen_col = mcts.search(state)
            if chosen_col is None:
                available = [c for c in range(COLS) if get_lowest_empty_row(c) is not None]
                if available:
                    chosen_col = random.choice(available)
            if chosen_col is not None:
                drop_piece(chosen_col)
            computer_delay_start = None
            hover_allowed = False


    def get_col_from_mouse(pos):
        layout = compute_layout()
        bx = layout["board_x"]
        cell = layout["cell"]
        x = pos[0]
        rel = x - bx - MARGIN
        if rel < 0:
            return None
        c = int(rel // (cell + MARGIN))
        return c if 0 <= c < COLS else None

    if current_player == "AI Bot":
        hover_col = None
    else:
        if mouse_moved:
            hover_allowed = True
        hover_col = get_col_from_mouse(mouse_pos) if hover_allowed else None

    draw_board(hover_col)
    pygame.display.flip()

    if click_anim and time.time()*1000 - click_anim["start"] > CLICK_ANIM_MS:
        click_anim = None

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.VIDEORESIZE:
            screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
        elif event.type == pygame.MOUSEBUTTONDOWN and not game_over:
            if event.button == 1 and current_player == "You":
                col = get_col_from_mouse(event.pos)
                if col is not None:
                    drop_piece(col)

pygame.quit()
sys.exit()