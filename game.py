
from __future__ import annotations
import json, math
from copy import deepcopy
from pathlib import Path
from typing import List, Dict, Tuple
import numpy as np

COST_FORT = 800

class GameState:
    """Logica principale del gioco"""
    def __init__(self, terrain: np.ndarray, k: int = 2):
        self.terrain = terrain
        self.n = terrain.shape[0]
        self.k = k
        self.forts: List[Dict] = []  # List[{'player': int, 'x': int, 'y': int, 'height': float, 'turn': int}]
        self.credits = [2000, 2000]
        self.scores = [0.0, 0.0]
        self.turn_count = 0
        self.current_player = 0  # 0 o 1
        self.history: List[Dict] = []  # azioni serializzate per replay

    # ----- Helpers ---------------------------------------------------------
    def distance2(self, x1, y1, x2, y2) -> int:
        return (x1 - x2)**2 + (y1 - y2)**2

    def can_place(self, player: int, x: int, y: int) -> bool:
        if not (0 <= x < self.n and 0 <= y < self.n):
            return False
        if self.credits[player] < COST_FORT:
            return False
        # altezza della casella - niente forti nell'acqua
        if float(self.terrain[x, y]) < 0.3:
            return False
        # Check already occupied
        for f in self.forts:
            if f['x'] == x and f['y'] == y:
                return False
            if self.distance2(x, y, f['x'], f['y']) <= self.k**2:
                return False
        return True

    def production(self, height: float) -> int:
        """Return credits produced per turn based on fort height."""
        return int((1.0 - height) * 200)

    def _adjacent_bonus(self, fort: Dict) -> float:
        for other in self.forts:
            if other is fort:
                continue
            if other['player'] == fort['player'] and self.distance2(fort['x'], fort['y'], other['x'], other['y']) <= 1:
                return 1.5
        return 1.0

    def place_fort(self, player: int, x: int, y: int) -> bool:
        if not self.can_place(player, x, y):
            return False
        h = float(self.terrain[x, y])
        self.credits[player] -= COST_FORT
        self.scores[player] += h ** 2
        self.forts.append({'player': player, 'x': x, 'y': y, 'height': h, 'turn': self.turn_count})
        self.history.append({'type': 'place', 'player': player, 'x': x, 'y': y})
        self._end_turn()
        return True

    def pass_turn(self, player: int):
        # produce crediti
        for f in self.forts:
            if f['player'] == player:
                prod = self.production(f['height'])
                prod = int(prod * self._adjacent_bonus(f))
                self.credits[player] += prod
        self.history.append({'type': 'pass', 'player': player})
        self._end_turn()

    def _end_turn(self):
        self.turn_count += 1
        self.current_player = 1 - self.current_player

    # --------- Fine partita -----------------------------------------------
    def any_valid_move(self, player: int) -> bool:
        if self.credits[player] < COST_FORT:
            return False
        for x in range(self.n):
            for y in range(self.n):
                if self.can_place(player, x, y):
                    return True
        return False

    def is_over(self) -> bool:
        return not (self.any_valid_move(0) or self.any_valid_move(1))

    def winner(self) -> int | None:
        if not self.is_over():
            return None
        if self.scores[0] > self.scores[1]:
            return 0
        if self.scores[1] > self.scores[0]:
            return 1
        return -1  # pareggio

    # ---------- Serializzazione -------------------------------------------
    def to_dict(self) -> Dict:
        return {
            'terrain': self.terrain.tolist(),
            'k': self.k,
            'forts': deepcopy(self.forts),
            'credits': self.credits.copy(),
            'scores': self.scores.copy(),
            'turn_count': self.turn_count,
            'current_player': self.current_player,
            'history': deepcopy(self.history)
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'GameState':
        import numpy as np
        gs = cls(np.array(data['terrain'], dtype=np.float32), k=data['k'])
        gs.forts = data['forts']
        gs.credits = data['credits']
        gs.scores = data['scores']
        gs.turn_count = data['turn_count']
        gs.current_player = data['current_player']
        gs.history = data['history']
        return gs
