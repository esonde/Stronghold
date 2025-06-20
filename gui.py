
import pygame, sys, os, math, json, argparse, glob, datetime
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
    def __init__(self, n=18, k=2, replay_path=None):
        pygame.init()
        pygame.mixer.init()
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
        self.tile_size = TILE_SIZE
        self.surface = pygame.display.set_mode(
            (n * self.tile_size, n * self.tile_size + 60), pygame.RESIZABLE
        )
        self.offset_x = 0
        self.offset_y = 0
        self.update_layout()
        self.check_auto_pass()
        pygame.display.set_caption('Fort Wars')
        if not replay_path:
            self.menu_loop()
        self.main_loop()

    def update_layout(self, w=None, h=None):
        if w is None or h is None:
            w, h = self.surface.get_size()
        self.tile_size = min(w // self.n, (h - 60) // self.n)
        self.offset_x = (w - self.n * self.tile_size) // 2
        self.offset_y = (h - 60 - self.n * self.tile_size) // 2

    def play_place_sound(self):
        try:
            freq = 440
            arr = (np.sin(np.linspace(0, 2*np.pi*freq, 4410)) * 32767).astype(np.int16)
            sound = pygame.sndarray.make_sound(arr)
            sound.play()
        except Exception:
            pass

    def play_pass_sound(self):
        try:
            freq = 220
            arr = (np.sin(np.linspace(0, 2*np.pi*freq, 4410)) * 32767).astype(np.int16)
            sound = pygame.sndarray.make_sound(arr)
            sound.play()
        except Exception:
            pass

    def check_auto_pass(self):
        while not self.replay_mode and not self.gs.any_valid_move(self.gs.current_player):
            self.gs.pass_turn(self.gs.current_player)

    # ------------------------------------------------------------------
    def draw(self):
        surf = self.surface
        surf.fill((0,0,0))
        # Draw terrain
        for x in range(self.n):
            for y in range(self.n):
                h = float(self.gs.terrain[x, y])
                color = height_color(h)
                rect = pygame.Rect(
                    self.offset_x + y * self.tile_size,
                    self.offset_y + x * self.tile_size,
                    self.tile_size - MARGIN,
                    self.tile_size - MARGIN,
                )
                pygame.draw.rect(surf, color, rect)

        # Influence
        if self.show_influence:
            mask = pygame.Surface(
                (self.n * self.tile_size, self.n * self.tile_size), pygame.SRCALPHA
            )
            for f in self.gs.forts:
                cx = self.offset_x + f['y'] * self.tile_size + self.tile_size // 2
                cy = self.offset_y + f['x'] * self.tile_size + self.tile_size // 2
                color = (255,0,0,60) if f['player']==0 else (0,0,255,60)
                pygame.draw.circle(mask, color, (cx, cy), self.gs.k * self.tile_size, 0)
            surf.blit(mask, (0,0))

        # Draw forts
        for f in self.gs.forts:
            cx = self.offset_x + f['y'] * self.tile_size + self.tile_size // 2
            cy = self.offset_y + f['x'] * self.tile_size + self.tile_size // 2
            color = (255,0,0) if f['player']==0 else (0,0,255)
            pygame.draw.circle(surf, (0,0,0), (cx, cy), self.tile_size // 2 - 2)
            pygame.draw.circle(surf, color, (cx, cy), self.tile_size // 2 - 4)
            # lines to adjacent forts of same player
            for other in self.gs.forts:
                if other is f or other['player'] != f['player']:
                    continue
                if self.gs.distance2(f['x'], f['y'], other['x'], other['y']) <= 1:
                    ox = self.offset_x + other['y'] * self.tile_size + self.tile_size // 2
                    oy = self.offset_y + other['x'] * self.tile_size + self.tile_size // 2
                    pygame.draw.line(surf, color, (cx, cy), (ox, oy), 2)

        # Highlight current player
        border = pygame.Rect(self.offset_x, self.offset_y, self.n * self.tile_size, self.n * self.tile_size)
        border_color = (255,0,0) if self.gs.current_player==0 else (0,0,255)
        pygame.draw.rect(surf, border_color, border, 3)

        # UI bar
        bar = pygame.Rect(self.offset_x, self.offset_y + self.n * self.tile_size, self.n * self.tile_size, 60)
        pygame.draw.rect(surf, (40,40,40), bar)
        # Checkbox influence
        cb_rect = pygame.Rect(self.offset_x + 10, self.offset_y + self.n * self.tile_size + 20, CHECKBOX_SIZE, CHECKBOX_SIZE)
        pygame.draw.rect(surf, (255,255,255), cb_rect, 2)
        if self.show_influence:
            pygame.draw.line(surf, (255,255,255), cb_rect.topleft, cb_rect.bottomright, 2)
            pygame.draw.line(surf, (255,255,255), cb_rect.topright, cb_rect.bottomleft, 2)
        label = self.font.render('Mostra influenza (I)', True, (200,200,200))
        surf.blit(label, (cb_rect.right + 8, cb_rect.top - 4))

        # Credits + scores
        txt = f'P0 Crediti: {self.gs.credits[0]:4d}  Score: {self.gs.scores[0]:.2f}   |   P1 Crediti: {self.gs.credits[1]:4d}  Score: {self.gs.scores[1]:.2f}'
        info = self.font.render(txt, True, (220,220,220))
        surf.blit(
            info,
            (
                self.offset_x + self.n * self.tile_size // 2 - info.get_width() // 2,
                self.offset_y + self.n * self.tile_size + 2,
            ),
        )

        # Hover info
        mx, my = pygame.mouse.get_pos()
        grid_x = (my - self.offset_y) // self.tile_size
        grid_y = (mx - self.offset_x) // self.tile_size
        hovered_height = None
        if 0 <= grid_x < self.n and 0 <= grid_y < self.n:
            hovered_height = float(self.gs.terrain[grid_x, grid_y])
        for f in self.gs.forts:
            if f['x'] == grid_x and f['y'] == grid_y:
                prod = self.gs.production(f['height'])
                if self.gs._adjacent_bonus(f) > 1.0:
                    prod = int(prod * 1.5)
                lines = [
                    f"Player: {f['player']}",
                    f"Coordinate: ({f['x']},{f['y']})",
                    f"Height: {f['height']:.2f}",
                    f"Prod/turn: {prod}",
                ]
                self.draw_tooltip(lines, mx, my)
                break
        else:
            if hovered_height is not None:
                prod = self.gs.production(hovered_height)
                lines = [
                    f"Coordinate: ({grid_x},{grid_y})",
                    f"Height: {hovered_height:.2f}",
                    f"Prod/turn: {prod}",
                ]
                self.draw_tooltip(lines, mx, my)

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

    def menu_loop(self):
        files = sorted(glob.glob('fortwars_*.json'))
        running = True
        while running:
            self.surface.fill((0, 0, 0))
            lines = ['N - Nuova partita'] + [f'{i+1} - {os.path.basename(f)}' for i, f in enumerate(files)]
            for i, text in enumerate(lines):
                label = self.font.render(text, True, (255, 255, 255))
                self.surface.blit(label, (40, 40 + i * 30))
            pygame.display.flip()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit(); sys.exit()
                    if event.unicode.lower() == 'n':
                        running = False
                        break
                    if event.unicode.isdigit():
                        idx = int(event.unicode) - 1
                        if 0 <= idx < len(files):
                            self.replay_mode = True
                            self.gs = load_game(files[idx])
                            self.replay_actions = iter(self.gs.history)
                            self.paused = True
                            running = False
                            break
            self.clock.tick(30)

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
            if event.type == pygame.VIDEORESIZE:
                self.surface = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                self.update_layout(event.w, event.h)
            if event.type == pygame.MOUSEBUTTONDOWN and not self.replay_mode:
                mx, my = event.pos
                if event.button == 1:
                    x = (my - self.offset_y) // self.tile_size
                    y = (mx - self.offset_x) // self.tile_size
                    if self.gs.place_fort(self.gs.current_player, x, y):
                        self.play_place_sound()
                        self.check_auto_pass()
                if event.button == 3:
                    self.gs.pass_turn(self.gs.current_player)
                    self.play_pass_sound()
                    self.check_auto_pass()
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
            self.play_pass_sound()
            self.check_auto_pass()
        # Place fort with mouse + Enter shortcut
        if event.key == pygame.K_RETURN:
            mx, my = pygame.mouse.get_pos()
            x = (my - self.offset_y) // self.tile_size
            y = (mx - self.offset_x) // self.tile_size
            if self.gs.place_fort(self.gs.current_player, x, y):
                self.play_place_sound()
                self.check_auto_pass()

    def save_current_game(self):
        now = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'fortwars_{now}.json'
        save_path = os.path.join(os.getcwd(), filename)
        save_game(self.gs, save_path)
        print(f'Saved game to {save_path}')

def main():
    parser = argparse.ArgumentParser(description='Fort Wars GUI')
    parser.add_argument('--n', type=int, default=18)
    parser.add_argument('--k', type=int, default=2)
    parser.add_argument('--replay', type=str, help='Path JSON saved game')
    args = parser.parse_args()
    FortWarsGUI(n=args.n, k=args.k, replay_path=args.replay)

if __name__ == '__main__':
    main()
