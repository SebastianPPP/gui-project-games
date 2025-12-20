import pygame
import sys
import math
import os
import csv
import vc_snake_video
import vc_snake_voice     
import dino_chrome_voice
import dino_chrome_video

WINDOW_WIDTH = 850
WINDOW_HEIGHT = 600
pygame.init()
menu_window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption('Menu główne')

WHITE = pygame.Color(255, 255, 255)
BLACK = pygame.Color(15, 15, 25)
NEON_CYAN = pygame.Color(0, 255, 255)
NEON_PINK = pygame.Color(255, 0, 150)
GRAY = pygame.Color(100, 100, 100)
DARK_PANEL = pygame.Color(30, 30, 40, 200)

try:
    font_title = pygame.font.Font("freesansbold.ttf", 46)
    font_btn = pygame.font.Font("freesansbold.ttf", 24)
    font_score_header = pygame.font.Font("freesansbold.ttf", 20)
    font_score = pygame.font.SysFont('consolas', 18) 
except:
    font_title = pygame.font.SysFont('arial', 46, bold=True)
    font_btn = pygame.font.SysFont('arial', 24)
    font_score_header = pygame.font.SysFont('arial', 20, bold=True)
    font_score = pygame.font.SysFont('courier new', 18)

GAME_KEYS = {
    0: "snake_video",
    1: "snake_voice",
    2: "dino_video",
    3: "dino_voice"
}

DISPLAY_NAMES = {
    0: "WYNIKI: SNAKE (WIDEO)",
    1: "WYNIKI: SNAKE (GŁOS)",
    2: "WYNIKI: DINO (WIDEO)",
    3: "WYNIKI: DINO (GŁOS)",
    4: "DO WIDZENIA!" 
}

SCORE_FILE = "scoreboard.csv"

