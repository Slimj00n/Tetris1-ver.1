import pygame
import random
import sys
import copy
import time

# --- 초기화 및 설정 ---
pygame.init()
pygame.display.set_caption("Tetris1 - Ultimate Masterpiece")

# 폰트 설정
try:
    FONT_LOGO = pygame.font.SysFont("arial black", 60, bold=True) # 로고용 폰트
    FONT_SCORE = pygame.font.SysFont("arial", 22, bold=True)
    FONT_UI = pygame.font.SysFont("arial", 18, bold=True)
    FONT_BIG = pygame.font.SysFont("arial", 35, bold=True)
except:
    FONT_LOGO = pygame.font.SysFont(None, 80, bold=True)
    FONT_SCORE = pygame.font.SysFont(None, 25)
    FONT_UI = pygame.font.SysFont(None, 20)
    FONT_BIG = pygame.font.SysFont(None, 40)

# 상수 설정
BLOCK_SIZE = 30
GRID_WIDTH = 10
GRID_HEIGHT = 20
COLOR_BACKGROUND = (20, 20, 25)
COLOR_GRID = (40, 40, 45)
COLOR_UI_BG = (35, 35, 40)
COLOR_TEXT = (255, 255, 255)
COLORS = [(0, 0, 0), (0, 240, 240), (240, 240, 0), (160, 0, 240), (0, 240, 0), (240, 0, 0), (0, 0, 240), (240, 160, 0)]

GAME_WIDTH = GRID_WIDTH * BLOCK_SIZE
UI_WIDTH = 180
SCREEN_WIDTH = GAME_WIDTH + UI_WIDTH
SCREEN_HEIGHT = GRID_HEIGHT * BLOCK_SIZE + 60
PLAY_AREA_Y = 60

SHAPES = [
    [[1, 1, 1, 1]], [[1, 1], [1, 1]], [[0, 1, 0], [1, 1, 1]],
    [[0, 1, 1], [1, 1, 0]], [[1, 1, 0], [0, 1, 1]], [[1, 0, 0], [1, 1, 1]], [[0, 0, 1], [1, 1, 1]]
]

