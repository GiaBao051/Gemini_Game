
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
HUD_HEIGHT = 90
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
DYN_WALL = (55, 85, 210)     # tường động (nhìn khác một chút)
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
#  QUÁI VẬT
# =========================
MONSTER_COUNT = 4
MONSTER_MOVE_MS = 220
CHASE_RANGE = 10
HIT_COOLDOWN_MS = 900

# =========================
#  CHƯỚNG NGẠI VẬT ĐỘNG (Dùng TÔ MÀU ĐỒ THỊ)
# =========================
DYN_WALL_COUNT = 90         # số ô tường động
DYN_MAX_COLORS = 4          # số màu dùng trong tô màu đồ thị
DYN_PHASE_MS = 850          # ms đổi pha (mỗi pha bật 1 nhóm màu)


# =========================
#  FONT TIẾNG VIỆT
# =========================
def load_vietnamese_font(size: int, bold: bool = False):
    """
    Mẹo chắc chắn 100% tiếng Việt:
    - Tải 'NotoSans-Regular.ttf' hoặc 'Roboto-Regular.ttf'
    - Đặt cùng thư mục file .py
    - Set FONT_TTF_PATH = "NotoSans-Regular.ttf"
    """
    FONT_TTF_PATH = None  # ví dụ: "NotoSans-Regular.ttf"

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
    if goal not in parent:
        return None
    cur = goal
    while parent[cur] is not None and parent[cur] != start:
        cur = parent[cur]
    if parent[cur] == start:
        return cur
    return None


# =========================
#  THUẬT TOÁN TÔ MÀU ĐỒ THỊ (Greedy Coloring)
# =========================
def build_adjacency(cells):
    s = set(cells)
    adj = {c: set() for c in cells}
    for (x, y) in cells:
        for nx, ny in neighbors4(x, y):
            if (nx, ny) in s:
                adj[(x, y)].add((nx, ny))
    return adj


def greedy_graph_coloring(vertices, edges, max_colors=4):
    """
    Greedy graph coloring:
    - Sắp xếp đỉnh theo bậc giảm dần
    - Gán màu nhỏ nhất chưa bị hàng xóm dùng
    """
    order = sorted(vertices, key=lambda v: len(edges.get(v, set())), reverse=True)
    color = {}
    for v in order:
        used = {color[n] for n in edges.get(v, set()) if n in color}
        for c in range(max_colors):
            if c not in used:
                color[v] = c
                break
        if v not in color:
            # fallback nếu cần nhiều hơn max_colors
            c = 0
            while c in used:
                c += 1
            color[v] = c
    return color


