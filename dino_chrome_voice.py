import pygame
import random
import sys
import threading
import time
import pyaudio
import numpy as np
import csv

SCREEN_WIDTH = 850
SCREEN_HEIGHT = 600
FPS = 30
GRAVITY = 1
GROUND_LEVEL = 450
JUMP_VELOCITY = 17
SCORE_FILE = "scoreboard.csv"

CHUNK_SIZE = 1024
AMPLITUDE_THRESHOLD = 2000 # Próg głośności skoku

WHITE = (255, 255, 255)
BLACK = (15, 15, 25)
NEON_GREEN = (50, 255, 50)
NEON_BLUE = (50, 150, 255)
RED = (255, 50, 50)
GRAY = (100, 100, 100)
BACKGROUND_COLOR = (240, 240, 240)
SCORE_COLOR = (83, 83, 83)

voice_jump_flag = False
audio_running = False
current_player_name = "Gracz"
selected_rate = 44100 

def save_score_to_csv(score):
    try:
        with open(SCORE_FILE, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["dino_voice", current_player_name, score])
    except Exception as e:
        print(f"Błąd zapisu: {e}")

def open_audio_stream(p, dev_index):
    rates_to_try = [44100, 48000, 16000, 32000]
    for r in rates_to_try:
        try:
            stream = p.open(format=pyaudio.paInt16, 
                            channels=1, 
                            rate=r, 
                            input=True, 
                            input_device_index=dev_index, 
                            frames_per_buffer=CHUNK_SIZE)
            print(f"Sukces audio: Urządzenie {dev_index} @ {r}Hz")
            return stream, r
        except Exception:
            continue
    print(f"Nie udało się otworzyć audio dla urządzenia {dev_index}")
    return None, 44100

def voice_control_dino(mic_index):
    global voice_jump_flag, audio_running
    
    p = pyaudio.PyAudio()
    stream, used_rate = open_audio_stream(p, mic_index)
    
    if stream is None:
        print("Błąd krytyczny audio - sterowanie głosem nieaktywne.")
        p.terminate()
        return

    try:
        while audio_running:
            try:
                data = stream.read(CHUNK_SIZE, exception_on_overflow=False)
                data_int = np.frombuffer(data, dtype=np.int16)
                
                peak = np.max(np.abs(data_int))
                
                if peak > AMPLITUDE_THRESHOLD:
                    voice_jump_flag = True
                    time.sleep(0.15) 
            except IOError:
                pass
            
    except Exception as e:
        print(f"Błąd wątku audio: {e}")
    finally:
        if stream: 
            stream.stop_stream()
            stream.close()
        p.terminate()

