# Maze Duel – BO3 Match

> Đồ án môn **Trí Tuệ Nhân Tạo** – Game mê cung 2D đa người chơi, kết hợp nhiều thuật toán AI trong một file HTML/JavaScript duy nhất.

---

## Mục lục

1. [Giới thiệu dự án](#1-giới-thiệu-dự-án)
2. [Mục tiêu đồ án](#2-mục-tiêu-đồ-án)
3. [Tổng quan gameplay](#3-tổng-quan-gameplay)
4. [Tính năng chính](#4-tính-năng-chính)
5. [Công nghệ sử dụng](#5-công-nghệ-sử-dụng)
6. [Kiến trúc hệ thống](#6-kiến-trúc-hệ-thống)
7. [Cấu trúc thư mục](#7-cấu-trúc-thư-mục)
8. [Hướng dẫn chạy dự án](#8-hướng-dẫn-chạy-dự-án)
9. [Hướng dẫn sử dụng](#9-hướng-dẫn-sử-dụng)
10. [Điều khiển trong game](#10-điều-khiển-trong-game)
11. [Luật chơi chi tiết](#11-luật-chơi-chi-tiết)
12. [**Các thuật toán AI – Trọng tâm đồ án**](#12-các-thuật-toán-ai--trọng-tâm-đồ-án)
13. [Hệ thống AI của CPU](#13-hệ-thống-ai-của-cpu)
14. [Giao thức mạng MQTT và đồng bộ trạng thái](#14-giao-thức-mạng-mqtt-và-đồng-bộ-trạng-thái)
15. [Các cấu hình quan trọng](#15-các-cấu-hình-quan-trọng)
16. [Debug và đánh giá chất lượng bản đồ](#16-debug-và-đánh-giá-chất-lượng-bản-đồ)
17. [Ưu điểm và hạn chế](#17-ưu-điểm-và-hạn-chế)
18. [Hướng phát triển](#18-hướng-phát-triển)

---

## 1. Giới thiệu dự án

**Maze Duel** là game mê cung 2D viết bằng một file `HTML/CSS/JavaScript` duy nhất, hỗ trợ hai chế độ chơi:

- **Offline** – chơi với CPU ở 3 mức độ khó (Dễ / Thường / Khó).
- **Online** – nhiều người chơi trong cùng phòng qua giao thức MQTT.

Mỗi trận đấu diễn ra theo thể thức **BO3** (Best of 3). Người chơi cần tìm kho báu trong mê cung, mang về đúng base của mình để giành chiến thắng ván đấu.

Điểm nổi bật:

- Mê cung sinh ngẫu nhiên theo **seed**, có thể tái tạo lại hoàn toàn.
- Độ khó **tăng dần** theo từng round.
- Có quiz tile, trap, quái vật, cơ chế cướp kho báu.
- Ứng dụng nhiều thuật toán AI: **DFS, BFS, A\*, Dijkstra, CSP, Graph Coloring, Tarjan, Influence Map**.
- Có debug panel đầy đủ và báo cáo chất lượng bản đồ từ console.

---

## 2. Mục tiêu đồ án

- Xây dựng trò chơi mê cung có tính tương tác cao, kết hợp gameplay và AI.
- Minh họa trực quan các chủ đề TTNT:
  - Sinh mê cung (DFS procedural generation).
  - Tìm đường (BFS, A\*, Dijkstra).
  - Bài toán thỏa mãn ràng buộc (CSP – Constraint Satisfaction Problem).
  - Tô màu đồ thị (Graph Coloring).
  - Phân tích đồ thị (Tarjan articulation point, bridge detection).
  - Bản đồ ảnh hưởng (Influence Map / Danger Map).
- Tạo sản phẩm có thể trình bày như đồ án môn học hoàn chỉnh.

---

## 3. Tổng quan gameplay

1. Người chơi xuất hiện tại base của mình (4 góc bản đồ).
2. Kho báu được đặt ở vị trí hợp lệ do CSP chọn.
3. Người chơi di chuyển để tìm và nhặt kho báu.
4. Khi đã có kho báu, mục tiêu là mang về đúng base.
5. Đối thủ có thể cướp kho báu khi chạm vào người đang giữ.
6. Quái vật và trap tạo thêm áp lực.
7. Người đầu tiên đưa kho báu về base thắng ván. Ai thắng 2 trong 3 ván thắng trận.

---

## 4. Tính năng chính

### 4.1 Chế độ chơi

- Offline với CPU (dễ / thường / khó).
- Online tối đa 4 người (cấu hình `MAX_PLAYERS`), phòng chơi dùng mã 4 ký tự.

### 4.2 Hệ thống mê cung

- Sinh bằng **DFS carve** trên lưới ô lẻ, đảm bảo tất cả ô đều kết nối.
- Thêm bước mở loop và giảm dead-end.
- Hậu xử lý nối các vùng rời rạc (flood-fill + corridor carving).
- Độ khó theo round: round cao hơn → mê cung chặt hơn, ít vòng lặp hơn.

### 4.3 Hệ thống kho báu

- Đặt vị trí bằng **CSP** đảm bảo fairness cho tất cả người chơi.
- Hỗ trợ cơ chế cướp kho báu giữa các người chơi.
- Khi kho báu được nhặt, bản đồ có thể tái sinh (regen map) để tạo biến động.

### 4.4 Hệ thống quiz

- Quiz tile phân tán đều theo **Graph Coloring** (mỗi vùng màu đóng góp quiz).
- Trả lời sai phải thử lại; trả lời đúng mới xóa ô quiz.
- CPU mô phỏng thời gian "suy nghĩ" thay vì hiện modal.

### 4.5 Hệ thống trap

- Đặt bẫy bằng phím `Space` (tối đa `TRAP_LIMIT` bẫy cùng lúc).
- Bẫy có TTL (`TRAP_TTL` ms) và không ảnh hưởng người đặt.
- Dẫm phải bẫy khi đang giữ kho báu → kho báu rơi tại chỗ.

### 4.6 Hệ thống quái vật

- Số lượng quái tăng theo round.
- Spawn vị trí phân tán bằng **Graph Coloring** (mỗi quái thuộc nhóm màu khác nhau).
- Hành vi: tuần tra hoặc truy đuổi khi phát hiện người chơi trong bán kính.
- Không đi xuyên tường; chạm quái → người chơi trở về base.
- Hệ thống gán quái-mục-tiêu dùng **Greedy Heuristic Assignment** (v3).

### 4.7 Debug và đánh giá

- Debug panel chi tiết (Tab).
- Console commands: `mapQualityReport()`, `aiDecisionReport()`, `tacticalSearchReport()`, `monsterAssignmentReport()`.

---

## 5. Công nghệ sử dụng

| Thành phần | Công nghệ |
|---|---|
| Giao diện và game engine | HTML5, CSS3, JavaScript (vanilla) |
| Render 2D | HTML5 Canvas API |
| Multiplayer transport | MQTT over WebSocket (`mqtt.js`) |
| MQTT Broker | `wss://broker.emqx.io:8084/mqtt` |
| Build system | Không có – single-file deployment |

---

## 6. Kiến trúc hệ thống

### 6.1 Chế độ offline

Chạy hoàn toàn trong trình duyệt. Game loop, AI, render, va chạm đều xử lý trên client.

### 6.2 Chế độ online – Host Authoritative

```
[Client 1 – Host]                [Client 2]           [Client N]
  Game logic chính         →  Nhận snapshot từ host
  Nhận MOVE từ clients     ←  Gửi MOVE input
  Broadcast UPDATE/MONS        Render từ snapshot
```

- Host xử lý toàn bộ logic game, AI quái, va chạm, CSP.
- Clients chỉ gửi input (`MOVE`, `TRAP_REQUEST`), nhận và render snapshot.
- Snapshot gồm: `tickId`, `seq`, `serverTs`, players, monsters, treasure, traps, events.
- Client bỏ qua snapshot cũ hơn snapshot đã nhận (guard 3-cấp: `tickId → seq → serverTs`).

---

## 7. Cấu trúc thư mục

```text
Game_Gemini/
├── claudegame.html   # Toàn bộ giao diện, AI, network, thuật toán
└── README.md         # Tài liệu này
```

---

## 8. Hướng dẫn chạy dự án

### Cách 1 – Mở trực tiếp

Mở file `claudegame.html` bằng trình duyệt (Chrome / Edge khuyến nghị).

### Cách 2 – Local server (khuyến nghị)

```powershell
cd E:\Learn\Ky4_25_26\TTNT\Game_Gemini
python -m http.server 5500
```

Truy cập: `http://127.0.0.1:5500/claudegame.html`

---

## 9. Hướng dẫn sử dụng

### Chơi offline

1. Nhập tên người chơi.
2. Nhấn **Bắt đầu** trong phần chơi với máy.
3. Chọn độ khó CPU: Dễ / Thường / Khó.
4. Xác nhận để vào game.

### Chơi online

1. Đợi trạng thái MQTT kết nối thành công.
2. Một người **tạo phòng** để lấy mã phòng 4 ký tự.
3. Người chơi khác **nhập mã phòng** để tham gia.
4. Host nhấn **Bắt đầu trận** khi đủ người.

---

## 10. Điều khiển trong game

| Phím | Tác dụng |
|---|---|
| `W A S D` hoặc `↑ ↓ ← →` | Di chuyển |
| `Space` | Đặt bẫy |
| `Tab` | Bật/tắt debug panel |
| `G` | Bật/tắt Graph Coloring overlay |
| `I` | Bật/tắt Influence Map overlay |
| `C` | Bật/tắt Choke Point overlay |

Trên thiết bị cảm ứng: D-pad ảo xuất hiện ở góc màn hình.

---

## 11. Luật chơi chi tiết

| Tình huống | Kết quả |
|---|---|
| Đi vào ô kho báu | Nhặt kho báu |
| Đi vào ô kho báu đang mang kho báu | Cướp kho báu từ đối thủ |
| Mang kho báu về đúng base | **Thắng ván** |
| Dẫm phải bẫy khi mang kho báu | Kho báu rơi tại ô đó |
| Chạm vào quái vật | Người chơi trở về base |
| Đi vào quiz tile | Phải trả lời đúng mới qua |
| Thắng 2/3 ván | **Thắng trận** |

---

## 12. Các thuật toán AI – Trọng tâm đồ án

Đây là phần cốt lõi của đồ án. Mỗi thuật toán được tích hợp vào gameplay với vai trò rõ ràng.

---

### 12.1 Sinh mê cung – DFS Randomized Maze Carving

**Vị trí trong code:** `generateMaze()` (~dòng 660)

**Nguyên lý:**

Mê cung được xây dựng trên lưới ô vuông kích thước `41×25`. Ban đầu toàn bộ ô là tường (`T_WALL`). Thuật toán **DFS đệ quy** (Recursive Backtracking) chỉ đi qua các ô có tọa độ **lẻ** (1, 3, 5, ...) để tạo cấu trúc mê cung chuẩn.

**Các bước:**

```
1. Khởi tạo: toàn bộ grid là T_WALL
2. DFS từ ô (1,1):
   - Đánh dấu ô hiện tại = T_FLOOR
   - Shuffle ngẫu nhiên 4 hướng di chuyển (dùng seeded RNG)
   - Với mỗi hướng: nếu ô đích chưa thăm → đục tường giữa → đệ quy vào ô đích
3. Mở thêm vòng lặp (loop):
   - Tính tỉ lệ LOOP_ADD_RATIO (0.12 mặc định, giảm theo round)
   - Duyệt các ô tường ngẫu nhiên, nếu có ≥2 hàng xóm là floor → mở ô đó
   → Giúp có nhiều đường đi hơn, giảm dead-end
4. Xử lý dead-end (DEAD_END_PASSES lần):
   - Mỗi ô floor chỉ có 1 hàng xóm floor → đây là dead-end
   - Đục thêm 1 tường ngẫu nhiên xung quanh để mở thêm đường thoát
5. Phục hồi tường đầu maze (điều chỉnh độ khó theo round):
   - Tăng wallRestoreChance (0.55 → 0.82) theo round
   - Đặt lại tường tại một số vị trí, đảm bảo không cô lập ô nào
6. Đảm bảo liên thông (Flood-fill + Corridor Carving):
   - BFS từ base[0] để tìm thành phần liên thông chính
   - Phát hiện ô "orphan" (floor nhưng không kết nối)
   - Đục hành lang L-shape nối orphan vào component chính
   - Lặp tối đa 32 lần cho đến khi không còn orphan
```

**Tại sao dùng DFS?** DFS tạo ra mê cung dài, ít nhánh rẽ – cảm giác "mê cung thật sự". Mở loop sau đó giảm độ phức tạp để gameplay vẫn mượt.

**Thông số điều chỉnh theo round:**

| Thông số | Round 1 | Round 2 | Round 3 |
|---|---|---|---|
| `loopAddRatio` | 0.12 | 0.09 | 0.06 |
| `deadEndPasses` | 2 | 1 | 0 |
| `wallRestoreChance` | 0.55 | 0.68 | 0.81 |

**Độ phức tạp:** O(W × H) thời gian và không gian.

---

### 12.2 BFS – Breadth-First Search

**Vị trí trong code:** `bfs()` (~dòng 550), `bfsDistanceMap()` (~dòng 570)

**Hai biến thể được dùng:**

**a) `bfs(grid, sx, sy, tx, ty, W, H)` – tìm đường:**
- Tìm đường ngắn nhất từ `(sx, sy)` đến `(tx, ty)` trong mê cung.
- Trả về danh sách bước `[{dx, dy}, ...]`.
- Được dùng làm **fallback** khi A\* hoặc Dijkstra không tìm thấy đường.
- Dùng cho **CPU Easy** (đường đi đơn giản, không né nguy hiểm).

**b) `bfsDistanceMap(grid, sx, sy, W, H)` – bản đồ khoảng cách:**
- BFS từ một nguồn, trả về `Float32Array` khoảng cách từ nguồn đến mọi ô.
- Dùng trong **CSP** để tính `distMaps` từ từng base → đánh giá fairness kho báu.
- Dùng trong **CPU Hard** để cache khoảng cách từ CPU đến mọi ô (`cpuDistMap`).

```
BFS Queue: [(sx, sy)]
dist[sx][sy] = 0
While queue không rỗng:
  (x, y) = dequeue
  For mỗi hướng 4-liên kề (nx, ny):
    If không phải tường và chưa thăm:
      dist[ny][nx] = dist[y][x] + 1
      Enqueue (nx, ny)
```

**Độ phức tạp:** O(W × H).

---

### 12.3 A\* (A-star) Pathfinding

**Vị trí trong code:** `aStar()` (~dòng 640), `aStarSafe()` (~dòng 1000)

**Hai biến thể:**

**a) `aStar(grid, sx, sy, tx, ty, W, H)` – A\* chuẩn:**

Sử dụng heuristic **Manhattan Distance**: `h(x,y) = |x−tx| + |y−ty|`

```
Open list (Min Binary Heap, so sánh f = g + h)
gScore[start] = 0
While open không rỗng:
  cur = pop node có f nhỏ nhất
  If cur == target: truy vết đường đi và trả về
  For mỗi hàng xóm (nx, ny):
    ng = gScore[cur] + 1
    If ng < gScore[ni]:
      gScore[ni] = ng
      prev[ni] = cur
      Push {i: ni, f: ng + h(nx,ny)} vào open
```

- Dùng `MinBinaryHeap` tự cài (không dùng sort) để đảm bảo O(log n) mỗi thao tác.
- Dùng `seq` làm tie-breaker khi hai node có `f` bằng nhau.
- **CPU Normal** dùng A\* chuẩn.
- A\* fallback về BFS nếu không tìm thấy đường.

**b) `aStarSafe(grid, gcResult, dangerZones, sx, sy, tx, ty, W, H, dangerWeight)` – A\* né nguy hiểm:**

Mở rộng A\* bằng cách tăng chi phí di chuyển qua **vùng nguy hiểm** (theo Graph Coloring zone):

```
Chi phí di chuyển qua ô (nx, ny):
  color = gcResult.colorMap[ny*W+nx]
  zoneCost = dangerZones[color] * dangerWeight   // nguy hiểm từng vùng màu
  g(nx, ny) = g(cur) + 1 + zoneCost
```

- `dangerZones[c]` = tổng nguy hiểm vùng màu c: mỗi quái trong vùng +2, holder +1.
- **CPU Hard** dùng `aStarSafe` trong giai đoạn khởi tạo (trước khi có INF_MAP).

**Độ phức tạp:** O((V + E) log V) với V = số ô floor, E = số cạnh lưới.

---

### 12.4 Dijkstra / Uniform Cost Search với Influence Map

**Vị trí trong code:** `dijkstraSafe()` (~dòng 1055)

Đây là thuật toán tìm đường **chính xác nhất** trong dự án, dùng riêng cho **CPU Hard** khi đã có Influence Map.

**Khác biệt với A\*:** Không có heuristic (h=0), nhưng chi phí từng ô được tính **động** từ `INF_MAP` ở cell-level (chính xác hơn zone-level của `aStarSafe`).

**Công thức chi phí ô:**

```
cellCost = 1   (chi phí cơ bản)

// Influence Map (cell-level)
if costMode == 'safe':
  cellCost += INF_MAP.danger[ni] * 3      // né nguy hiểm mạnh
elif costMode == 'seek':
  cellCost += INF_MAP.danger[ni] * 0.5   // chấp nhận nguy hiểm nhẹ
  cellCost -= min(0.8, INF_MAP.opportunity[ni] * 0.12)  // thu hút cơ hội

// Quiz tile: tốn thêm 3 (thời gian trả lời)
if grid[ni] == T_QUIZ: cellCost += 3

// Choke point do đối thủ kiểm soát
if costMode == 'safe' and isCellChokePoint(nx, ny): cellCost += 4

// Ô cần tránh (quái gần, bẫy gần)
if costMode == 'safe' and shouldAvoidCell(actor, nx, ny): cellCost += 3.2
```

**Hai chế độ:**

| Chế độ | Mục đích | Dùng khi |
|---|---|---|
| `'safe'` | Né nguy hiểm tối đa | CPU đang mang kho báu về base |
| `'seek'` | Chấp nhận nguy hiểm, đến đích nhanh | CPU đang đi lấy kho báu |

**Độ phức tạp:** O((V + E) log V).

---

### 12.5 Constraint Satisfaction Problem (CSP)

**Vị trí trong code:** `cspSolve()` (~dòng 2560), `cspCheckTreasure()`, `cspCheckMonster()`, `cspCheckQuiz()`

Đây là **thuật toán trung tâm** của đồ án. CSP đảm bảo mọi thực thể (kho báu, quái vật, quiz) được đặt ở vị trí hợp lệ theo hệ thống ràng buộc.

#### Mô hình CSP

```
Biến (Variables):
  X0          = vị trí kho báu
  X1..Xm      = vị trí m quái vật
  Xm+1..Xm+n = vị trí n quiz tile

Miền giá trị (Domains):
  Tất cả ô floor trong mê cung (loại ô tường)

Ràng buộc (Constraints):
  Xem bảng bên dưới
```

#### Ràng buộc theo thực thể

**Kho báu:**

| Ràng buộc | Mô tả |
|---|---|
| `treasureMinDistBase` | Khoảng cách Manhattan đến mỗi base ≥ ngưỡng (tăng theo round) |
| `treasureFairnessStdMax` | Độ lệch chuẩn khoảng cách BFS từ các base ≤ ngưỡng |
| `treasureFairnessLeadMax` | Khoảng cách base gần nhất − base xa nhất ≤ ngưỡng |
| `treasureAntiCampLeadMax` | Chênh lệch khoảng cách tối đa (chống camping một góc) |
| Reachable | Phải tồn tại đường đi BFS từ tất cả base |

**Quái vật:**

| Ràng buộc | Mô tả |
|---|---|
| `monsterMinDistBase` | Khoảng cách BFS đến mỗi base ≥ ngưỡng |
| `monsterMinDistEach` | Khoảng cách Manhattan giữa các quái ≥ ngưỡng |
| `monsterMinDistTreasure` | Quái không ôm sát kho báu ngay từ đầu |
| Không trùng | Không trùng vị trí với kho báu và quái khác |

**Quiz tile:**

| Ràng buộc | Mô tả |
|---|---|
| `quizMinSpread` | Khoảng cách Manhattan giữa các quiz ≥ ngưỡng |
| Không trùng | Không trùng base, kho báu, quái |

#### Chiến lược giải CSP

CSP được giải theo **3 phase tuần tự** (không backtrack toàn bộ mà phase sau dựa vào kết quả phase trước):

```
Phase 1 – Treasure (LCV + Fairness Scoring):
  Sắp xếp domain bằng LCV (Least Constraining Value):
    Ưu tiên ô có nhiều hàng xóm floor nhất (mở nhất)
  Duyệt domain đã sắp xếp:
    Kiểm tra hard constraints (khoảng cách, fairness)
    Nếu qua → tính score = −fairStd×18 − fairLead×6 + fairMin×0.6 − centerBias×0.25 + openness×1.2
    Giữ lại bestTreasure có score cao nhất
  Fallback: nếu không tìm được → thử lại với constraints nới lỏng hơn

Phase 2 – Monsters (Greedy + Graph Coloring spawn):
  Spawn quái phân tán theo Graph Coloring (mỗi quái 1 vùng màu khác nhau)
  Kiểm tra hard constraints cho từng quái
  Nếu thất bại: fallback placement (BFS từ trung tâm)

Phase 3 – Quiz (Graph Coloring phân tán):
  Phân quota quiz cho mỗi nhóm màu (ít nhất 1 quiz/màu)
  Đặt quiz trong từng nhóm màu để phân tán đều khắp bản đồ
```

#### LCV (Least Constraining Value)

```javascript
function lcvOrder(candidates, grid, W, H) {
  return candidates
    .map(p => ({
      ...p,
      openness: neighbors4(p.x, p.y, W, H)
                  .filter(n => grid[n.y*W+n.x] !== T_WALL).length
    }))
    .sort((a, b) => b.openness - a.openness);  // ô thông thoáng nhất trước
}
```

#### CSP Reroll – Cơ chế kiểm tra chất lượng

Sau khi CSP trả về kết quả, hệ thống **đánh giá chất lượng bản đồ** và có thể reroll:

```
evaluateGeneratedMapQuality(layout):
  Tính fairnessScore = 100 - fairStd * 18 - fairLead * 7
  Tính monsterSpreadScore
  Tính quizDistributionScore
  Tổng hợp → mapQualityScore (0–100)

shouldRejectCspResult(layout):
  Return true nếu:
    fairStd > CSP_MAX_FAIRNESS_STD_BEFORE_REROLL (5.6)
    hoặc mapQualityScore < CSP_MIN_MAP_QUALITY_SCORE (61)

generateAcceptedRoundLayout(round):
  Loop tối đa CSP_MAX_REROLL_ATTEMPTS (3) lần:
    Chạy CSP với seed khác nhau
    Nếu chất lượng đạt → trả về
  Return kết quả tốt nhất trong các lần thử
```

---

### 12.6 Graph Coloring – Tô màu đồ thị

**Vị trí trong code:** `applyGraphColoring()` (~dòng 855)

**Mô hình đồ thị:**
- **Đỉnh (V):** Mọi ô floor/quiz trong mê cung.
- **Cạnh (E):** Hai ô kề nhau theo 4 hướng (không có tường ngăn).
- **Bài toán:** Gán màu cho mỗi đỉnh sao cho không có 2 đỉnh kề nhau cùng màu.

**Thuật toán: Greedy Graph Coloring**

```
colorMap = [-1, -1, ..., -1]   // W×H phần tử
numColors = 0

Duyệt theo thứ tự raster (từ trên xuống, trái sang phải):
  For mỗi ô (x, y) không phải tường:
    usedColors = tập màu của 4 hàng xóm (đã được tô)
    c = số nguyên nhỏ nhất không có trong usedColors
    colorMap[y*W+x] = c
    numColors = max(numColors, c+1)
```

Thuật toán **Greedy** này không đảm bảo số màu tối thiểu (chromatic number) nhưng hiệu quả O(V+E) và cho kết quả ổn định với lưới mê cung.

**Ứng dụng trong game:**

| Ứng dụng | Mô tả |
|---|---|
| **Quiz placement** | Phân quota quiz theo nhóm màu → quiz phân tán đều khắp bản đồ |
| **Monster spawn** | Mỗi quái spawn thuộc nhóm màu khác nhau → quái phân tán tối đa |
| **Zone danger (CPU)** | Tính `dangerZones[color]` để CPU né vùng có quái/holder |
| **A\* Safe** | `aStarSafe` tăng chi phí đi qua vùng nguy hiểm theo màu |
| **Debug overlay** | Nhấn `G` để hiển thị màu từng vùng trên bản đồ |

---

### 12.7 Thuật toán Tarjan – Articulation Points & Bridges

**Vị trí trong code:** `findArticulationPoints()` (~dòng 1418), `findBridges()` (~dòng 1470)

**Mục đích:** Tìm **điểm khớp (articulation point)** và **cầu (bridge)** trong đồ thị mê cung – đây là các vị trí chiến lược trọng yếu của bản đồ.

**Định nghĩa:**
- **Articulation point:** Đỉnh mà khi xóa đi sẽ làm tăng số thành phần liên thông của đồ thị.
- **Bridge:** Cạnh mà khi xóa đi sẽ làm tăng số thành phần liên thông.

**Thuật toán Tarjan (DFS Iterative):**

```
visited[v], disc[v], low[v], parent[v]
timer = 0

DFS từ mỗi đỉnh chưa thăm:
  Stack = [{u: start, ai: 0, cc: 0}]
  Khi xử lý đỉnh u:
    disc[u] = low[u] = timer++
    Với mỗi hàng xóm v của u:
      If v chưa thăm:
        cc++ (đếm con DFS của u)
        Đệ quy vào v
        After return: low[u] = min(low[u], low[v])
        Kiểm tra AP:
          - Root AP: parent[u] == -1 và cc >= 2
          - Non-root AP: low[v] >= disc[u]
      Else if v != parent[u]:
        low[u] = min(low[u], disc[v])   // back edge
```

Sử dụng **stack tường minh** (iterative) thay vì đệ quy để tránh stack overflow với mê cung lớn 41×25 (~500 đỉnh).

**Xếp hạng choke point chiến lược:**

```javascript
rank = 1000 / (distCenter + 1) + 500 / (avgBaseDist + 1)
```

- Ô gần trung tâm bản đồ: rank cao.
- Ô nằm giữa nhiều base: rank cao.
- Top choke points được cache lại theo seed (`CHOKE_CACHE`).

**Ứng dụng:**
- **CPU Hard** sử dụng choke points để **phục kích** (ambush) hoặc **phòng thủ** (defense).
- `buildInfluenceMap()` thêm điểm nguy hiểm tại top-10 choke points.
- Debug overlay "C" hiển thị articulation points trên bản đồ.

---

### 12.8 Influence Map / Danger Map

**Vị trí trong code:** `buildInfluenceMap()` (~dòng 1152), `INF_MAP` object

**Mục đích:** Tạo bản đồ số hóa thể hiện mức độ **nguy hiểm** và **cơ hội** tại mỗi ô — là nền tảng cho AI CPU Hard đưa ra quyết định.

**Cấu trúc:**

```
INF_MAP.danger[i]      // Float32Array(W×H) – điểm nguy hiểm tại ô i
INF_MAP.opportunity[i] // Float32Array(W×H) – điểm cơ hội tại ô i
```

**Hàm lan tỏa (spread):**

```
spread(arr, cx, cy, baseVal, radius):
  For mỗi ô (x, y) trong vùng Manhattan radius:
    If không phải tường:
      d = |x-cx| + |y-cy|
      arr[y*W+x] += baseVal * (1 - d / (radius+1))
```

Giá trị giảm dần tuyến tính theo khoảng cách từ nguồn.

**Các nguồn nguy hiểm và cơ hội:**

| Nguồn | Loại | Base value | Radius |
|---|---|---|---|
| Quái vật | Danger | 10 | 5 |
| Bẫy đang tồn tại | Danger | 6 | 2 |
| Enemy player | Danger | 3 (1.2 khi grace) | 3 |
| Top-10 choke points | Danger | 2 | 1 |
| CPU player (holder) | Danger | 1 | 2 |
| Kho báu tự do | Opportunity | 10 | 6 |
| Enemy holder | Opportunity | 8 (2.5 khi grace) | 4 |
| Base của CPU | Opportunity | 5 | 3 |

**Ứng dụng:**

```
dijkstraSafe (safe mode):  cellCost += danger[ni] * 3
dijkstraSafe (seek mode):  cellCost += danger[ni] * 0.5
                          cellCost -= min(0.8, opportunity[ni] * 0.12)

scoreCellByInfluence:  score = opportunity*2.1 - danger*2.6 - dist*0.45
shouldAvoidCell:       return danger > 13 OR (danger > 9 AND opportunity < 3)
```

**Rebuild strategy:** `buildInfluenceMap()` được gọi sau mỗi lần quái hoặc người chơi di chuyển đáng kể (không gọi mỗi frame để tiết kiệm CPU).

---

### 12.9 Monster Assignment – Greedy Heuristic với Budget Control

**Vị trí trong code:** `assignMonstersToTargets()` (~dòng 1702)

**Bài toán:** Phân công mỗi quái vật một **chiến lược mục tiêu** sao cho áp lực đối với người chơi được tối ưu.

**Các loại mục tiêu (target modes):**

| Mode | Mô tả |
|---|---|
| `direct_chase` | Trực tiếp đuổi theo một người chơi cụ thể |
| `zone_control` | Canh giữ vùng xung quanh holder (người đang mang kho báu) |
| `mid_control` | Kiểm soát khu vực giữa bản đồ |
| `defense` | Bảo vệ vùng gần base |
| `patrol` | Tuần tra bình thường |

**Phân bổ budget:**

```
directBudget = min(numPlayers, numMonsters)    // 1 quái/người max
zoneBudget   = holder ? 1 : 0                  // chỉ khi có holder
leftover     = numMonsters - directBudget - zoneBudget
midBudget    = ceil(leftover * 0.6)
defenseBudget = leftover - midBudget
```

**Thuật toán gán (Greedy với Regret-based Ordering):**

```
1. Với mỗi quái mi, tính "regret" = cost_best2 - cost_best1
   → Sắp xếp quái theo regret giảm dần (quái "khó chọn" được ưu tiên xử lý trước)

2. For mỗi quái mi (theo thứ tự regret):
   best = null
   For mỗi target t:
     If budget[t.mode] còn dư AND cap[t] chưa đầy:
       If t.mode == direct_chase AND player đang trong grace: skip
       cost = computeMonsterAssignmentCost(mi, t, {pressureByPlayer, ...})
       update best nếu cost thấp hơn
   Nếu không có best → fallback (bỏ qua budget mode, chỉ giữ grace constraint)
   Gán assignments[mi] = best.t
   Cập nhật pressureByPlayer, modeUsage, targetUsage
```

**Hàm chi phí gán:**

Chi phí phụ thuộc vào khoảng cách Manhattan quái–target, áp lực hiện tại lên từng người chơi, và mode cụ thể.

---

### 12.10 Minimax với Alpha-Beta Pruning (Tactical Search)

**Vị trí trong code:** `tacticalSearch()` (~dòng 2100)

CPU Hard sử dụng **Minimax** với **Alpha-Beta Pruning** cho các quyết định chiến thuật ngắn hạn:

```
tacticalSearch(cpu, depth=3):
  Trạng thái = {cpuPos, playerPos, treasurePos, holders}
  Max player = CPU (muốn maximize utility)
  Min player = opponent (muốn minimize utility)

  Alpha-Beta Pruning:
    alpha = −∞ (giá trị tốt nhất CPU đã tìm được)
    beta  = +∞  (giá trị tốt nhất opponent đã tìm được)
    Nếu alpha >= beta → cắt tỉa nhánh

  Utility function:
    + Gần kho báu (nếu chưa có)
    + Gần base (nếu đang giữ kho báu)
    + Gần holder (nếu muốn cướp)
    − Gần quái vật
    − Gần bẫy
    − Gần choke point nguy hiểm
```

**Kết quả:** `tacticalSearch` trả về action tốt nhất (`{dx, dy}`) cho CPU trong các tình huống cụ thể như: cướp kho báu, né bẫy, thoát khỏi góc chết.

---

### Tổng kết các thuật toán

| Thuật toán | Lớp | Ứng dụng trong game |
|---|---|---|
| **DFS Randomized** | Tree Search | Sinh mê cung có cấu trúc |
| **BFS** | Graph Search | Tìm đường ngắn nhất, distance map |
| **A\*** | Heuristic Search | CPU Normal pathfinding |
| **A\* Safe** | Heuristic + Zone Cost | CPU Hard khởi tạo |
| **Dijkstra / UCS** | Optimal Search | CPU Hard runtime (cell-level cost) |
| **CSP + Backtracking** | Constraint Satisfaction | Đặt kho báu, quái, quiz đảm bảo công bằng |
| **LCV Heuristic** | CSP Ordering | Tối ưu thứ tự thử domain trong CSP |
| **Greedy Graph Coloring** | Graph Coloring | Phân vùng quiz, spawn quái phân tán |
| **Tarjan (Iterative DFS)** | Graph Analysis | Tìm articulation point và bridge |
| **Influence / Danger Map** | Potential Field | Nền tảng quyết định CPU Hard |
| **Greedy Assignment** | Combinatorial Opt. | Phân công quái–mục-tiêu |
| **Minimax + Alpha-Beta** | Adversarial Search | Quyết định chiến thuật CPU Hard |

---

## 13. Hệ thống AI của CPU

### 13.1 Dễ (`CPU_EASY_MS = 900ms`)

- Pathfinding bằng **BFS** thuần.
- Xác suất di chuyển ngẫu nhiên cao (~40%).
- Phản ứng chậm, không né nguy hiểm tích cực.
- Mục tiêu đơn giản: đi lấy kho báu → đi về base.

### 13.2 Thường (`CPU_NORMAL_MS = 550ms`)

- Pathfinding bằng **A\*** chuẩn.
- Cân bằng giữa đuổi mục tiêu và phản ứng nguy hiểm cơ bản.
- Biết cướp kho báu từ đối thủ.
- Tránh ô có quái gần.

### 13.3 Khó (`CPU_HARD_MS = 280ms`)

- Pathfinding bằng **Dijkstra Safe** (cell-level danger cost).
- Dùng **Influence Map** để đánh giá tất cả ô xung quanh.
- Dùng **Choke Point analysis** để phục kích hoặc phòng thủ.
- Dùng **Minimax + Alpha-Beta** cho quyết định chiến thuật.
- Cache **BFS distance map** từ vị trí CPU để tối ưu tính toán.
- Quản lý **state machine** đầy đủ: seek → ambush → return → flee → steal.

---

## 14. Giao thức mạng MQTT và đồng bộ trạng thái

### 14.1 Các message type

| Type | Hướng | Mô tả |
|---|---|---|
| `JOIN` | Client → Host | Tham gia phòng |
| `ROOM_UPDATE` | Host → All | Cập nhật danh sách phòng |
| `REJECT` | Host → Client | Từ chối tham gia |
| `INIT` | Host → All | Khởi tạo ván mới (seed, layout CSP) |
| `MOVE` | Client → Host | Gửi input di chuyển |
| `TRAP_REQUEST` | Client → Host | Yêu cầu đặt bẫy |
| `UPDATE` | Host → All | **Snapshot đầy đủ trạng thái game** |
| `REGEN_MAP` | Host → All | Tái sinh bản đồ |
| `ROUND_END` | Host → All | Kết thúc ván |
| `NEXT_ROUND` | Host → All | Chuyển sang ván tiếp theo |
| `MATCH_END` | Host → All | Kết thúc trận |
| `RETURN_LOBBY` | Host → All | Trở về lobby |
| `LEAVE` | Client → All | Rời phòng |

**Topic:** `mazeduel/room/<ROOM_CODE>`

### 14.2 Snapshot đồng bộ (UPDATE message)

Mỗi UPDATE snapshot chứa:

```json
{
  "type": "UPDATE",
  "tickId": 42,
  "seq": 187,
  "serverTs": 1709800000000,
  "snapshot": {
    "tickId": 42, "seq": 187, "serverTs": ..., "reason": "monster_tick",
    "players": [{"idx":0,"x":5,"y":3,"has":false,"score":1,...}],
    "monsters": [{"idx":0,"x":10,"y":7,"mode":"chase","targetPlayerIdx":0}],
    "treasure": {"x":20,"y":12},
    "treasureHolder": -1,
    "traps": [{"owner":1,"x":8,"y":4,"createdAt":...,"ttl":12000}],
    "events": [...],
    "regen": null
  }
}
```

### 14.3 Snapshot ordering (chống lag/out-of-order)

Client chỉ áp dụng snapshot **mới hơn** snapshot đã nhận:

```javascript
isIncomingSnapshotNewer(tickId, seq, serverTs):
  If tickId >  lastTick: return true
  If tickId == lastTick AND seq >  lastSeq: return true
  If tickId == lastTick AND seq == lastSeq AND serverTs > lastTs: return true
  return false  // drop stale snapshot
```

### 14.4 Event queue

Mỗi snapshot piggybacking tối đa 10 sự kiện gần nhất:

| Event | Trigger |
|---|---|
| `treasure_pickup` | Người chơi nhặt kho báu |
| `treasure_steal` | Cướp kho báu |
| `trap_place` | Đặt bẫy |
| `trap_hit` | Dẫm phải bẫy |
| `trap_expire` | Bẫy hết TTL |
| `monster_hit` | Quái chạm người chơi |
| `map_regen` | Bản đồ tái sinh |

---

## 15. Các cấu hình quan trọng

Trong object `CFG` của `claudegame.html`:

| Hằng số | Mặc định | Mô tả |
|---|---|---|
| `W`, `H` | 41, 25 | Kích thước mê cung (ô) |
| `TILE` | 16 | Kích thước mỗi ô (pixel) |
| `MAX_PLAYERS` | 4 | Số người chơi tối đa |
| `MONSTER_MOVE_MS` | 450 | Chu kỳ di chuyển quái (ms) |
| `TRAP_LIMIT` | 3 | Số bẫy tối đa mỗi người |
| `TRAP_TTL` | 12000 | Thời gian sống bẫy (ms) |
| `BO3` | 3 | Số ván tối đa mỗi trận |
| `LOOP_ADD_RATIO` | 0.12 | Tỉ lệ thêm vòng lặp vào maze |
| `DEAD_END_PASSES` | 2 | Số lần xử lý dead-end |
| `CPU_EASY_MS` | 900 | Tốc độ CPU Dễ (ms/bước) |
| `CPU_NORMAL_MS` | 550 | Tốc độ CPU Thường |
| `CPU_HARD_MS` | 280 | Tốc độ CPU Khó |
| `CSP_MAX_REROLL_ATTEMPTS` | 3 | Số lần reroll CSP tối đa |
| `CSP_MAX_FAIRNESS_STD_BEFORE_REROLL` | 5.6 | Ngưỡng reject CSP (độ lệch chuẩn fairness) |
| `CSP_MIN_MAP_QUALITY_SCORE` | 61 | Điểm chất lượng tối thiểu để chấp nhận bản đồ |
| `MQTT_URL` | `wss://broker.emqx.io:8084/mqtt` | Địa chỉ MQTT broker |

---

## 16. Debug và đánh giá chất lượng bản đồ

### Debug panel (phím `Tab`)

Hiển thị: FPS, Ping MQTT, mode, số người, round, số trap, thông tin CSP, Graph Coloring, Influence Map, trạng thái AI CPU, Choke Points, Minimax.

### Overlay bản đồ

| Phím | Overlay |
|---|---|
| `G` | Graph Coloring vùng màu |
| `I` | Influence Map (danger/opportunity) |
| `C` | Choke Points (articulation points) |

### Console commands

```javascript
// Báo cáo chất lượng bản đồ hiện tại
mapQualityReport()

// Báo cáo quyết định AI CPU
aiDecisionReport()

// Báo cáo kết quả Tactical Search (Minimax)
tacticalSearchReport()

// Báo cáo phân công quái–mục-tiêu
monsterAssignmentReport()

// Chạy offline optimizer (thử nghiệm tham số tối ưu)
runOfflineOptimizer({ samplesPerRound: 3, numPlayers: 2 })
```

---

## 17. Ưu điểm và hạn chế

### Ưu điểm

- Chạy gọn trong một file, dễ demo và nộp bài.
- Ứng dụng **8+ thuật toán AI** rõ ràng, có thể minh họa trực quan.
- Có chế độ offline lẫn online hoàn chỉnh.
- CSP với hệ thống reroll đảm bảo layout đủ công bằng trước khi chơi.
- Debug panel và console tools đầy đủ cho mục đích học thuật.

### Hạn chế

- Logic tập trung trong một file HTML lớn, khó bảo trì.
- Online phụ thuộc vào MQTT broker công cộng (có thể ngắt kết nối).
- Host-authoritative ở mức client-side, chưa phải dedicated server.
- Không có test tự động hay hệ thống CI/CD.

---

## 18. Hướng phát triển

- Tách game logic thành nhiều module JavaScript riêng.
- Xây dựng dedicated authoritative server.
- Bổ sung replay, thống kê sau trận và lịch sử trận đấu.
- Mở rộng thêm vật phẩm, kỹ năng, nhiều loại quái vật.
- Thêm chế độ xếp hạng hoặc nhiều bản đồ.
- Thêm lag compensation và client-side prediction hoàn chỉnh cho online mode.
- Tối ưu AI theo hành vi người chơi.

## 20. Kết luận

`Maze Duel` là một đồ án game mê cung có tính tương tác cao, phù hợp để trình bày trong các môn học liên quan đến lập trình game, trí tuệ nhân tạo, hoặc hệ thống tương tác thời gian thực. Dự án thể hiện rõ sự kết hợp giữa:

- Thiết kế gameplay.
- Lập trình giao diện canvas.
- Đồng bộ trạng thái online.
- Ứng dụng các thuật toán AI trong thực tế.

Đây là một nền tảng tốt để tiếp tục mở rộng thành một sản phẩm hoàn chỉnh hơn trong tương lai.

## 21. Ghi chú bản quyền

Dự án hiện phù hợp cho mục đích học tập, báo cáo, bài tập lớn và trình diễn đồ án. Nếu muốn công bố rộng rãi, nên bổ sung thêm file license riêng như `MIT` hoặc `Apache-2.0`.
