from dataclasses import dataclass, field
from typing import List, Optional
import random

PRIZES = [50, 250, 500, 1000, 2500, 5000, 10000, 25000, 75000]

@dataclass
class Question:
    text: str
    options: List[str]  # exactly 4
    correct: int        # 0..3

@dataclass
class GameState:
    user_id: int
    jokers: int = 7
    current_index: int = 0
    prize_level: int = -1  # -1 before 1st
    super_joker_used: bool = False
    active_question: Optional[Question] = None

    def lose_jokers_or_levels(self, wrong: bool):
        if not wrong:
            self.prize_level += 1
            return
        if self.jokers >= 3:
            self.jokers -= 3
        elif self.jokers == 2:
            self.jokers = 0
            self.prize_level -= 1
        elif self.jokers == 1:
            self.jokers = 0
            self.prize_level -= 2
        else:
            self.prize_level -= 3
        self.prize_level = max(self.prize_level, -1)