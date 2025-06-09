
import pygame, sys, os, math, json, argparse
import numpy as np
from typing import Tuple
from terrain import generate_terrain
from game import GameState, COST_FORT
from save_load import save_game, load_game

TILE_SIZE = 30
MARGIN = 2
FONT_SIZE = 18
CHECKBOX_SIZE = 20
INFO_BG = (250, 250, 250)
INFO_FG = (10, 10, 10)

def height_color(h: float) -> Tuple[int, int, int]:
    """Return RGB color based on height"""
    # blu->verde->marrone
    if h < 0.3:
        # water-ish lowland
        t = h / 0.3
        return (int(0 + 55*t), int(100 + 100*t), int(200 + 55*t))
    elif h < 0.6:
        t = (h - 0.3) / 0.3
        return (int(55 + 100*t), int(200 + 30*t), int(55))
    else:
        t = (h - 0.6) / 0.4
        return (int(155 + 100*t), int(130 + 50*t), int(55))

class FortWarsGUI:
    def __init__(self, n=16, k=2, replay_path=None):
        pygame.init()
        self.n = n
        self.k = k
        self.font = pygame.font.SysFont('consolas', FONT_SIZE)
        self.clock = pygame.time.Clock()
        if replay_path:
            self.replay_mode = True
            self.gs = load_game(replay_path)
            self.replay_actions = iter(self.gs.history)
            self.paused = True
        else:
            self.replay_mode = False
            terrain = generate_terrain(n)
            self.gs = GameState(terrain, k=k)
        self.show_influence = False
        self.surface = pygame.display.set_mode((n*TILE_SIZE, n*TILE_SIZE + 60))
        pygame.display.set_caption('Fort Wars')
        self.main_loop()

    # ------------------------------------------------------------------
    def draw(self):
        surf = self.surface
        surf.fill((0,0,0))
        # Draw terrain
        for x in range(self.n):
            for y in range(self.n):
                h = float(self.gs.terrain[x, y])
                color = height_color(h)
                rect = pygame.Rect(y*TILE_SIZE, x*TILE_SIZE, TILE_SIZE-MARGIN, TILE_SIZE-MARGIN)
                pygame.draw.rect(surf, color, rect)

        # Influence
        if self.show_influence:
            mask = pygame.Surface((self.n*TILE_SIZE, self.n*TILE_SIZE), pygame.SRCALPHA)
            for f in self.gs.forts:
                cx = f['y']*TILE_SIZE + TILE_SIZE//2
                cy = f['x']*TILE_SIZE + TILE_SIZE//2
                color = (255,0,0,60) if f['player']==0 else (0,0,255,60)
                pygame.draw.circle(mask, color, (cx,cy), self.gs.k * TILE_SIZE, 0)
            surf.blit(mask, (0,0))

        # Draw forts
        for f in self.gs.forts:
            cx = f['y']*TILE_SIZE + TILE_SIZE//2
            cy = f['x']*TILE_SIZE + TILE_SIZE//2
            color = (255,0,0) if f['player']==0 else (0,0,255)
            pygame.draw.circle(surf, (0,0,0), (cx,cy), TILE_SIZE//2-2)
            pygame.draw.circle(surf, color, (cx,cy), TILE_SIZE//2-4)

        # UI bar
        bar = pygame.Rect(0, self.n*TILE_SIZE, self.n*TILE_SIZE, 60)
        pygame.draw.rect(surf, (40,40,40), bar)
        # Checkbox influence
        cb_rect = pygame.Rect(10, self.n*TILE_SIZE + 20, CHECKBOX_SIZE, CHECKBOX_SIZE)
        pygame.draw.rect(surf, (255,255,255), cb_rect, 2)
        if self.show_influence:
            pygame.draw.line(surf, (255,255,255), cb_rect.topleft, cb_rect.bottomright, 2)
            pygame.draw.line(surf, (255,255,255), cb_rect.topright, cb_rect.bottomleft, 2)
        label = self.font.render('Mostra influenza (I)', True, (200,200,200))
        surf.blit(label, (cb_rect.right + 8, cb_rect.top - 4))

        # Credits + scores
        txt = f'P0 Crediti: {self.gs.credits[0]:4d}  Score: {self.gs.scores[0]:.2f}   |   P1 Crediti: {self.gs.credits[1]:4d}  Score: {self.gs.scores[1]:.2f}'
        info = self.font.render(txt, True, (220,220,220))
        surf.blit(info, (self.n*TILE_SIZE//2 - info.get_width()//2, self.n*TILE_SIZE + 2))

        # Hover info
        mx, my = pygame.mouse.get_pos()
        grid_x = my // TILE_SIZE
        grid_y = mx // TILE_SIZE
        for f in self.gs.forts:
            if f['x']==grid_x and f['y']==grid_y:
                lines = [
                    f"Player: {f['player']}",
                    f"Coordinate: ({f['x']},{f['y']})",
                    f"Height: {f['height']:.2f}",
                    f"Prod/turn: {self.gs.production(f['height'])}"
                ]
                self.draw_tooltip(lines, mx, my)
                break

        pygame.display.flip()

    def draw_tooltip(self, lines, mx, my):
        padding = 4
        surfaces = [self.font.render(l, True, INFO_FG) for l in lines]
        width = max(s.get_width() for s in surfaces) + 2*padding
        height = sum(s.get_height() for s in surfaces) + 2*padding
        rect = pygame.Rect(mx, my - height, width, height)
        pygame.draw.rect(self.surface, INFO_BG, rect)
        pygame.draw.rect(self.surface, (0,0,0), rect, 1)
        y = rect.top + padding
        for s in surfaces:
            self.surface.blit(s, (rect.left + padding, y))
            y += s.get_height()

    # ------------------------------------------------------------------
    def main_loop(self):
        while True:
            self.handle_events()
            self.draw()
            self.clock.tick(30)

    # ------------------------------------------------------------------
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()
                if event.key == pygame.K_i:
                    self.show_influence = not self.show_influence
                if event.key == pygame.K_s and not self.replay_mode:
                    self.save_current_game()
                if self.replay_mode:
                    if event.key == pygame.K_SPACE:
                        self.step_replay()
                    if event.key == pygame.K_r:
                        self.paused = not self.paused
                else:
                    self.handle_game_key(event)
        # Auto play replay if not paused
        if self.replay_mode and not self.paused:
            pygame.time.wait(300)
            self.step_replay()

    def step_replay(self):
        try:
            action = next(self.replay_actions)
        except StopIteration:
            self.paused = True
            return
        if action['type']=='place':
            self.gs.place_fort(action['player'], action['x'], action['y'])
            # Undo forced role switch in original
            self.gs.current_player = action['player']
        else:
            self.gs.pass_turn(action['player'])
            self.gs.current_player = action['player']

    def handle_game_key(self, event):
        if event.key == pygame.K_p:
            # pass turn
            self.gs.pass_turn(self.gs.current_player)
        # Place fort with mouse + Enter shortcut
        if event.key == pygame.K_RETURN:
            mx, my = pygame.mouse.get_pos()
            x = my // TILE_SIZE
            y = mx // TILE_SIZE
            self.gs.place_fort(self.gs.current_player, x, y)

    def save_current_game(self):
        now = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'fortwars_{now}.json'
        save_path = os.path.join(os.getcwd(), filename)
        save_game(self.gs, save_path)
        print(f'Saved game to {save_path}')

def main():
    parser = argparse.ArgumentParser(description='Fort Wars GUI')
    parser.add_argument('--n', type=int, default=16)
    parser.add_argument('--k', type=int, default=2)
    parser.add_argument('--replay', type=str, help='Path JSON saved game')
    args = parser.parse_args()
    FortWarsGUI(n=args.n, k=args.k, replay_path=args.replay)

if __name__ == '__main__':
    main()