def show_config_screen(screen):
    clock = pygame.time.Clock()
    font = pygame.font.SysFont('arial', 24)
    font_title = pygame.font.SysFont('arial', 40, bold=True)
    font_small = pygame.font.SysFont('arial', 16)
    
    player_name = "Gracz Dino"
    input_active = True
    
    p = pyaudio.PyAudio()
    mics = []
    
    try:
        count = p.get_device_count()
        for i in range(count):
            try:
                info = p.get_device_info_by_index(i)
                if info['maxInputChannels'] > 0:
                    name = info['name']
                    mics.append(f"{i}: {name[:30]}")
            except: pass
    except: pass
        
    if not mics: mics = ["Brak mikrofonu"]
    sel_idx = 0
    
    def get_mic_id():
        try: return int(mics[sel_idx].split(':')[0])
        except: return None

    stream = None
    stream, _ = open_audio_stream(p, get_mic_id())

    error_msg = ""

    while True:
        screen.fill(BLACK)
        
        pygame.draw.rect(screen, (30, 30, 40), (100, 50, 650, 500), border_radius=10)
        pygame.draw.rect(screen, NEON_BLUE, (100, 50, 650, 500), 2, border_radius=10)
        
        title = font_title.render("KONFIGURACJA: DINO GŁOS", True, WHITE)
        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 70))
        
        screen.blit(font.render("Nazwa Gracza:", True, GRAY), (150, 150))
        pygame.draw.rect(screen, NEON_BLUE if input_active else GRAY, (150, 180, 300, 40), 2)
        screen.blit(font.render(player_name, True, WHITE), (160, 190))
        
        screen.blit(font.render("Mikrofon (Strzałki L/P):", True, GRAY), (150, 250))
        screen.blit(font.render(f"< {mics[sel_idx]} >", True, NEON_GREEN), (150, 280))
        
        screen.blit(font.render("Test (Klaśnij!):", True, GRAY), (500, 150))
        pygame.draw.rect(screen, GRAY, (500, 180, 50, 200), 2)
        
        bar_drawn = False
        try:
            if stream and stream.is_active():
                try:
                    data = np.frombuffer(stream.read(CHUNK_SIZE, exception_on_overflow=False), dtype=np.int16)
                    vol = np.max(np.abs(data))
                    h = min(198, int(vol / 100))
                    
                    color = NEON_GREEN if h < (AMPLITUDE_THRESHOLD / 100) else RED
                    pygame.draw.rect(screen, color, (502, 378 - h, 46, h))
                    
                    thresh_y = 378 - int(AMPLITUDE_THRESHOLD / 100)
                    pygame.draw.line(screen, WHITE, (490, thresh_y), (560, thresh_y), 2)
                    bar_drawn = True
                except IOError: 
                    pass # Ignoruj błędy odczytu (buffer overflow)
        except OSError:
            stream = None
            error_msg = "Błąd podglądu audio"

        if not bar_drawn and error_msg:
            err_surf = font_small.render("Błąd Audio", True, RED)
            screen.blit(err_surf, (490, 390))

        btn_txt = font.render("GRAJ (Enter)", True, BLACK)
        btn_rect = pygame.Rect(SCREEN_WIDTH//2 - 100, 480, 200, 50)
        pygame.draw.rect(screen, NEON_GREEN, btn_rect, border_radius=5)
        screen.blit(btn_txt, (btn_rect.centerx - btn_txt.get_width()//2, btn_rect.centery - btn_txt.get_height()//2))
        
        esc = font.render("ESC - Wyjście", True, RED)
        screen.blit(esc, (120, 500))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if stream: stream.close()
                p.terminate()
                return None, None
                
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if stream: stream.close()
                    p.terminate()
                    return None, None
                    
                if event.key == pygame.K_RETURN:
                    if stream: stream.close()
                    p.terminate()
                    return player_name, get_mic_id()
                
                if input_active:
                    if event.key == pygame.K_BACKSPACE: 
                        player_name = player_name[:-1]
                    elif len(player_name) < 12 and event.unicode.isprintable(): 
                        player_name += event.unicode
                
                if event.key == pygame.K_RIGHT or event.key == pygame.K_LEFT:
                    if stream: 
                        stream.stop_stream()
                        stream.close()
                    
                    if event.key == pygame.K_RIGHT:
                        sel_idx = (sel_idx + 1) % len(mics)
                    else:
                        sel_idx = (sel_idx - 1) % len(mics)
                    
                    stream, _ = open_audio_stream(p, get_mic_id())
                    error_msg = "" if stream else "Nieudane otwarcie"
        
        clock.tick(30)

class Dino(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((40, 60))
        self.image.fill((80, 80, 80))
        self.rect = self.image.get_rect()
        self.rect.midbottom = (80, GROUND_LEVEL)
        self.y_velocity = 0
        self.is_jumping = False

    def update(self):
        if self.is_jumping:
            self.y_velocity += GRAVITY
            self.rect.y += self.y_velocity
            if self.rect.bottom >= GROUND_LEVEL:
                self.rect.bottom = GROUND_LEVEL
                self.is_jumping = False
                self.y_velocity = 0

    def jump(self):
        if not self.is_jumping:
            self.is_jumping = True
            self.y_velocity = -JUMP_VELOCITY

class Cactus(pygame.sprite.Sprite):
    def __init__(self, speed):
        super().__init__()
        height = random.choice([40, 60, 80])
        self.image = pygame.Surface((30, height))
        self.image.fill((0, 150, 0))
        self.rect = self.image.get_rect()
        self.rect.bottomright = (SCREEN_WIDTH, GROUND_LEVEL)
        self.speed = speed

    def update(self):
        self.rect.x -= self.speed
        if self.rect.right < 0:
            self.kill()

def run_dino_game():
    global voice_jump_flag, audio_running, current_player_name

    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Dino - Sterowanie Głosem")
    
    name, mic_id = show_config_screen(screen)
    if name is None: return # Anulowano w menu
    
    current_player_name = name

    dino = Dino()
    all_sprites = pygame.sprite.Group()
    cacti_group = pygame.sprite.Group()
    all_sprites.add(dino)

    game_active = True
    score = 0
    obstacle_speed = 6
    clock = pygame.time.Clock()

    SPAWN_CACTUS = pygame.USEREVENT + 1
    pygame.time.set_timer(SPAWN_CACTUS, 1500)

    voice_jump_flag = False
    audio_running = True
    
    thread = threading.Thread(target=voice_control_dino, args=(mic_id,), daemon=True)
    thread.start()

    while game_active:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game_active = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE: dino.jump() # Awaryjne sterowanie
                if event.key == pygame.K_ESCAPE: game_active = False
            
            if event.type == SPAWN_CACTUS:
                cacti_group.add(Cactus(obstacle_speed))
                all_sprites.add(cacti_group.sprites()[-1])

        if voice_jump_flag:
            dino.jump()
            voice_jump_flag = False

        if pygame.sprite.spritecollide(dino, cacti_group, False):
            save_score_to_csv(score)
            
            screen.fill(BACKGROUND_COLOR)
            font = pygame.font.SysFont('arial', 60, bold=True)
            screen.blit(font.render("GAME OVER", True, RED), (SCREEN_WIDTH//2 - 150, SCREEN_HEIGHT//2 - 50))
            
            sc_txt = pygame.font.SysFont('arial', 30).render(f"Wynik: {score}", True, SCORE_COLOR)
            screen.blit(sc_txt, (SCREEN_WIDTH//2 - 60, SCREEN_HEIGHT//2 + 20))
            
            pygame.display.flip()
            time.sleep(3)
            game_active = False
            break

        all_sprites.update()
        score += 1
        
        if score % 500 == 0:
            obstacle_speed += 0.5
            pygame.time.set_timer(SPAWN_CACTUS, max(600, 1500 - (score // 5)))

        screen.fill(BACKGROUND_COLOR)
        pygame.draw.line(screen, SCORE_COLOR, (0, GROUND_LEVEL), (SCREEN_WIDTH, GROUND_LEVEL), 2)
        all_sprites.draw(screen)
        
        sc_surf = pygame.font.SysFont('consolas', 24).render(f"Score: {score}", True, SCORE_COLOR)
        screen.blit(sc_surf, (SCREEN_WIDTH - 150, 20))
        
        pygame.display.flip()
        clock.tick(FPS)

    audio_running = False
    if thread.is_alive():
        thread.join(timeout=1.0)

if __name__ == '__main__':
    run_dino_game()