import pygame
import sys
import random
from collections import deque

# =========================
#  CẤU HÌNH CHUNG
# =========================
SCREEN_WIDTH = 1100
SCREEN_HEIGHT = 720
FPS = 60
HUD_HEIGHT = 80
PADDING = 16

# Mê cung lớn & khó hơn (odd numbers)
MAP_W = 41
MAP_H = 25

# TILE tự fit màn hình
TILE_SIZE = min(
    (SCREEN_WIDTH - 2 * PADDING) // MAP_W,
    (SCREEN_HEIGHT - HUD_HEIGHT - 2 * PADDING) // MAP_H
)

# =========================
#  MÀU SẮC
# =========================
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

WALL = (35, 55, 150)
FLOOR = (14, 18, 35)
GRID = (20, 26, 50)

RED = (255, 80, 80)
GREEN = (80, 230, 120)

YELLOW = (255, 215, 0)
PURPLE = (170, 80, 255)

MONSTER_COLOR = (255, 140, 0)

UI_BG = (18, 20, 34)

# tile codes
T_FLOOR = 0
T_WALL = 1
T_QUIZ = 2

# =========================
#  THAM SỐ QUÁI VẬT
# =========================
MONSTER_COUNT = 4
MONSTER_MOVE_MS = 220
CHASE_RANGE = 10          # <= 10 ô (theo đường đi BFS) thì đuổi
HIT_COOLDOWN_MS = 900     # tránh bị hit liên tục trong 1s


# =========================
#  FONT TIẾNG VIỆT
# =========================
def load_vietnamese_font(size: int, bold: bool = False):
    """
    Ưu tiên font hỗ trợ tiếng Việt trên Windows.
    Nếu muốn chắc chắn 100%: tải NotoSans-Regular.ttf, đặt cùng thư mục
    và đổi FONT_TTF_PATH = "NotoSans-Regular.ttf"
    """
    FONT_TTF_PATH = None  # ví dụ "NotoSans-Regular.ttf"

    if FONT_TTF_PATH:
        try:
            return pygame.font.Font(FONT_TTF_PATH, size)
        except:
            pass

    for name in ["Segoe UI", "Arial", "Tahoma", "Verdana"]:
        f = pygame.font.SysFont(name, size, bold=bold)
        if f:
            return f

    return pygame.font.Font(None, size)


# =========================
#  HELPERS
# =========================
def is_walkable(tile):
    return tile in (T_FLOOR, T_QUIZ)

def neighbors4(x, y):
    for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
        yield x + dx, y + dy


def bfs_full(grid, start):
    """
    BFS từ start ra toàn map.
    return: dist dict, parent dict (để dựng đường đi)
    """
    h = len(grid)
    w = len(grid[0])
    q = deque([start])
    dist = {start: 0}
    parent = {start: None}

    while q:
        x, y = q.popleft()
        for nx, ny in neighbors4(x, y):
            if 0 <= nx < w and 0 <= ny < h and is_walkable(grid[ny][nx]):
                if (nx, ny) not in dist:
                    dist[(nx, ny)] = dist[(x, y)] + 1
                    parent[(nx, ny)] = (x, y)
                    q.append((nx, ny))
    return dist, parent


def reconstruct_next_step(parent, start, goal):
    """
    Với parent map từ BFS (gốc start), dựng step đầu tiên từ start -> goal.
    """
    if goal not in parent:
        return None
    cur = goal
    while parent[cur] is not None and parent[cur] != start:
        cur = parent[cur]
    if parent[cur] == start:
        return cur
    return None


