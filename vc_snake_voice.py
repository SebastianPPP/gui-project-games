import pygame
import time
import random
import threading
import pyaudio
import numpy as np
import csv
import speech_recognition as sr
from ctypes import *

try:
    ERROR_HANDLER_FUNC = CFUNCTYPE(None, c_char_p, c_int, c_char_p, c_int, c_char_p)
    def py_error_handler(filename, line, function, err, fmt): pass
    c_error_handler = ERROR_HANDLER_FUNC(py_error_handler)
    asound = cdll.LoadLibrary('libasound.so')
    asound.snd_lib_error_set_handler(c_error_handler)
except: pass

WINDOW_WIDTH = 850
WINDOW_HEIGHT = 600
SCORE_FILE = "scoreboard.csv"

BLACK = (15, 15, 25)
WHITE = (255, 255, 255)
GREEN = (50, 255, 50)
NEON_BLUE = (50, 150, 255)
NEON_YELLOW = (255, 255, 50)
GRAY = (100, 100, 100)
RED = (255, 50, 50)

CHUNK_SIZE = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RECORD_SECONDS = 1.5 

# Globalne
running = True
current_player_name = "Gracz"
direction = 'RIGHT'
change_to = direction
snake_paused_for_voice = False  # Flaga pauzy

def open_audio_stream(p, dev_index, input=True):
    rates_to_try = [44100, 48000, 16000] if input else [44100]
    if dev_index is not None:
        try: dev_index = int(dev_index)
        except: dev_index = None

    for r in rates_to_try:
        try:
            stream = p.open(format=FORMAT, channels=CHANNELS, rate=r, 
                            input=input, output=not input,
                            input_device_index=dev_index if input else None, 
                            frames_per_buffer=CHUNK_SIZE)
            return stream, r
        except Exception: continue
    return None, 44100

def save_score_to_csv(score):
    try:
        with open(SCORE_FILE, mode='a', newline='', encoding='utf-8') as f:
            csv.writer(f).writerow(["snake_voice", current_player_name, score])
    except: pass

def recognize_speech(audio_bytes, rate):
    r = sr.Recognizer()
    try:
        audio_data = sr.AudioData(audio_bytes, rate, 2) # 2 = sample_width (16-bit)
        
        # Rozpoznawanie (Język POLSKI)
        text = r.recognize_google(audio_data, language="pl-PL").lower()
        print(f"Google usłyszał: '{text}'")
        return text
    except sr.UnknownValueError:
        print("Google: Nie zrozumiano")
    except sr.RequestError:
        print("Google: Błąd połączenia")
    except Exception as e:
        print(f"Błąd rozpoznawania: {e}")
    return None

def game_audio_thread(p, mic_id, rate):
    global running, change_to, snake_paused_for_voice
    
    stream, valid_rate = open_audio_stream(p, mic_id, input=True)
    if not stream:
        print("Błąd mikrofonu w grze")
        return

    noise_level = 500
    temp = []
    print("Kalibracja szumu...")
    for _ in range(20):
        try:
            d = np.frombuffer(stream.read(CHUNK_SIZE, exception_on_overflow=False), dtype=np.int16)
            temp.append(np.abs(d).mean())
        except: pass
    if temp: noise_level = max(np.mean(temp) * 2.5, 600)
    print(f"Próg szumu: {noise_level:.0f}")

    while running:
        if snake_paused_for_voice:
            frames = []
            try: stream.read(stream.get_read_available(), exception_on_overflow=False)
            except: pass
            
            for _ in range(0, int(valid_rate / CHUNK_SIZE * RECORD_SECONDS)):
                try:
                    data = stream.read(CHUNK_SIZE, exception_on_overflow=False)
                    frames.append(data)
                except: pass
            
            full_audio = b''.join(frames)
            
            text = recognize_speech(full_audio, valid_rate)
            
            if text:
                if "gór" in text or "gura" in text: change_to = 'UP'
                elif "dół" in text or "doł" in text: change_to = 'DOWN'
                elif "lew" in text: change_to = 'LEFT'
                elif "praw" in text: change_to = 'RIGHT'
            
            snake_paused_for_voice = False
            
        else:
            try:
                data = stream.read(CHUNK_SIZE, exception_on_overflow=False)
                vol = np.abs(np.frombuffer(data, dtype=np.int16)).mean()
                
                if vol > noise_level:
                    print(f"Wykryto głos ({vol:.0f}) -> PAUZA i SŁUCHANIE")
                    snake_paused_for_voice = True
            except: pass

    stream.close()

