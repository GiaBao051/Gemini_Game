# questions.py
from __future__ import annotations
import time
import uuid
from typing import Dict, Any, List, Optional, Tuple
import random

Question = Dict[str, Any]

CATEGORIES = ["math", "logic", "trick", "pattern"]

class QuestionBank:
    def __init__(self, seed: int = 1):
        self.rnd = random.Random(seed)
        self.answers: Dict[str, int] = {}
        # Minimal offline pool (bạn có thể mở rộng / dùng Gemini để sinh)
        self.pool: List[Question] = [
            {"category":"math","difficulty":1,"prompt":"2+3=?","choices":["4","5","6","7"],"answer_index":1},
            {"category":"math","difficulty":3,"prompt":"Nếu 5x=35 thì x=?","choices":["5","6","7","8"],"answer_index":2},
            {"category":"logic","difficulty":2,"prompt":"Sắp xếp đúng: 1, 1, 2, 3, 5, ...","choices":["6","7","8","9"],"answer_index":1},
            {"category":"trick","difficulty":2,"prompt":"Càng lấy đi càng lớn là gì?","choices":["Hố","Nước","Lửa","Bóng"],"answer_index":0},
            {"category":"pattern","difficulty":4,"prompt":"Chuỗi: 2, 6, 12, 20, ...","choices":["28","30","32","34"],"answer_index":0},
        ]

    def sample_questions(self, category: str, count: int) -> List[Question]:
        cand = [q for q in self.pool if q["category"] == category]
        if len(cand) < count:
            # fallback: cho phép lặp nếu thiếu
            return [self.rnd.choice(cand) for _ in range(count)]
        self.rnd.shuffle(cand)
        return cand[:count]

    def register_question(self, q: Question) -> Question:
        qid = f"q-{uuid.uuid4().hex[:8]}"
        self.answers[qid] = int(q["answer_index"])
        return {
            "id": qid,
            "category": q["category"],
            "difficulty": int(q["difficulty"]),
            "prompt": q["prompt"],
            "choices": q["choices"],
            "timeout_ms": 8000,
        }

    def check_answer(self, qid: str, choice: Any) -> bool:
        if qid not in self.answers:
            return False
        try:
            c = int(choice)
        except Exception:
            return False
        ans = self.answers.pop(qid)
        return c == ans
