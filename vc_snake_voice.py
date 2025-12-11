import pygame
import time
import random
import speech_recognition as sr
import threading
import pyaudio
import numpy as np
import queue

# Sterowanie wątkami
running = True      # zatrzymuje VAD i SR po wyjściu z gry
audio_queue = queue.Queue()
paused = False

# game config
SNAKE_SPEED = 5
WINDOW_WIDTH = 720
WINDOW_HEIGHT = 480

# Kolory
BLACK = pygame.Color(0, 0, 0)
WHITE = pygame.Color(255, 255, 255)
RED = pygame.Color(255, 0, 0)
GREEN = pygame.Color(0, 255, 0)

# Initialize Pygame
pygame.init()
pygame.display.set_caption('Voice Controlled Snake')
game_window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))

fps_controller = pygame.time.Clock()

# game variables
snake_pos = [100, 50]
snake_body = [[100, 50], [90, 50], [80, 50]]
food_pos = [random.randrange(1, (WINDOW_WIDTH//10)) * 10,
            random.randrange(1, (WINDOW_HEIGHT//10)) * 10]
food_spawn = True

direction = 'RIGHT'
change_to = direction
score = 0


# ============================================================
#                   VAD LISTENER
# ============================================================
def vad_listener():
    global paused, running

    pa = pyaudio.PyAudio()
    RATE = 16000
    CHUNK = 1024

    stream = pa.open(format=pyaudio.paInt16,
                     channels=1,
                     rate=RATE,
                     input=True,
                     input_device_index=None,
                     frames_per_buffer=CHUNK)

    # Kalibracja szumu
    noise = []
    for _ in range(20):
        data = np.frombuffer(stream.read(CHUNK, exception_on_overflow=False), dtype=np.int16)
        noise.append(np.abs(data).mean())
        time.sleep(0.05)

    noise_level = np.mean(noise)
    THRESHOLD = noise_level * 15.0

    HOLD_TIME = 0.8
    POST_BUFFER = 0.3

    recording = False
    buffer_frames = []
    last_voice_time = 0

    while running:
        data = stream.read(CHUNK, exception_on_overflow=False)
        frame = np.frombuffer(data, dtype=np.int16)
        volume = np.abs(frame).mean()
        now = time.time()

        if volume > THRESHOLD:
            if not recording:
                paused = True
                recording = True

            last_voice_time = now
            buffer_frames.append(data)
            continue

        if recording and (now - last_voice_time > HOLD_TIME):
            extra_chunks = int((POST_BUFFER * RATE) / CHUNK)
            for _ in range(extra_chunks):
                buffer_frames.append(stream.read(CHUNK, exception_on_overflow=False))

            audio_queue.put(b"".join(buffer_frames))

            recording = False
            buffer_frames = []


# ============================================================
#               SPEECH RECOGNITION WORKER
# ============================================================
def speech_recognition_worker():
    global change_to, paused, running

    recognizer = sr.Recognizer()

    while running:
        raw_audio = audio_queue.get()
        audio_data = sr.AudioData(raw_audio, 16000, 2)
        command_recognized = False
        try:
            text = recognizer.recognize_google(audio_data).lower()
            print(">> Google rozpoznał:", text)


            if "move up" in text:
                change_to = "UP"
                command_recognized = True

            elif "move down" in text:
                change_to = "DOWN"
                command_recognized = True

            elif "move left" in text:
                change_to = "LEFT"
                command_recognized = True

            elif "move right" in text:
                change_to = "RIGHT"
                command_recognized = True

            elif "game resume" in text:
                command_recognized = True

            else:
                print(">> Nieznana komenda.")

        except Exception:
            print(">> Błąd rozpoznawania.")

        if command_recognized:
            paused = False
            print(">> Gra wznowiona.")

        audio_queue.task_done()


# ============================================================
#                      GUI + LOGIKA
# ============================================================
def show_score(choice, color, font, size):
    score_font = pygame.font.SysFont(font, size)
    score_surface = score_font.render('Score : ' + str(score), True, color)
    score_rect = score_surface.get_rect()
    game_window.blit(score_surface, score_rect)


def game_over():
    global paused

    paused = False

    my_font = pygame.font.SysFont('times new roman', 90)
    game_over_surface = my_font.render('GAME OVER', True, RED)
    game_over_rect = game_over_surface.get_rect()
    game_over_rect.midtop = (WINDOW_WIDTH/2, WINDOW_HEIGHT/4)
    game_window.blit(game_over_surface, game_over_rect)
    show_score(0, BLACK, 'times new roman', 20)
    pygame.display.flip()
    time.sleep(2)

    return True   # ← KLUCZOWE


# ============================================================
#                      MAIN GAME LOOP
# ============================================================
def run_game():
    global direction, change_to, score, food_spawn, food_pos, snake_pos, snake_body, paused

    # --- RESET STANU GRY (NIE DOTYKAMY AUDIO!) ---
    paused = False

    snake_pos = [100, 50]
    snake_body = [[100, 50], [90, 50], [80, 50]]

    food_pos = [random.randrange(1, (WINDOW_WIDTH // 10)) * 10,
                random.randrange(1, (WINDOW_HEIGHT // 10)) * 10]
    food_spawn = True

    direction = 'RIGHT'
    change_to = direction
    score = 0
    # --- KONIEC RESETU ---

    running=True

    vad_thread = threading.Thread(target=vad_listener, daemon=True)
    sr_thread = threading.Thread(target=speech_recognition_worker, daemon=True)
    vad_thread.start()
    sr_thread.start()

    while True:
        # Obsługa eventów
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    change_to = 'UP'
                elif event.key == pygame.K_DOWN:
                    change_to = 'DOWN'
                elif event.key == pygame.K_LEFT:
                    change_to = 'LEFT'
                elif event.key == pygame.K_RIGHT:
                    change_to = 'RIGHT'

            if event.type == pygame.QUIT:
                running = False
                return  # ← WRACA DO MENU

        # Blokowanie przeciwstawnych kierunków
        if change_to == 'UP' and direction != 'DOWN':
            direction = 'UP'
        elif change_to == 'DOWN' and direction != 'UP':
            direction = 'DOWN'
        elif change_to == 'LEFT' and direction != 'RIGHT':
            direction = 'LEFT'
        elif change_to == 'RIGHT' and direction != 'LEFT':
            direction = 'RIGHT'

        # Pauza (mówisz → pauza)
        if paused:
            show_score(1, WHITE, 'times new roman', 20)
            pygame.display.update()
            fps_controller.tick(SNAKE_SPEED)
            continue

        # -------------------
        # RUCH WĘŻA
        # -------------------
        if direction == 'UP': snake_pos[1] -= 10
        elif direction == 'DOWN': snake_pos[1] += 10
        elif direction == 'LEFT': snake_pos[0] -= 10
        elif direction == 'RIGHT': snake_pos[0] += 10

        snake_body.insert(0, list(snake_pos))
        if snake_pos == food_pos:
            score += 10
            food_spawn = False
        else:
            snake_body.pop()

        if not food_spawn:
            food_pos = [random.randrange(1, WINDOW_WIDTH//10) * 10,
                        random.randrange(1, WINDOW_HEIGHT//10) * 10]
        food_spawn = True

        # -------------------
        # RYSOWANIE
        # -------------------
        game_window.fill(BLACK)
        for pos in snake_body:
            pygame.draw.rect(game_window, GREEN, pygame.Rect(pos[0], pos[1], 10, 10))

        pygame.draw.rect(game_window, WHITE, pygame.Rect(food_pos[0], food_pos[1], 10, 10))

        # -------------------
        # KOLIZJE
        # -------------------
        if snake_pos[0] < 0 or snake_pos[0] > WINDOW_WIDTH-10:
            if game_over(): return

        if snake_pos[1] < 0 or snake_pos[1] > WINDOW_HEIGHT-10:
            if game_over(): return

        for block in snake_body[1:]:
            if snake_pos == block:
                if game_over(): return

        # Aktualizacja ekranu
        show_score(1, WHITE, 'times new roman', 20)
        pygame.display.update()
        fps_controller.tick(SNAKE_SPEED)


if __name__ == '__main__':
    run_game()