def select_dynamic_walls(base_grid, count, avoid=set(), min_dist=6):
    """
    Chọn các ô sàn để làm tường động (tránh base, tránh kho báu, tránh quiz).
    """
    h = len(base_grid)
    w = len(base_grid[0])

    def manhattan(a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    floors = []
    for y in range(h):
        for x in range(w):
            if base_grid[y][x] == T_FLOOR and (x, y) not in avoid:
                floors.append((x, y))

    random.shuffle(floors)
    chosen = []
    for p in floors:
        if len(chosen) >= count:
            break
        ok = True
        for a in avoid:
            if manhattan(p, a) < min_dist:
                ok = False
                break
        if not ok:
            continue
        # tránh chọn các ô quá sát nhau để dễ quan sát (không bắt buộc)
        for c in chosen:
            if manhattan(p, c) < 2:
                ok = False
                break
        if ok:
            chosen.append(p)

    return chosen


def apply_dynamic_walls(game_map, base_grid, dyn_cells, dyn_color, phase, protected):
    """
    Áp chướng ngại vật động lên game_map dựa vào phase.
    protected: set các ô bắt buộc phải đi được (vị trí player, kho báu rơi,...)
    """
    for (x, y) in dyn_cells:
        if (x, y) in protected:
            game_map[y][x] = T_FLOOR
            continue

        # dyn_cells đều được chọn từ T_FLOOR nên base_grid[y][x] là floor.
        c = dyn_color.get((x, y), 0)
        if c == phase:
            game_map[y][x] = T_WALL
        else:
            game_map[y][x] = T_FLOOR


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

    # add loops
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
    Popup trắc nghiệm: box tự tính chiều cao để không đè option 4.
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

    def move(self, dx, dy, game_map, base_grid, opponent, screen, font_title, font_text):
        nx, ny = self.x + dx, self.y + dy
        if ny < 0 or ny >= len(game_map) or nx < 0 or nx >= len(game_map[0]):
            return
        if not is_walkable(game_map[ny][nx]):
            return

        # quiz
        if game_map[ny][nx] == T_QUIZ:
            ok = show_question_popup(screen, font_title, font_text)
            if not ok:
                return
            # xóa quiz trên cả base_grid và game_map
            base_grid[ny][nx] = T_FLOOR
            game_map[ny][nx] = T_FLOOR

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

    def step(self, game_map, players, now_ms):
        if now_ms < self.next_move_ms:
            return

        self.next_move_ms = now_ms + MONSTER_MOVE_MS
        start = (self.x, self.y)
        dist, parent = bfs_full(game_map, start)

        # chọn target gần nhất trong CHASE_RANGE
        targets = []
        for p in players:
            pos = (p.x, p.y)
            if pos in dist and dist[pos] <= CHASE_RANGE:
                targets.append((dist[pos], pos))
        targets.sort(key=lambda t: t[0])

        if targets:
            goal = targets[0][1]
            nxt = reconstruct_next_step(parent, start, goal)
            if nxt:
                self.x, self.y = nxt
        else:
            cand = []
            for nx, ny in neighbors4(self.x, self.y):
                if 0 <= nx < len(game_map[0]) and 0 <= ny < len(game_map) and is_walkable(game_map[ny][nx]):
                    cand.append((nx, ny))
            if cand:
                self.x, self.y = random.choice(cand)


# =========================
#  SPAWN / REGEN MAP
# =========================
def random_floor_cell(base_grid, avoid=set()):
    h = len(base_grid)
    w = len(base_grid[0])
    floors = [(x, y) for y in range(h) for x in range(w) if base_grid[y][x] == T_FLOOR and (x, y) not in avoid]
    return random.choice(floors) if floors else (1, 1)


def spawn_monsters(base_grid, players, count):
    avoid = {(p.x, p.y) for p in players}
    avoid |= {p.start_pos for p in players}
    monsters = []
    for _ in range(count):
        x, y = random_floor_cell(base_grid, avoid=avoid)
        monsters.append(Monster(x, y))
        avoid.add((x, y))
    return monsters


def build_dynamic_system(base_grid, players, treasure_pos):
    """
    Tạo hệ tường động:
    - chọn dyn_cells
    - build graph adjacency
    - tô màu đồ thị (greedy)
    """
    avoid = {p.start_pos for p in players} | {(p.x, p.y) for p in players}
    if treasure_pos:
        avoid.add(tuple(treasure_pos))

    # tránh đặt dyn lên quiz
    for y in range(len(base_grid)):
        for x in range(len(base_grid[0])):
            if base_grid[y][x] == T_QUIZ:
                avoid.add((x, y))

    dyn_cells = select_dynamic_walls(base_grid, DYN_WALL_COUNT, avoid=avoid, min_dist=6)
    adj = build_adjacency(dyn_cells)
    dyn_color = greedy_graph_coloring(dyn_cells, adj, max_colors=DYN_MAX_COLORS)
    k = max(dyn_color.values()) + 1 if dyn_color else 1
    return dyn_cells, dyn_color, k


def regenerate_base_map(players):
    """
    Nhặt kho báu -> map đổi:
    - regen base_grid mới
    - giữ nguyên vị trí player (ép thành floor)
    - có đường từ player về base của chính mình
    """
    attempts = 0
    while True:
        attempts += 1
        seed = random.randint(1, 999999)
        base_grid = generate_maze(MAP_W, MAP_H, seed=seed, extra_loops=0.14)

        for p in players:
            bx, by = p.start_pos
            base_grid[by][bx] = T_FLOOR
            base_grid[p.y][p.x] = T_FLOOR

        # đặt quiz mới (không cần treasure nữa vì đang return phase)
        dummy = (MAP_W // 2, MAP_H // 2)
        place_quiz_tiles(base_grid, players[0].start_pos, players[1].start_pos, dummy, count=14, min_apart=4)

        ok = True
        for p in players:
            d, _ = bfs_full(base_grid, (p.x, p.y))
            if p.start_pos not in d:
                ok = False
                break

        if ok or attempts >= 30:
            return base_grid


# =========================
#  MAIN
# =========================
def main():
    pygame.init()
    pygame.display.set_caption("Maze Duel — Dynamic Obstacles (Graph Coloring) + Monsters + Treasure")
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()

    font_main = load_vietnamese_font(20, bold=True)
    font_small = load_vietnamese_font(18, bold=False)
    font_big = load_vietnamese_font(32, bold=True)

    pygame.key.set_repeat(160, 70)

    # --- init base map ---
    base_grid = generate_maze(MAP_W, MAP_H, seed=random.randint(1, 999999), extra_loops=0.10)

    map_origin_x = PADDING
    map_origin_y = PADDING

    s1 = (1, 1)
    s2 = (MAP_W - 2, MAP_H - 2)
    base_grid[s1[1]][s1[0]] = T_FLOOR
    base_grid[s2[1]][s2[0]] = T_FLOOR

    # players
    p1 = Player(s1[0], s1[1], RED, [pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT], "P1 Đỏ")
    p2 = Player(s2[0], s2[1], GREEN, [pygame.K_w, pygame.K_s, pygame.K_a, pygame.K_d], "P2 Xanh")
    players = [p1, p2]

    # treasure placement
    treasure = pick_treasure_position(base_grid, s1, s2)
    treasure_pos = [treasure[0], treasure[1]]

    # quiz placement
    place_quiz_tiles(base_grid, s1, s2, treasure, count=16, min_apart=4)

    # game_map starts as copy of base_grid
    game_map = [row[:] for row in base_grid]

    # dynamic obstacle system (graph coloring)
    dyn_cells, dyn_color, dyn_k = build_dynamic_system(base_grid, players, treasure_pos)
    dyn_phase = 0
    next_phase_ms = pygame.time.get_ticks() + DYN_PHASE_MS

    # monsters
    monsters = spawn_monsters(base_grid, players, MONSTER_COUNT)

    map_changed_after_pick = False
    winner_text = ""
    running = True

    while running:
        now_ms = pygame.time.get_ticks()

        # --- đổi pha chướng ngại vật động ---
        if now_ms >= next_phase_ms and dyn_k > 0:
            dyn_phase = (dyn_phase + 1) % dyn_k
            next_phase_ms = now_ms + DYN_PHASE_MS

        # bảo vệ các ô quan trọng để không bị "đóng tường" đè lên
        protected = {(p1.x, p1.y), (p2.x, p2.y)}
        if treasure_pos:
            protected.add(tuple(treasure_pos))
        for m in monsters:
            protected.add((m.x, m.y))

        # apply dyn overlay lên game_map (chỉ cập nhật dyn_cells)
        # lưu ý: game_map trước đó có thể bị thay đổi quiz -> đã sửa cả base_grid nên ok.
        apply_dynamic_walls(game_map, base_grid, dyn_cells, dyn_color, dyn_phase, protected)

        # --- EVENTS ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                dirs = [(0, -1), (0, 1), (-1, 0), (1, 0)]  # U D L R

                if event.key in p1.controls:
                    idx = p1.controls.index(event.key)
                    dx, dy = dirs[idx]
                    p1.move(dx, dy, game_map, base_grid, p2, screen, font_big, font_main)

                if event.key in p2.controls:
                    idx = p2.controls.index(event.key)
                    dx, dy = dirs[idx]
                    p2.move(dx, dy, game_map, base_grid, p1, screen, font_big, font_main)

        # --- LOGIC: treasure pickup ---
        if treasure_pos is not None:
            for p in players:
                if p.x == treasure_pos[0] and p.y == treasure_pos[1]:
                    p.has_treasure = True
                    treasure_pos = None

                    # MAP ĐỔI NGAY KHI NHẶT KHO BÁU
                    base_grid = regenerate_base_map(players)
                    game_map = [row[:] for row in base_grid]

                    # rebuild dynamic obstacles (graph coloring) cho map mới
                    dyn_cells, dyn_color, dyn_k = build_dynamic_system(base_grid, players, treasure_pos)
                    dyn_phase = 0
                    next_phase_ms = now_ms + DYN_PHASE_MS

                    # respawn monsters
                    monsters = spawn_monsters(base_grid, players, MONSTER_COUNT)

                    map_changed_after_pick = True
                    break

        # --- LOGIC: monsters ---
        for m in monsters:
            m.step(game_map, players, now_ms)

            for p in players:
                if (m.x, m.y) == (p.x, p.y):
                    if now_ms - p.last_hit_ms >= HIT_COOLDOWN_MS:
                        p.last_hit_ms = now_ms
                        if p.has_treasure:
                            p.has_treasure = False
                            treasure_pos = [p.x, p.y]  # rơi kho báu
                        p.return_to_base()

        # --- WIN CHECK ---
        if p1.has_treasure and (p1.x, p1.y) == p1.start_pos:
            winner_text = "NGƯỜI CHƠI ĐỎ THẮNG!"
            running = False

        if p2.has_treasure and (p2.x, p2.y) == p2.start_pos:
            winner_text = "NGƯỜI CHƠI XANH THẮNG!"
            running = False

        # --- DRAW ---
        screen.fill(FLOOR)

        dyn_set = set(dyn_cells)

        for row in range(MAP_H):
            for col in range(MAP_W):
                tile = game_map[row][col]
                x = map_origin_x + col * TILE_SIZE
                y = map_origin_y + row * TILE_SIZE

                if tile == T_WALL:
                    # nếu là tường động đang bật, tô màu khác
                    if (col, row) in dyn_set:
                        pygame.draw.rect(screen, DYN_WALL, (x, y, TILE_SIZE, TILE_SIZE))
                    else:
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

        # treasure
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

        line1 = f"Kho báu: {carrier} | Quái đuổi khi <= {CHASE_RANGE} ô | Tường động (Graph Coloring): pha {dyn_phase+1}/{max(1,dyn_k)}"
        txt1 = font_main.render(line1, True, WHITE)
        screen.blit(txt1, (20, hud_y + 14))

        if map_changed_after_pick:
            line2 = "Map tự đổi khi nhặt kho báu ✅ | Tường động đổi theo nhóm màu (không bật tường kề nhau)."
            txt2 = font_small.render(line2, True, (180, 200, 255))
            screen.blit(txt2, (20, hud_y + 46))
        else:
            line2 = "Ô tím = Trắc nghiệm | Đúng mới đi tiếp. Tường động đổi liên tục nhưng an toàn quanh người chơi."
            txt2 = font_small.render(line2, True, (180, 200, 255))
            screen.blit(txt2, (20, hud_y + 46))

        pygame.display.flip()
        clock.tick(FPS)

    # --- END SCREEN ---
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