class Tetris:
    def __init__(self):
        self.grid = [[0 for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        self.game_over = False
        self.game_started = False
        self.score = 0
        self.next_pieces = [self.new_piece_data() for _ in range(3)]
        self.current_piece = self.spawn_piece()
        self.lock_delay_timer = 0
        self.LOCK_DELAY_MAX = 500
        self.lock_reset_count = 0
        self.LOCK_RESET_LIMIT = 15
        self.was_on_ground = False
        self.start_time = time.time() # 로고 깜빡임용

    def new_piece_data(self):
        shape_id = random.randint(0, len(SHAPES) - 1)
        return {'shape': SHAPES[shape_id], 'color': shape_id + 1}

    def spawn_piece(self):
        next_data = self.next_pieces.pop(0)
        self.next_pieces.append(self.new_piece_data())
        p = {'shape': next_data['shape'], 'color': next_data['color'], 
             'x': GRID_WIDTH // 2 - len(next_data['shape'][0]) // 2, 'y': -2}
        self.lock_reset_count = 0
        self.was_on_ground = False
        if not self.valid_move(p, p['x'], p['y']): self.game_over = True
        return p

    def valid_move(self, piece, x, y):
        for ry, row in enumerate(piece['shape']):
            for rx, cell in enumerate(row):
                if cell:
                    nx, ny = x + rx, y + ry
                    if nx < 0 or nx >= GRID_WIDTH or ny >= GRID_HEIGHT: return False
                    if ny >= 0 and self.grid[ny][nx]: return False
        return True

    def rotate_piece(self):
        test_piece = copy.deepcopy(self.current_piece)
        test_piece['shape'] = [list(row) for row in zip(*test_piece['shape'][::-1])]
        kicks = [(0, 0), (-1, 0), (1, 0), (0, -1)]
        for dx, dy in kicks:
            if self.valid_move(test_piece, test_piece['x'] + dx, test_piece['y'] + dy):
                self.current_piece['shape'] = test_piece['shape']
                self.current_piece['x'] += dx
                self.current_piece['y'] += dy
                if not self.valid_move(self.current_piece, self.current_piece['x'], self.current_piece['y'] + 1):
                    if self.lock_reset_count < self.LOCK_RESET_LIMIT:
                        self.lock_delay_timer = 0
                        self.lock_reset_count += 1
                return True
        return False

    def freeze(self):
        for ry, row in enumerate(self.current_piece['shape']):
            for rx, cell in enumerate(row):
                if cell:
                    x, y = self.current_piece['x'] + rx, self.current_piece['y'] + ry
                    if y >= 0: self.grid[y][x] = self.current_piece['color']
                    else: self.game_over = True
        self.clear_lines()
        if not self.game_over: self.current_piece = self.spawn_piece()
        self.lock_delay_timer = 0

    def clear_lines(self):
        new_grid = [row for row in self.grid if not all(cell != 0 for cell in row)]
        lines = GRID_HEIGHT - len(new_grid)
        if lines > 0:
            self.score += 50 * lines
            for _ in range(lines): new_grid.insert(0, [0 for _ in range(GRID_WIDTH)])
            self.grid = new_grid

    def get_current_speed(self):
        # 🔴 [마지막 디테일 1번]: 500점마다 난이도 상승 (가파른 곡선)
        current_velocity = 1.2 + (self.score // 500 * 0.1)
        interval = 1000 / current_velocity
        return max(100, int(interval))

def draw_block(screen, x, y, color_id, size=BLOCK_SIZE, alpha=255):
    if color_id == 0: return
    color = list(COLORS[color_id])
    if alpha < 255:
        # 투명도 적용 (메뉴용)
        pygame.draw.rect(screen, color + [alpha], (x, y, size, size))
        pygame.draw.rect(screen, (255, 255, 255, alpha), (x, y, size, size), 1)
    else:
        pygame.draw.rect(screen, color, (x, y, size, size))
        pygame.draw.rect(screen, (255, 255, 255), (x, y, size, size), 1)

def main():
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    clock = pygame.time.Clock()
    game = Tetris()
    drop_time, left_timer, right_timer, soft_drop_timer = 0, 0, 0, 0
    
    # 🔴 [마지막 디테일 2번]: 조작 속도 하향 (묵직한 느낌)
    KEY_DELAY = 220     # DAS (첫 이동 지연)
    KEY_INTERVAL = 60   # ARR (연속 이동 간격)
    SOFT_DROP_INTERVAL = 80 # 소프트 드롭 간격

    while True:
        dt = clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if not game.game_started:
                    if event.key in [pygame.K_SPACE, pygame.K_RETURN]: game.game_started = True
                elif game.game_over:
                    if event.key == pygame.K_SPACE: return True
                else:
                    if event.key == pygame.K_UP: game.rotate_piece()
                    if event.key == pygame.K_SPACE: 
                        while game.valid_move(game.current_piece, game.current_piece['x'], game.current_piece['y'] + 1):
                            game.current_piece['y'] += 1
                        game.score += 10
                        game.freeze()
                        drop_time = 0

        if game.game_started and not game.game_over:
            fall_speed = game.get_current_speed()
            can_move_down = game.valid_move(game.current_piece, game.current_piece['x'], game.current_piece['y'] + 1)
            if not can_move_down:
                if not game.was_on_ground: game.lock_reset_count, game.was_on_ground = 0, True
                game.lock_delay_timer += dt
                if game.lock_delay_timer >= game.LOCK_DELAY_MAX: game.freeze()
            else:
                game.was_on_ground, drop_time = False, drop_time + dt
                if drop_time > fall_speed:
                    game.current_piece['y'] += 1
                    drop_time, game.lock_delay_timer = 0, 0

            # --- 좌우 이동 (조작 속도 제한 적용) ---
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT]:
                if left_timer <= 0:
                    if game.valid_move(game.current_piece, game.current_piece['x'] - 1, game.current_piece['y']): game.current_piece['x'] -= 1
                    left_timer = KEY_DELAY if left_timer == 0 else KEY_INTERVAL
                else: left_timer -= dt
            else: left_timer = 0
            
            if keys[pygame.K_RIGHT]:
                if right_timer <= 0:
                    if game.valid_move(game.current_piece, game.current_piece['x'] + 1, game.current_piece['y']): game.current_piece['x'] += 1
                    right_timer = KEY_DELAY if right_timer == 0 else KEY_INTERVAL
                else: right_timer -= dt
            else: right_timer = 0
            
            # --- 아래 이동 (소프트 드롭 속도 제한 적용) ---
            if keys[pygame.K_DOWN]:
                soft_drop_timer += dt
                if soft_drop_timer >= SOFT_DROP_INTERVAL:
                    if game.valid_move(game.current_piece, game.current_piece['x'], game.current_piece['y'] + 1):
                        game.current_piece['y'] += 1
                        drop_time = 0
                    soft_drop_timer = 0
            else: soft_drop_timer = 0

        # --- 그리기 ---
        screen.fill(COLOR_BACKGROUND)
        pygame.draw.rect(screen, COLOR_UI_BG, (0, 0, SCREEN_WIDTH, PLAY_AREA_Y))
        score_txt = FONT_SCORE.render(f"SCORE: {game.score}", True, COLOR_TEXT)
        speed_txt = FONT_SCORE.render(f"INTERVAL: {game.get_current_speed()}ms", True, (0, 255, 150))
        screen.blit(score_txt, (20, 15)); screen.blit(speed_txt, (GAME_WIDTH - 150, 15))

        # 게임 격자 및 쌓인 블록
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                pygame.draw.rect(screen, COLOR_GRID, (x * BLOCK_SIZE, PLAY_AREA_Y + y * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE), 1)
                if game.grid[y][x]: draw_block(screen, x * BLOCK_SIZE, PLAY_AREA_Y + y * BLOCK_SIZE, game.grid[y][x])
        
        # 현재 블록
        if game.game_started and not game.game_over:
            for ry, row in enumerate(game.current_piece['shape']):
                for rx, cell in enumerate(row):
                    if cell:
                        draw_y = PLAY_AREA_Y + (game.current_piece['y'] + ry) * BLOCK_SIZE
                        if draw_y >= PLAY_AREA_Y: draw_block(screen, (game.current_piece['x'] + rx) * BLOCK_SIZE, draw_y, game.current_piece['color'])

        # UI 영역
        pygame.draw.rect(screen, COLOR_UI_BG, (GAME_WIDTH, PLAY_AREA_Y, UI_WIDTH, SCREEN_HEIGHT - PLAY_AREA_Y))
        next_lbl = FONT_UI.render("NEXT BLOCKS", True, COLOR_TEXT); screen.blit(next_lbl, (GAME_WIDTH + 20, PLAY_AREA_Y + 20))
        for i, piece in enumerate(game.next_pieces):
            for ry, row in enumerate(piece['shape']):
                for rx, cell in enumerate(row):
                    if cell: draw_block(screen, GAME_WIDTH + 45 + rx * 18, PLAY_AREA_Y + 70 + (i * 90) + ry * 18, piece['color'], 18)

        # 🔴 [마지막 디테일 3번]: 초기 메뉴 화면 로고 추가
        if not game.game_started:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA); overlay.fill((0, 0, 0, 220)); screen.blit(overlay, (0, 0))
            
            # Tetris1 로고 (HTML 스타일)
            logo_text = FONT_LOGO.render("Tetris1", True, (0, 150, 255))
            logo_rect = logo_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 60))
            
            # 부드러운 깜빡임 효과
            if int(time.time() * 2) % 2 == 0:
                screen.blit(logo_text, logo_rect)
            
            # 시작 버튼 느낌
            pygame.draw.rect(screen, (0, 120, 215), (SCREEN_WIDTH//2 - 120, SCREEN_HEIGHT//2 + 30, 240, 60), border_radius=12)
            pygame.draw.rect(screen, (255, 255, 255), (SCREEN_WIDTH//2 - 120, SCREEN_HEIGHT//2 + 30, 240, 60), 2, border_radius=12)
            start_txt = FONT_BIG.render("PRESS SPACE", True, (255, 255, 255)); screen.blit(start_txt, (SCREEN_WIDTH//2 - start_txt.get_width()//2, SCREEN_HEIGHT//2 + 42))
            
        if game.game_over:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA); overlay.fill((200, 0, 0, 150)); screen.blit(overlay, (0, 0))
            over_txt = FONT_BIG.render("GAME OVER", True, COLOR_TEXT); screen.blit(over_txt, (SCREEN_WIDTH//2 - over_txt.get_width()//2, SCREEN_HEIGHT//2 - 20))
        pygame.display.flip()

if __name__ == "__main__":
    while main(): pass