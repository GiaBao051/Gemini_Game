from __future__ import annotations

import asyncio
import json
import random
import time
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from maze import generate_maze, mutate_maze_for_return, T_WALL, T_FLOOR, T_QUIZ
from algorithms.csp_placement import solve_csp_placement, bfs_dist, INF
from algorithms.coloring import build_quiz_graph, greedy_coloring
from algorithms.hungarian import hungarian, pad_to_square
from questions import QuestionBank, CATEGORIES

Vec = Tuple[int, int]

DIRS: Dict[str, Vec] = {
    "U": (0, -1),
    "D": (0, 1),
    "L": (-1, 0),
    "R": (1, 0),
}

@dataclass
class Player:
    id: str
    name: str
    pos: Vec
    start: Vec
    has_treasure: bool = False
    locked: bool = False
    stun_until: float = 0.0
    active_qid: Optional[str] = None


class GameRoom:
    """Authoritative 2-player room."""

    def __init__(self, room_id: str, tick_hz: int = 15):
        self.room_id = room_id
        self.tick_hz = tick_hz

        self.players: Dict[str, Player] = {}
        self.sockets: Dict[str, Any] = {}
        self.input_q: Dict[str, asyncio.Queue] = {}

        self.phase: str = "SEARCH"   # SEARCH -> RETURN
        self.carrier_id: Optional[str] = None

        self.w = 31
        self.h = 21
        self.seed = random.randint(1, 10**9)

        # --- Build a playable map with CSP placement (retry if needed) ---
        self.grid = None
        self.start1 = (1, 1)
        self.start2 = (self.w - 2, self.h - 2)

        self.treasure_pos: Vec = (0, 0)
        self.quiz_positions: List[Vec] = []
        self.quiz_category_by_pos: Dict[Vec, str] = {}
        self.quiz_target_diff: Dict[Vec, int] = {}
        self.quiz_tile_data: Dict[Vec, Dict[str, Any]] = {}

        self.qbank = QuestionBank(seed=self.seed)

        self._task: Optional[asyncio.Task] = None
        self._tick: int = 0
        self._ended: bool = False

        self._init_map_with_algorithms()

    def _init_map_with_algorithms(self) -> None:
        tries = 12
        quiz_count = 12

        last_err = None
        for _ in range(tries):
            try:
                self.grid = generate_maze(self.w, self.h, seed=random.randint(1, 10**9))
                floor_cells = [
                    (x, y)
                    for y in range(1, self.h - 1)
                    for x in range(1, self.w - 1)
                    if self.grid[y][x] == T_FLOOR
                ]

                placement = solve_csp_placement(
                    grid=self.grid,
                    floor_cells=floor_cells,
                    start1=self.start1,
                    start2=self.start2,
                    quiz_count=quiz_count,
                    k_apart=6,
                    balance_tol=6,
                    seed=random.randint(1, 10**9),
                )
                if not placement:
                    last_err = "CSP returned None"
                    continue

                self.treasure_pos = placement["T"]
                self.quiz_positions = [placement[f"Q{i}"] for i in range(quiz_count)]

                # mark quiz tiles
                for (x, y) in self.quiz_positions:
                    self.grid[y][x] = T_QUIZ

                # 1) Graph coloring => category assignment
                adj = build_quiz_graph(self.grid, self.quiz_positions, radius=7)
                colors = greedy_coloring(adj)  # node_index -> color_int
                self.quiz_category_by_pos = {}
                for i, pos in enumerate(self.quiz_positions):
                    self.quiz_category_by_pos[pos] = CATEGORIES[colors[i] % len(CATEGORIES)]

                # 2) Target difficulty by distance to treasure (near treasure -> harder)
                dist_to_t = bfs_dist(self.grid, self.treasure_pos)
                maxd = 1
                for (x, y) in floor_cells:
                    d = dist_to_t[y][x]
                    if d < INF:
                        maxd = max(maxd, d)

                def target_difficulty(pos: Vec) -> int:
                    d = dist_to_t[pos[1]][pos[0]]
                    # ratio high when close to treasure
                    ratio = 1.0 - (d / maxd) if maxd else 0.0
                    t = 1 + int(round(ratio * 4))  # 1..5
                    return max(1, min(5, t))

                self.quiz_target_diff = {pos: target_difficulty(pos) for pos in self.quiz_positions}

                # 3) Assignment (Hungarian) within each category to match difficulty
                self.quiz_tile_data = {}
                for cat in CATEGORIES:
                    tiles = [pos for pos in self.quiz_positions if self.quiz_category_by_pos[pos] == cat]
                    if not tiles:
                        continue

                    qs = self.qbank.sample_questions(cat, count=len(tiles))

                    cost: List[List[int]] = []
                    for pos in tiles:
                        tdiff = self.quiz_target_diff[pos]
                        row = [abs(int(q["difficulty"]) - tdiff) for q in qs]
                        cost.append(row)

                    sq = pad_to_square(cost, pad_value=10**6)
                    _, assign = hungarian(sq)

                    for i, pos in enumerate(tiles):
                        j = assign[i]
                        if j >= len(qs):
                            # padded assignment, fallback best
                            j = min(range(len(qs)), key=lambda jj: cost[i][jj])
                        picked = qs[j]
                        reg = self.qbank.register_question(picked)
                        self.quiz_tile_data[pos] = reg

                # success
                return

            except Exception as e:
                last_err = str(e)

        raise RuntimeError(f"Map init failed after {tries} tries: {last_err}")

    # ----------------- Player / socket plumbing -----------------

    def add_player(self, player_id: str, name: str, ws: Any) -> None:
        if player_id in self.players:
            return
        start = self.start1 if len(self.players) == 0 else self.start2
        self.players[player_id] = Player(id=player_id, name=name, pos=start, start=start)
        self.sockets[player_id] = ws
        self.input_q[player_id] = asyncio.Queue()

        # Start loop when 2 players present
        if len(self.players) == 2 and self._task is None:
            self._task = asyncio.create_task(self._loop())

    async def send_start(self, player_id: str) -> None:
        payload = {
            "type": "start",
            "player_id": player_id,
            "room_id": self.room_id,
            "map": {
                "w": self.w,
                "h": self.h,
                "grid": self.grid,
                "starts": {pid: list(p.start) for pid, p in self.players.items()},
                "treasure": list(self.treasure_pos),
                "quiz": [list(p) for p in self.quiz_positions],
            },
            "state": self._state_dict(),
        }
        await self._send(player_id, payload)

    async def handle_client_msg(self, player_id: str, msg: dict) -> None:
        t = msg.get("type")
        if t in ("input", "answer"):
            q = self.input_q.get(player_id)
            if q:
                await q.put((t, msg))
        else:
            await self._send(player_id, {"type": "error", "message": f"Unknown type: {t}"})

    async def broadcast(self, payload: dict) -> None:
        for pid in list(self.sockets.keys()):
            try:
                await self._send(pid, payload)
            except Exception:
                pass

    async def _send(self, player_id: str, payload: dict) -> None:
        ws = self.sockets.get(player_id)
        if not ws:
            return
        await ws.send_text(json.dumps(payload))

    # ----------------- Game loop -----------------

    async def _loop(self) -> None:
        dt = 1.0 / float(self.tick_hz)
        try:
            while not self._ended:
                start_t = time.time()
                self._tick += 1

                # Inputs
                for pid in list(self.players.keys()):
                    await self._drain_inputs(pid)

                # Resolve interactions
                await self._resolve()

                # Broadcast state
                await self.broadcast({
                    "type": "state",
                    "t": self._tick,
                    "phase": self.phase,
                    "players": {pid: self._player_view(p) for pid, p in self.players.items()},
                    "treasure": list(self.treasure_pos),
                    "carrier": self.carrier_id,
                })

                elapsed = time.time() - start_t
                await asyncio.sleep(max(0.0, dt - elapsed))
        except asyncio.CancelledError:
            return
        except Exception as e:
            # Fail safe: notify and end
            await self.broadcast({"type": "error", "message": f"Room crashed: {type(e).__name__}"})
            self._ended = True

    async def _drain_inputs(self, pid: str) -> None:
        p = self.players.get(pid)
        if not p:
            return

        now = time.time()

        # Drain up to N actions per tick to avoid abuse
        q = self.input_q.get(pid)
        if not q:
            return

        for _ in range(6):
            if q.empty():
                break
            kind, msg = await q.get()

            if kind == "input":
                if p.locked or now < p.stun_until:
                    continue
                d = str(msg.get("dir") or "").upper()
                if d in DIRS:
                    self._try_move(p, DIRS[d])

            elif kind == "answer":
                await self._handle_answer(p, msg)

    def _try_move(self, p: Player, dxy: Vec) -> None:
        x, y = p.pos
        dx, dy = dxy
        nx, ny = x + dx, y + dy

        if not (0 <= nx < self.w and 0 <= ny < self.h):
            return
        if self.grid[ny][nx] == T_WALL:
            return

        p.pos = (nx, ny)

        # Quiz trigger only in SEARCH to avoid "hard lock" on return path
        if self.phase == "SEARCH" and self.grid[ny][nx] == T_QUIZ and not p.locked:
            p.locked = True
            asyncio.create_task(self._ask_question_for_tile(p, (nx, ny)))

    async def _ask_question_for_tile(self, p: Player, tile_pos: Vec) -> None:
        q = self.quiz_tile_data.get(tile_pos)
        if not q:
            q = self.qbank.register_question({
                "category": "logic",
                "difficulty": 1,
                "prompt": "1+1=?",
                "choices": ["1", "2", "3", "4"],
                "answer_index": 1,
            })
            self.quiz_tile_data[tile_pos] = q

        p.active_qid = q["id"]
        await self._send(p.id, {
            "type": "question",
            "qid": q["id"],
            "prompt": q["prompt"],
            "choices": q["choices"],
            "timeout_ms": q["timeout_ms"],
            "meta": {"category": q.get("category"), "difficulty": q.get("difficulty")},
        })

        # timeout
        await asyncio.sleep(q["timeout_ms"] / 1000.0)
        if p.locked and p.active_qid == q["id"]:
            p.locked = False
            p.active_qid = None
            p.stun_until = time.time() + 2.0

    async def _handle_answer(self, p: Player, msg: dict) -> None:
        qid = msg.get("qid")
        choice = msg.get("choice")

        if not p.locked or not p.active_qid or qid != p.active_qid:
            return

        ok = self.qbank.check_answer(qid, choice)
        p.locked = False
        p.active_qid = None
        if not ok:
            p.stun_until = time.time() + 2.0

    async def _resolve(self) -> None:
        # Treasure pick (only if not currently carried)
        if self.carrier_id is None:
            for pid, p in self.players.items():
                if p.pos == self.treasure_pos:
                    self.carrier_id = pid
                    p.has_treasure = True
                    self.phase = "RETURN"
                    # mutate maze so carrier can return
                    self.grid = mutate_maze_for_return(self.grid, from_pos=p.pos, to_pos=p.start)
                    await self.broadcast({"type": "event", "name": "TREASURE_PICKED", "by": pid})
                    break

        # Steal on same-tile contact
        if self.carrier_id is not None:
            carrier = self.players.get(self.carrier_id)
            if carrier:
                for pid, p in self.players.items():
                    if pid == self.carrier_id:
                        continue
                    if p.pos == carrier.pos:
                        carrier.has_treasure = False
                        p.has_treasure = True
                        self.carrier_id = pid
                        await self.broadcast({"type": "event", "name": "TREASURE_STOLEN", "by": pid})
                        break

                # Win if carrier returns to their start
                carrier = self.players.get(self.carrier_id)
                if carrier and carrier.pos == carrier.start:
                    await self.broadcast({"type": "end", "winner": carrier.id})
                    self._ended = True
                    if self._task:
                        self._task.cancel()

    def _player_view(self, p: Player) -> dict:
        return {
            "id": p.id,
            "name": p.name,
            "pos": list(p.pos),
            "has_treasure": p.has_treasure,
            "locked": p.locked,
            "stun_ms": max(0, int((p.stun_until - time.time()) * 1000)),
        }

    def _state_dict(self) -> dict:
        return {
            "phase": self.phase,
            "carrier": self.carrier_id,
            "players": {pid: self._player_view(p) for pid, p in self.players.items()},
            "treasure": list(self.treasure_pos),
        }


class RoomManager:
    """Very small matchmaker: 1 waiting room, rooms end on disconnect."""

    def __init__(self):
        self.waiting: Optional[GameRoom] = None
        self.player_to_room: Dict[str, GameRoom] = {}

    async def join_or_create(self, ws: Any, player_id: str, name: str) -> GameRoom:
        if self.waiting is None or len(self.waiting.players) >= 2:
            self.waiting = GameRoom(room_id=f"r-{uuid.uuid4().hex[:6]}")

        room = self.waiting
        room.add_player(player_id=player_id, name=name, ws=ws)
        self.player_to_room[player_id] = room

        if len(room.players) == 2:
            self.waiting = None

        return room

    async def disconnect(self, player_id: str) -> None:
        room = self.player_to_room.pop(player_id, None)
        if not room:
            return
        # End match on disconnect
        try:
            await room.broadcast({"type": "end", "winner": "disconnect"})
        except Exception:
            pass
        room._ended = True
        if room._task:
            room._task.cancel()