def init_scoreboard():
    if not os.path.exists(SCORE_FILE):
        with open(SCORE_FILE, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(["Gra", "Gracz", "Wynik"]) 
        print("Utworzono scoreboard.csv")

def get_scores_for_game(game_key, limit=10):
    scores = []
    if os.path.exists(SCORE_FILE):
        try:
            with open(SCORE_FILE, mode='r', encoding='utf-8') as file:
                reader = csv.reader(file)
                next(reader, None) # Pomiń nagłówek
                for row in reader:
                    if len(row) >= 3 and row[0] == game_key:
                        try:
                            scores.append({'player': row[1], 'score': int(row[2])})
                        except ValueError:
                            continue 
            
            # Sortuj malejąco po wyniku
            scores.sort(key=lambda x: x['score'], reverse=True)
        except Exception as e:
            print(f"Błąd CSV: {e}")
    return scores[:limit]

def draw_fluid_background(surface, time):
    """Generuje animowane tło."""
    surface.fill(BLACK)
    for i in range(0, WINDOW_WIDTH, 20):
        y_pos = 300 + math.sin(i * 0.01 + time) * 100 + math.sin(i * 0.05 + time * 2) * 50
        
        color_val = max(0, min(255, int(abs(y_pos - 300) * 1.5)))
        line_color = (0, color_val // 2, color_val)
        
        pygame.draw.line(surface, line_color, (i, WINDOW_HEIGHT), (i, y_pos), 2)

def draw_menu_buttons(surface, options, selected_idx):
    start_x = 50
    start_y = 150
    
    for i, text in enumerate(options):
        btn_rect = pygame.Rect(start_x, start_y + i * 70, 300, 50)
        
        is_selected = (i == selected_idx)
        
        bg_color = (40, 40, 60) if not is_selected else (60, 60, 90)
        border_color = GRAY if not is_selected else NEON_PINK
        text_color = WHITE if is_selected else GRAY
        
        pygame.draw.rect(surface, bg_color, btn_rect, border_radius=8)
        pygame.draw.rect(surface, border_color, btn_rect, 2, border_radius=8)
        
        txt_surf = font_btn.render(text, True, text_color)
        txt_rect = txt_surf.get_rect(center=btn_rect.center)
        surface.blit(txt_surf, txt_rect)
        
        if is_selected:
            pts = [(start_x - 15, btn_rect.centery - 5), 
                   (start_x - 15, btn_rect.centery + 5), 
                   (start_x - 5, btn_rect.centery)]
            pygame.draw.polygon(surface, NEON_PINK, pts)

def draw_scoreboard(surface, game_idx):
    panel_rect = pygame.Rect(400, 150, 400, 400)
    
    s = pygame.Surface((panel_rect.width, panel_rect.height))
    s.set_alpha(180)
    s.fill((20, 20, 30))
    surface.blit(s, (panel_rect.x, panel_rect.y))
    
    pygame.draw.rect(surface, NEON_CYAN, panel_rect, 2, border_radius=8)
    
    header_text = DISPLAY_NAMES.get(game_idx, "WYNIKI")
    header_surf = font_score_header.render(header_text, True, NEON_CYAN)
    surface.blit(header_surf, (panel_rect.x + 20, panel_rect.y + 20))
    
    pygame.draw.line(surface, NEON_CYAN, (panel_rect.x + 20, panel_rect.y + 50), 
                     (panel_rect.right - 20, panel_rect.y + 50), 1)

    if game_idx == 4:
        msg = font_score.render("Do zobaczenia!", True, WHITE)
        surface.blit(msg, (panel_rect.x + 20, panel_rect.y + 70))
        return

    game_key = GAME_KEYS.get(game_idx, "unknown")
    scores = get_scores_for_game(game_key)
    
    start_y = panel_rect.y + 70
    if not scores:
        no_score = font_score.render("Brak wyników w bazie.", True, GRAY)
        surface.blit(no_score, (panel_rect.x + 20, start_y))
    else:
        
        for i, entry in enumerate(scores):
            player_name = entry['player'][:12] 
            score_line = f"{i+1}. {player_name:<12} | {entry['score']}"
            
            txt = font_score.render(score_line, True, WHITE)
            surface.blit(txt, (panel_rect.x + 20, start_y + i * 30))

def main_menu():
    init_scoreboard()
    
    options = [
        "1. Snake (Wideo)",
        "2. Snake (Głosowy)",
        "3. Dino (Wideo)",
        "4. Dino (Głosowy)",
        "Wyjście"
    ]
    
    selected_game = 0
    clock = pygame.time.Clock()
    time_counter = 0.0

    while True:
        time_counter += 0.05
        
        # 1. Rysowanie
        draw_fluid_background(menu_window, time_counter)
        
        # Tytuł
        title = font_title.render("CENTRUM GIER", True, WHITE)
        menu_window.blit(title, (50, 50))
        
        # Menu i Scoreboard
        draw_menu_buttons(menu_window, options, selected_game)
        draw_scoreboard(menu_window, selected_game)
        
        footer = font_score.render("Strzałki: Wybór | ENTER: Start", True, GRAY)
        menu_window.blit(footer, (50, WINDOW_HEIGHT - 30))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_DOWN:
                    selected_game = (selected_game + 1) % len(options)
                if event.key == pygame.K_UP:
                    selected_game = (selected_game - 1) % len(options)
                
                if event.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()
                
                if event.key == pygame.K_RETURN:
                    # Uruchamianie gier
                    if selected_game == 0: vc_snake_video.run_game()
                    elif selected_game == 1: vc_snake_voice.run_game()
                    elif selected_game == 2: dino_chrome_video.run_dino_camera_game()
                    elif selected_game == 3: dino_chrome_voice.run_dino_game()
                    elif selected_game == 4: pygame.quit(); sys.exit()
                
                if event.key == pygame.K_1: vc_snake_video.run_game()
                if event.key == pygame.K_2: vc_snake_voice.run_game()
                if event.key == pygame.K_3: dino_chrome_video.run_dino_camera_game()
                if event.key == pygame.K_4: dino_chrome_voice.run_dino_game()

        pygame.display.update()
        clock.tick(60)

if __name__ == '__main__':
    main_menu()