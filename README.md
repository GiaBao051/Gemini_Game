# MAZE DUEL  
### Game mê cung 2 người chơi – Multiplayer Realtime với WebSocket

**Môn học:** Trí tuệ nhân tạo / Kỹ thuật thỏa mãn ràng buộc  
**Chương liên quan:** Chương 3 – Các phương pháp giải bài toán thỏa mãn ràng buộc  

---

## 1. Giới thiệu dự án

**Maze Duel** là một game 2D góc nhìn top-down, lấy cảm hứng từ Pacman, trong đó **2 người chơi thi đấu trực tiếp** trong một mê cung.  
Mục tiêu của trò chơi là **tìm và mang một kho báu duy nhất về vị trí xuất phát của mình** để giành chiến thắng.

Điểm đặc biệt của dự án:
- Game chạy **realtime multiplayer** thông qua **WebSocket**
- Mê cung và chướng ngại vật **không tĩnh**, có thể thay đổi theo thời gian
- Trò chơi **ứng dụng trực tiếp các thuật toán AI trong Chương 3**, bao gồm:
  - Bài toán thỏa mãn ràng buộc (CSP)
  - Thuật toán tô màu đồ thị
  - Bài toán phân công công việc (Hungarian Algorithm)

Dự án vừa mang tính **thực hành lập trình**, vừa là **minh chứng trực quan cho việc ứng dụng thuật toán AI vào hệ thống thực tế**.

---

## 2. Luật chơi & Gameplay

### 2.1 Mục tiêu
- Tìm **kho báu (Treasure)** trong mê cung
- Nhặt kho báu và **đưa về đúng điểm xuất phát của mình**
- Người đầu tiên mang kho báu về thành công sẽ **chiến thắng**

### 2.2 Các giai đoạn (Phase)
- **SEARCH**  
  Hai người chơi cùng tìm kho báu
- **RETURN**  
  Khi một người nhặt kho báu:
  - Người đó phải mang kho báu về điểm xuất phát
  - Người còn lại được quyền **truy đuổi và cướp kho báu**

### 2.3 Chướng ngại vật – Quiz
- Các ô màu vàng là **Quiz Tile**
- Khi bước vào, người chơi:
  - Bị khóa di chuyển
  - Phải trả lời một câu hỏi (toán học, logic, mẹo…)
- Trả lời đúng → tiếp tục  
- Trả lời sai → bị phạt (delay / mất lượt)

### 2.4 Cướp kho báu
- Nếu đối thủ **chạm vào người đang giữ kho báu**
- Kho báu sẽ **đổi chủ**

---

## 3. Kiến trúc hệ thống

### 3.1 Mô hình Client – Server

Server giữ vai trò **authoritative server**:
- Xử lý toàn bộ logic game
- Kiểm tra va chạm, luật chơi, chiến thắng
- Client chỉ gửi input và hiển thị trạng thái

┌───────────────┐ WebSocket ┌────────────────────────┐
│ Web Client A │ <-------------------> │ FastAPI Game Server │
│ (Canvas UI) │ │ GameRoom + Algorithms │
└───────────────┘ └────────────────────────┘
┌───────────────┐ WebSocket ┌────────────────────────┘
│ Web Client B │ <-------------------> │ CSP / Coloring / │
│ (Canvas UI) │ │ Hungarian Algorithms │
└───────────────┘ └────────────────────────┘

---

## 4. Công nghệ sử dụng

- **Python 3.10+**
- **FastAPI** (WebSocket server)
- **Uvicorn** (ASGI server)
- **HTML / CSS / JavaScript**
- Canvas API cho render game 2D

---

## 5. Cấu trúc thư mục

├─ app.py # FastAPI server + WebSocket endpoint
├─ game.py # Game loop, room, state, luật chơi
├─ maze.py # Sinh mê cung + biến đổi map
├─ questions.py # Ngân hàng câu hỏi
├─ web_client_v2.html # Giao diện web
├─ requirements.txt
└─ algorithms/
├─ csp_placement.py # CSP – đặt treasure & quiz
├─ coloring.py # Tô màu đồ thị quiz
└─ hungarian.py # Bài toán phân công công việc

---

## 6. Hướng dẫn cài đặt & chạy

### 6.1 Tạo môi trường ảo
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
Nếu bị chặn:
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned -Force

### 6.2 Cài thư viện
python -m pip install -r requirements.txt

### 6.3 Chạy server
python -m uvicorn app:app --host 127.0.0.1 --port 8080 --reload

### 6.4 Mở game
Mở trình duyệt:
http://127.0.0.1:8080/
Mở 2 tab để chơi 2 người.

## 7. Giao thức WebSocket
Client → Server
{ "type": "join", "name": "Player1" }
{ "type": "input", "dir": "U" }
{ "type": "answer", "qid": "...", "choice": 2 }

## 8. Ứng dụng các thuật toán AI
# 8.1 Thuật toán 1 – Bài toán thỏa mãn ràng buộc (CSP)

Bài toán
Cần đặt:
1 kho báu (Treasure)
N ô Quiz
Thỏa các ràng buộc:
Kho báu reachable từ cả 2 người chơi
Kho báu cân bằng khoảng cách giữa 2 người chơi
Quiz không trùng nhau, không trùng start
Quiz cách nhau tối thiểu một khoảng nhất định
Giải pháp
Dùng BFS để tính khoảng cách
Backtracking + pruning để tìm nghiệm thỏa mãn
📁 File: algorithms/csp_placement.py

# 8.2 Thuật toán 2 – Tô màu đồ thị (Graph Coloring)
Mục tiêu
Các ô Quiz gần nhau không nên cùng loại câu hỏi
Mô hình
Node = 1 Quiz
Edge nếu 2 Quiz ở gần nhau
Dùng Greedy Coloring để gán màu → ánh xạ thành category câu hỏi.
📁 File: algorithms/coloring.py

# 8.3 Thuật toán 3 – Bài toán phân công (Hungarian Algorithm)
Mục tiêu
Gán câu hỏi cho Quiz sao cho:
Quiz gần kho báu → câu hỏi khó
Quiz xa kho báu → câu hỏi dễ
Mô hình
Worker = Quiz tile
Job = Question
Cost = |difficulty - targetDifficulty|
Dùng Hungarian Algorithm để tối ưu tổng chi phí.
📁 File: algorithms/hungarian.py

# 9. Kết luận
Dự án Maze Duel đã:
Ứng dụng thành công 3 nhóm thuật toán AI
Kết hợp AI với game multiplayer realtime
Thể hiện rõ tính thực tiễn của các thuật toán trong Chương 3
Game có thể mở rộng thêm AI đối thủ, replay, spectator, hoặc học máy trong tương lai.

# 10. License

---

Nếu bạn muốn, mình có thể:
- ✍️ Viết **báo cáo Word/PDF** dựa trên README này  
- 🎯 Tóm tắt lại thành **slide thuyết trình**  
- 🧠 Thêm phần **đánh giá độ phức tạp & ưu/nhược điểm** cho từng thuật toán  

Bạn chỉ cần nói 👍
