import os, sys, numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from game import GameState, COST_FORT

def test_place_and_production():
    terrain = np.full((4,4), 0.5, dtype=np.float32)
    gs = GameState(terrain)
    assert gs.place_fort(0, 0, 0)
    assert gs.credits[0] == 2000 - COST_FORT
    gs.pass_turn(0)
    assert gs.credits[0] == 2000 - COST_FORT + gs.production(0.5)