# =========================
#  MAZE GENERATOR (Backtracking + loops)
# =========================
def generate_maze(width: int, height: int, seed=None, extra_loops=0.10):
    rnd = random.Random(seed)
    grid = [[T_WALL for _ in range(width)] for __ in range(height)]

    for y in range(1, height, 2):
        for x in range(1, width, 2):
            grid[y][x] = T_FLOOR

    start = (1, 1)
    stack = [start]
    visited = {start}
    dirs = [(2, 0), (-2, 0), (0, 2), (0, -2)]

    while stack:
        x, y = stack[-1]
        neigh = []
        for dx, dy in dirs:
            nx, ny = x + dx, y + dy
            if 1 <= nx < width - 1 and 1 <= ny < height - 1 and (nx, ny) not in visited:
                neigh.append((nx, ny, dx, dy))
        if neigh:
            nx, ny, dx, dy = rnd.choice(neigh)
            grid[y + dy // 2][x + dx // 2] = T_FLOOR
            visited.add((nx, ny))
            stack.append((nx, ny))
        else:
            stack.pop()

    # add loops: phá thêm tường để maze rối hơn
    walls = []
    for y in range(1, height - 1):
        for x in range(1, width - 1):
            if grid[y][x] == T_WALL:
                if grid[y][x - 1] == T_FLOOR and grid[y][x + 1] == T_FLOOR:
                    walls.append((x, y))
                elif grid[y - 1][x] == T_FLOOR and grid[y + 1][x] == T_FLOOR:
                    walls.append((x, y))

    rnd.shuffle(walls)
    open_count = int(len(walls) * extra_loops)
    for i in range(open_count):
        x, y = walls[i]
        grid[y][x] = T_FLOOR

    return grid


def pick_treasure_position(grid, s1, s2):
    d1, _ = bfs_full(grid, s1)
    d2, _ = bfs_full(grid, s2)

    best = None
    best_score = None
    for p, v1 in d1.items():
        if p in d2:
            v2 = d2[p]
            if v1 < 10 or v2 < 10:
                continue
            mn = min(v1, v2)
            bal = abs(v1 - v2)
            score = (mn * 1000) - (bal * 20)
            if best_score is None or score > best_score:
                best_score = score
                best = p

    if not best:
        floors = [(x, y) for y in range(len(grid)) for x in range(len(grid[0])) if grid[y][x] == T_FLOOR]
        best = random.choice(floors)
    return best


def place_quiz_tiles(grid, s1, s2, treasure, count=16, min_apart=4):
    rnd = random.Random()
    h = len(grid)
    w = len(grid[0])
    floors = [(x, y) for y in range(h) for x in range(w) if grid[y][x] == T_FLOOR]
    rnd.shuffle(floors)

    chosen = []

    def manhattan(a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    for p in floors:
        if len(chosen) >= count:
            break
        if manhattan(p, s1) < 8 or manhattan(p, s2) < 8:
            continue
        if manhattan(p, treasure) < 6:
            continue
        ok = True
        for c in chosen:
            if manhattan(p, c) < min_apart:
                ok = False
                break
        if ok:
            chosen.append(p)

    for (x, y) in chosen:
        grid[y][x] = T_QUIZ

    return chosen


# =========================
#  QUESTIONS: TRẮC NGHIỆM
# =========================
def generate_mcq():
    t = random.choice(["add", "sub", "mul", "div", "trick"])
    if t == "add":
        a = random.randint(10, 99)
        b = random.randint(10, 99)
        correct = a + b
        q = f"Tính: {a} + {b} = ?"
    elif t == "sub":
        a = random.randint(20, 120)
        b = random.randint(10, a)
        correct = a - b
        q = f"Tính: {a} - {b} = ?"
    elif t == "mul":
        a = random.randint(3, 15)
        b = random.randint(3, 15)
        correct = a * b
        q = f"Tính: {a} × {b} = ?"
    elif t == "div":
        b = random.randint(2, 12)
        correct = random.randint(2, 20)
        a = b * correct
        q = f"Tính: {a} ÷ {b} = ?"
    else:
        q = "Số nhỏ nhất có 2 chữ số là số nào?"
        correct = 10

    options = {correct}
    while len(options) < 4:
        delta = random.randint(-18, 18)
        cand = correct + delta
        if cand >= 0:
            options.add(cand)

    options = list(options)
    random.shuffle(options)
    correct_idx = options.index(correct)

    return {
        "question": q,
        "options": options,
        "correct_idx": correct_idx
    }


def show_question_popup(screen, font_title, font_text):
    """
    FIX LỖI UI: box tự tính chiều cao để không đè option 4 / dòng hướng dẫn.
    """
    data = generate_mcq()
    q_text = data["question"]
    options = data["options"]
    correct = data["correct_idx"]

    w, h = screen.get_size()

    opt_h = 52
    gap = 12
    top_area = 140
    bottom_area = 60
    box_w = 600
    # đủ cho 4 options + guide
    box_h = top_area + (4 * opt_h) + (3 * gap) + bottom_area

    box = pygame.Rect(w // 2 - box_w // 2, h // 2 - box_h // 2, box_w, box_h)

    option_rects = []
    opt_w = box_w - 60
    start_y = box.y + top_area
    for i in range(4):
        r = pygame.Rect(box.x + 30, start_y + i * (opt_h + gap), opt_w, opt_h)
        option_rects.append(r)

    selected = None
    feedback = None
    feedback_color = WHITE
    feedback_time = 0

    while True:
        overlay = pygame.Surface((w, h))
        overlay.set_alpha(190)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))

        pygame.draw.rect(screen, WHITE, box, border_radius=14)
        pygame.draw.rect(screen, (70, 110, 255), box, 3, border_radius=14)

        title = font_title.render("TRẢ LỜI CÂU HỎI ĐỂ ĐI TIẾP", True, (40, 80, 200))
        screen.blit(title, (box.x + 30, box.y + 22))

        q_render = font_text.render(q_text, True, BLACK)
        screen.blit(q_render, (box.x + 30, box.y + 80))

        if feedback:
            fb = font_text.render(feedback, True, feedback_color)
            screen.blit(fb, (box.x + 30, box.y + 110))
            if pygame.time.get_ticks() - feedback_time > 650:
                return selected == correct

        for i, r in enumerate(option_rects):
            is_hover = r.collidepoint(pygame.mouse.get_pos())
            bg = (240, 240, 240) if not is_hover else (220, 235, 255)
            pygame.draw.rect(screen, bg, r, border_radius=10)
            pygame.draw.rect(screen, (150, 150, 150), r, 2, border_radius=10)

            label = font_text.render(f"{i+1}) {options[i]}", True, (30, 30, 30))
            screen.blit(label, (r.x + 14, r.y + 14))

        guide = font_text.render("Chọn đáp án: [1-4] hoặc click | ESC: bỏ qua", True, (80, 80, 80))
        screen.blit(guide, (box.x + 30, box.y + box_h - 40))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False

                if event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4,
                                 pygame.K_KP1, pygame.K_KP2, pygame.K_KP3, pygame.K_KP4):
                    key_map = {
                        pygame.K_1: 0, pygame.K_2: 1, pygame.K_3: 2, pygame.K_4: 3,
                        pygame.K_KP1: 0, pygame.K_KP2: 1, pygame.K_KP3: 2, pygame.K_KP4: 3
                    }
                    selected = key_map[event.key]
                    if selected == correct:
                        feedback = "✅ Đúng! Bạn được đi tiếp."
                        feedback_color = (40, 160, 60)
                    else:
                        feedback = "❌ Sai! Bạn bị chặn lại."
                        feedback_color = (200, 40, 40)
                    feedback_time = pygame.time.get_ticks()

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for i, r in enumerate(option_rects):
                    if r.collidepoint(event.pos):
                        selected = i
                        if selected == correct:
                            feedback = "✅ Đúng! Bạn được đi tiếp."
                            feedback_color = (40, 160, 60)
                        else:
                            feedback = "❌ Sai! Bạn bị chặn lại."
                            feedback_color = (200, 40, 40)
                        feedback_time = pygame.time.get_ticks()