def show_config_screen(screen):
    clock = pygame.time.Clock()
    font = pygame.font.SysFont('arial', 24)
    player_name = "Gracz"
    
    p = pyaudio.PyAudio()
    mics = []
    try:
        for i in range(p.get_device_count()):
            try:
                info = p.get_device_info_by_index(i)
                if info['maxInputChannels'] > 0:
                    mics.append(f"{i}: {info['name'][:25]}")
            except: pass
    except: pass
    if not mics: mics = ["Brak mikrofonu"]
    sel_idx = 0
    
    def get_mic_id():
        try: return int(mics[sel_idx].split(':')[0])
        except: return None

    stream, rate = open_audio_stream(p, get_mic_id())

    while True:
        screen.fill(BLACK)
        pygame.draw.rect(screen, (30,30,40), (50,50,750,500), border_radius=10)
        pygame.draw.rect(screen, NEON_BLUE, (50,50,750,500), 2, border_radius=10)
        
        screen.blit(font.render("KONFIGURACJA GŁOSU", True, WHITE), (320, 70))
        screen.blit(font.render(f"1. Gracz: {player_name}", True, WHITE), (100, 130))
        screen.blit(font.render(f"2. Mikrofon: < {mics[sel_idx]} >", True, GREEN), (100, 180))
        
        bar_w = 0
        if stream and stream.is_active():
            try:
                data = np.frombuffer(stream.read(CHUNK_SIZE, exception_on_overflow=False), dtype=np.int16)
                vol = np.abs(data).mean()
                bar_w = min(200, int(vol / 10))
            except: pass
        
        pygame.draw.rect(screen, GRAY, (300, 220, 200, 20))
        pygame.draw.rect(screen, GREEN, (300, 220, bar_w, 20))
        screen.blit(font.render("Test Mikrofonu", True, GRAY), (300, 250))

        pygame.draw.rect(screen, NEON_BLUE, (250, 450, 350, 60), border_radius=5)
        st = font.render("GRAJ (ENTER)", True, WHITE)
        screen.blit(st, (425 - st.get_width()//2, 480 - st.get_height()//2))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if stream: stream.close(); p.terminate()
                return None, None, None
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if stream: stream.close(); p.terminate()
                    return None, None, None
                if event.key == pygame.K_BACKSPACE: player_name = player_name[:-1]
                elif len(player_name) < 12 and event.unicode.isalnum(): player_name += event.unicode
                
                if event.key in [pygame.K_RIGHT, pygame.K_LEFT]:
                    if stream: stream.close()
                    if event.key == pygame.K_RIGHT: sel_idx = (sel_idx + 1) % len(mics)
                    else: sel_idx = (sel_idx - 1) % len(mics)
                    stream, rate = open_audio_stream(p, get_mic_id())

                if event.key == pygame.K_RETURN:
                    if stream: stream.close()
                    p.terminate()
                    return player_name, get_mic_id(), rate
        clock.tick(30)

def run_game():
    global direction, change_to, score, food_spawn, snake_pos, snake_body, food_pos, running, current_player_name, snake_paused_for_voice
    
    pygame.init()
    win = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    
    res = show_config_screen(win)
    if not res: return
    current_player_name, mic_id, best_rate = res

    snake_pos = [100, 50]
    snake_body = [[100, 50], [90, 50], [80, 50]]
    food_pos = [200, 200]
    direction = 'RIGHT'
    change_to = direction
    score = 0
    running = True
    snake_paused_for_voice = False

    p_game = pyaudio.PyAudio()
    t = threading.Thread(target=game_audio_thread, args=(p_game, mic_id, best_rate), daemon=True)
    t.start()
    
    clk = pygame.time.Clock()
    font_instr = pygame.font.SysFont('arial', 20)
    font_status = pygame.font.SysFont('arial', 40, bold=True)
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: running = False
                if event.key == pygame.K_UP: change_to = 'UP'
                if event.key == pygame.K_DOWN: change_to = 'DOWN'
                if event.key == pygame.K_LEFT: change_to = 'LEFT'
                if event.key == pygame.K_RIGHT: change_to = 'RIGHT'

        if not snake_paused_for_voice:
            if change_to == 'UP' and direction != 'DOWN': direction = 'UP'
            if change_to == 'DOWN' and direction != 'UP': direction = 'DOWN'
            if change_to == 'LEFT' and direction != 'RIGHT': direction = 'LEFT'
            if change_to == 'RIGHT' and direction != 'LEFT': direction = 'RIGHT'

            if direction == 'UP': snake_pos[1] -= 10
            elif direction == 'DOWN': snake_pos[1] += 10
            elif direction == 'LEFT': snake_pos[0] -= 10
            elif direction == 'RIGHT': snake_pos[0] += 10

            snake_body.insert(0, list(snake_pos))
            if snake_pos == food_pos:
                score += 10
                food_pos = [random.randrange(1, WINDOW_WIDTH//10)*10, random.randrange(1, WINDOW_HEIGHT//10)*10]
            else: snake_body.pop()

            if (snake_pos[0] < 0 or snake_pos[0] > WINDOW_WIDTH or snake_pos[1] < 0 or snake_pos[1] > WINDOW_HEIGHT or any(snake_pos == b for b in snake_body[1:])):
                save_score_to_csv(score)
                running = False
                win.fill(BLACK)
                go = pygame.font.SysFont('arial', 50).render("GAME OVER", True, RED)
                win.blit(go, (WINDOW_WIDTH//2-100, WINDOW_HEIGHT//2))
                pygame.display.flip()
                time.sleep(2)

        win.fill(BLACK)
        
        if snake_paused_for_voice:
            ov = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
            ov.set_alpha(150)
            ov.fill((0,0,50))
            win.blit(ov, (0,0))
            
            st_txt = font_status.render("SŁUCHAM...", True, NEON_YELLOW)
            win.blit(st_txt, (WINDOW_WIDTH//2 - st_txt.get_width()//2, WINDOW_HEIGHT//2))
            
            hint = font_instr.render("(Powiedz: góra, dół, lewo, prawo)", True, WHITE)
            win.blit(hint, (WINDOW_WIDTH//2 - hint.get_width()//2, WINDOW_HEIGHT//2 + 50))
        else:
            msg = font_instr.render("Krzyknij, aby wydać komendę!", True, GRAY)
            win.blit(msg, (10, WINDOW_HEIGHT - 30))
        
        for pos in snake_body: pygame.draw.rect(win, GREEN, pygame.Rect(pos[0], pos[1], 10, 10))
        pygame.draw.rect(win, WHITE, pygame.Rect(food_pos[0], food_pos[1], 10, 10))
        
        sc_txt = font_instr.render(f"Wynik: {score}", True, WHITE)
        win.blit(sc_txt, (10, 10))

        pygame.display.update()
        clk.tick(10)
    
    p_game.terminate()

if __name__ == '__main__':
    run_game()