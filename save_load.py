
import json, datetime, os
from pathlib import Path
from typing import Union
from game import GameState

def save_game(gs: GameState, filepath: Union[str, os.PathLike]):
    data = gs.to_dict()
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f)

def load_game(filepath: Union[str, os.PathLike]) -> GameState:
    from game import GameState
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return GameState.from_dict(data)