# =========================
#  PLAYER
# =========================
class Player:
    def __init__(self, x, y, color, controls, name):
        self.x = x
        self.y = y
        self.color = color
        self.controls = controls
        self.name = name
        self.has_treasure = False
        self.start_pos = (x, y)
        self.last_hit_ms = -10_000

    def return_to_base(self):
        self.x, self.y = self.start_pos

    def move(self, dx, dy, grid, opponent, screen, font_title, font_text):
        nx, ny = self.x + dx, self.y + dy
        if ny < 0 or ny >= len(grid) or nx < 0 or nx >= len(grid[0]):
            return
        if not is_walkable(grid[ny][nx]):
            return

        # quiz
        if grid[ny][nx] == T_QUIZ:
            ok = show_question_popup(screen, font_title, font_text)
            if not ok:
                return
            grid[ny][nx] = T_FLOOR

        # PvP cướp kho báu
        if nx == opponent.x and ny == opponent.y:
            if (not self.has_treasure) and opponent.has_treasure:
                opponent.has_treasure = False
                self.has_treasure = True
                opponent.return_to_base()

        self.x, self.y = nx, ny

    def draw(self, surface, ox, oy):
        rect = (ox + self.x * TILE_SIZE + 4, oy + self.y * TILE_SIZE + 4, TILE_SIZE - 8, TILE_SIZE - 8)
        pygame.draw.rect(surface, self.color, rect, border_radius=10)

        if self.has_treasure:
            cx = ox + self.x * TILE_SIZE + TILE_SIZE // 2
            cy = oy + self.y * TILE_SIZE + TILE_SIZE // 2
            pygame.draw.circle(surface, YELLOW, (cx, cy), max(4, TILE_SIZE // 8))
            pygame.draw.rect(surface, YELLOW, rect, 2, border_radius=10)


# =========================
#  MONSTER
# =========================
class Monster:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.next_move_ms = 0

    def draw(self, surface, ox, oy):
        cx = ox + self.x * TILE_SIZE + TILE_SIZE // 2
        cy = oy + self.y * TILE_SIZE + TILE_SIZE // 2
        r = max(6, TILE_SIZE // 3)
        pygame.draw.circle(surface, MONSTER_COLOR, (cx, cy), r)
        pygame.draw.circle(surface, (10, 10, 10), (cx - r // 3, cy - r // 4), max(2, r // 6))
        pygame.draw.circle(surface, (10, 10, 10), (cx + r // 3, cy - r // 4), max(2, r // 6))

    def step(self, grid, players, now_ms):
        if now_ms < self.next_move_ms:
            return

        self.next_move_ms = now_ms + MONSTER_MOVE_MS

        start = (self.x, self.y)
        dist, parent = bfs_full(grid, start)

        # chọn target gần nhất trong CHASE_RANGE
        targets = []
        for p in players:
            pos = (p.x, p.y)
            if pos in dist and dist[pos] <= CHASE_RANGE:
                targets.append((dist[pos], pos))
        targets.sort(key=lambda t: t[0])

        if targets:
            # đuổi theo target gần nhất
            goal = targets[0][1]
            nxt = reconstruct_next_step(parent, start, goal)
            if nxt:
                self.x, self.y = nxt
        else:
            # lang thang ngẫu nhiên
            cand = []
            for nx, ny in neighbors4(self.x, self.y):
                if 0 <= nx < len(grid[0]) and 0 <= ny < len(grid) and is_walkable(grid[ny][nx]):
                    cand.append((nx, ny))
            if cand:
                self.x, self.y = random.choice(cand)


# =========================
#  SPAWN / REGEN MAP
# =========================
def random_floor_cell(grid, avoid=set()):
    h = len(grid)
    w = len(grid[0])
    floors = [(x, y) for y in range(h) for x in range(w) if grid[y][x] == T_FLOOR and (x, y) not in avoid]
    return random.choice(floors) if floors else (1, 1)


def spawn_monsters(grid, players, count):
    avoid = {(p.x, p.y) for p in players}
    avoid |= {p.start_pos for p in players}
    monsters = []
    for _ in range(count):
        x, y = random_floor_cell(grid, avoid=avoid)
        monsters.append(Monster(x, y))
        avoid.add((x, y))
    return monsters


def regenerate_map_for_return(players):
    """
    Nhặt kho báu -> map đổi:
    - regen maze mới
    - giữ nguyên vị trí hiện tại của 2 player (ép thành floor)
    - đảm bảo có đường về base cho cả 2
    """
    attempts = 0
    while True:
        attempts += 1
        seed = random.randint(1, 999999)
        # return phase: tạo nhiều loop hơn để rối nhưng không bị cụt quá
        grid = generate_maze(MAP_W, MAP_H, seed=seed, extra_loops=0.14)

        # ép tile base + tile player hiện tại thành đường
        for p in players:
            bx, by = p.start_pos
            grid[by][bx] = T_FLOOR
            grid[p.y][p.x] = T_FLOOR

        # đặt quiz mới
        treasure_dummy = (MAP_W // 2, MAP_H // 2)
        place_quiz_tiles(grid, players[0].start_pos, players[1].start_pos, treasure_dummy, count=14, min_apart=4)

        # check connectivity: mỗi player -> base của mình
        ok = True
        for p in players:
            d, _ = bfs_full(grid, (p.x, p.y))
            if p.start_pos not in d:
                ok = False
                break

        if ok or attempts >= 30:
            return grid


# =========================
#  MAIN
# =========================
def main():
    pygame.init()
    pygame.display.set_caption("Maze Duel (Pygame) — Treasure + Monsters + Auto-Map-Change")
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()

    font_main = load_vietnamese_font(20, bold=True)
    font_small = load_vietnamese_font(18, bold=False)
    font_big = load_vietnamese_font(32, bold=True)

    pygame.key.set_repeat(160, 70)

    # initial map
    game_map = generate_maze(MAP_W, MAP_H, seed=random.randint(1, 999999), extra_loops=0.10)

    map_origin_x = PADDING
    map_origin_y = PADDING

    s1 = (1, 1)
    s2 = (MAP_W - 2, MAP_H - 2)
    game_map[s1[1]][s1[0]] = T_FLOOR
    game_map[s2[1]][s2[0]] = T_FLOOR

    # players
    p1 = Player(s1[0], s1[1], RED, [pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT], "P1 Đỏ")
    p2 = Player(s2[0], s2[1], GREEN, [pygame.K_w, pygame.K_s, pygame.K_a, pygame.K_d], "P2 Xanh")
    players = [p1, p2]

    # treasure
    treasure = pick_treasure_position(game_map, s1, s2)
    treasure_pos = [treasure[0], treasure[1]]

    # quiz
    place_quiz_tiles(game_map, s1, s2, treasure, count=16, min_apart=4)

    # monsters
    monsters = spawn_monsters(game_map, players, MONSTER_COUNT)

    map_changed_after_pick = False
    winner_text = ""

    running = True
    while running:
        now_ms = pygame.time.get_ticks()

        # ===== EVENTS =====
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                dirs = [(0, -1), (0, 1), (-1, 0), (1, 0)]  # U D L R

                if event.key in p1.controls:
                    idx = p1.controls.index(event.key)
                    dx, dy = dirs[idx]
                    p1.move(dx, dy, game_map, p2, screen, font_big, font_main)

                if event.key in p2.controls:
                    idx = p2.controls.index(event.key)
                    dx, dy = dirs[idx]
                    p2.move(dx, dy, game_map, p1, screen, font_big, font_main)

        # ===== LOGIC: treasure pickup =====
        if treasure_pos is not None:
            for p in players:
                if p.x == treasure_pos[0] and p.y == treasure_pos[1]:
                    p.has_treasure = True
                    treasure_pos = None

                    # MAP ĐỔI NGAY KHI NHẶT
                    game_map = regenerate_map_for_return(players)
                    monsters = spawn_monsters(game_map, players, MONSTER_COUNT)
                    map_changed_after_pick = True
                    break

        # ===== LOGIC: monsters move & hit =====
        for m in monsters:
            m.step(game_map, players, now_ms)

            # hit check
            for p in players:
                if (m.x, m.y) == (p.x, p.y):
                    if now_ms - p.last_hit_ms >= HIT_COOLDOWN_MS:
                        p.last_hit_ms = now_ms

                        # nếu đang cầm treasure -> rơi tại chỗ bị hit
                        if p.has_treasure:
                            p.has_treasure = False
                            treasure_pos = [p.x, p.y]  # rơi ra map
                        p.return_to_base()

        # ===== WIN CHECK =====
        if p1.has_treasure and (p1.x, p1.y) == p1.start_pos:
            winner_text = "NGƯỜI CHƠI ĐỎ THẮNG!"
            running = False

        if p2.has_treasure and (p2.x, p2.y) == p2.start_pos:
            winner_text = "NGƯỜI CHƠI XANH THẮNG!"
            running = False

        # ===== DRAW =====
        screen.fill(FLOOR)

        # tiles
        for row in range(MAP_H):
            for col in range(MAP_W):
                tile = game_map[row][col]
                x = map_origin_x + col * TILE_SIZE
                y = map_origin_y + row * TILE_SIZE

                if tile == T_WALL:
                    pygame.draw.rect(screen, WALL, (x, y, TILE_SIZE, TILE_SIZE))
                    pygame.draw.rect(screen, GRID, (x, y, TILE_SIZE, TILE_SIZE), 1)
                else:
                    pygame.draw.rect(screen, FLOOR, (x, y, TILE_SIZE, TILE_SIZE))
                    pygame.draw.rect(screen, GRID, (x, y, TILE_SIZE, TILE_SIZE), 1)

                if tile == T_QUIZ:
                    pygame.draw.rect(screen, PURPLE, (x + 2, y + 2, TILE_SIZE - 4, TILE_SIZE - 4), border_radius=8)
                    txt = font_small.render("?", True, WHITE)
                    screen.blit(txt, (x + TILE_SIZE // 2 - txt.get_width() // 2, y + TILE_SIZE // 2 - txt.get_height() // 2))

        # bases
        b1x, b1y = map_origin_x + p1.start_pos[0] * TILE_SIZE, map_origin_y + p1.start_pos[1] * TILE_SIZE
        pygame.draw.rect(screen, (120, 10, 10), (b1x + 3, b1y + 3, TILE_SIZE - 6, TILE_SIZE - 6), border_radius=8)
        base_txt = font_small.render("BASE", True, WHITE)
        screen.blit(base_txt, (b1x + TILE_SIZE // 2 - base_txt.get_width() // 2, b1y + TILE_SIZE // 2 - base_txt.get_height() // 2))

        b2x, b2y = map_origin_x + p2.start_pos[0] * TILE_SIZE, map_origin_y + p2.start_pos[1] * TILE_SIZE
        pygame.draw.rect(screen, (10, 120, 10), (b2x + 3, b2y + 3, TILE_SIZE - 6, TILE_SIZE - 6), border_radius=8)
        screen.blit(base_txt, (b2x + TILE_SIZE // 2 - base_txt.get_width() // 2, b2y + TILE_SIZE // 2 - base_txt.get_height() // 2))

        # treasure draw (nếu còn nằm trên map)
        if treasure_pos:
            tx = map_origin_x + treasure_pos[0] * TILE_SIZE + TILE_SIZE // 2
            ty = map_origin_y + treasure_pos[1] * TILE_SIZE + TILE_SIZE // 2
            r = max(8, TILE_SIZE // 3)
            pygame.draw.circle(screen, YELLOW, (tx, ty), r)
            if pygame.time.get_ticks() % 500 < 250:
                pygame.draw.circle(screen, WHITE, (tx, ty), r - 5, 2)

        # monsters
        for m in monsters:
            m.draw(screen, map_origin_x, map_origin_y)

        # players
        for p in players:
            p.draw(screen, map_origin_x, map_origin_y)

        # HUD
        hud_y = SCREEN_HEIGHT - HUD_HEIGHT
        pygame.draw.rect(screen, UI_BG, (0, hud_y, SCREEN_WIDTH, HUD_HEIGHT))

        carrier = "-"
        if p1.has_treasure:
            carrier = "ĐỎ"
        elif p2.has_treasure:
            carrier = "XANH"

        if treasure_pos is None and carrier != "-":
            status = f"ĐANG CÓ NGƯỜI CẦM KHO BÁU: {carrier} | Quái cách <= {CHASE_RANGE} ô sẽ đuổi!"
            color = YELLOW
        else:
            status = f"TÌM KHO BÁU | Ô tím = Quiz | Quái cách <= {CHASE_RANGE} ô sẽ đuổi!"
            color = WHITE

        txt = font_main.render(status, True, color)
        screen.blit(txt, (20, hud_y + 16))

        if map_changed_after_pick:
            note = font_small.render("Map đã đổi khi nhặt kho báu!", True, (180, 200, 255))
            screen.blit(note, (20, hud_y + 46))

        pygame.display.flip()
        clock.tick(FPS)

    # ===== END SCREEN =====
    while True:
        screen.fill(BLACK)
        t_win = font_big.render(winner_text, True, YELLOW)
        t_note = font_main.render("Nhấn SPACE để thoát game", True, WHITE)
        screen.blit(t_win, (SCREEN_WIDTH // 2 - t_win.get_width() // 2, SCREEN_HEIGHT // 2 - 60))
        screen.blit(t_note, (SCREEN_WIDTH // 2 - t_note.get_width() // 2, SCREEN_HEIGHT // 2 + 10))
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE):
                pygame.quit()
                sys.exit()


if __name__ == "__main__":
    main()
