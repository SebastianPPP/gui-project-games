import pygame
import time
import random
import speech_recognition as sr
import threading
import pyaudio
import numpy as np
import queue


audio_queue = queue.Queue()   # kolejka przekazująca audio VAD → SR
paused = False   

# game config
SNAKE_SPEED = 5
WINDOW_WIDTH = 720
WINDOW_HEIGHT = 480

paused = False

# Color definitions (RGB)
BLACK = pygame.Color(0, 0, 0)
WHITE = pygame.Color(255, 255, 255)
RED = pygame.Color(255, 0, 0)
GREEN = pygame.Color(0, 255, 0)

# Initialize Pygame
pygame.init()
pygame.display.set_caption('Voice Controlled Snake')
game_window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))

# FPS controller
fps_controller = pygame.time.Clock()

# game variables
snake_pos = [100, 50]
snake_body = [[100, 50], [90, 50], [80, 50]]

# Initial food pos and direction
food_pos = [random.randrange(1, (WINDOW_WIDTH//10)) * 10, 
            random.randrange(1, (WINDOW_HEIGHT//10)) * 10]
food_spawn = True

direction = 'RIGHT'
change_to = direction 

score = 0

def vad_listener():
    global paused
    import pyaudio
    import numpy as np
    import time

    pa = pyaudio.PyAudio()

    RATE = 16000
    CHUNK = 1024

    stream = pa.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=RATE,
        input=True,
        frames_per_buffer=CHUNK
    )

    # Kalibracja szumu
    noise = []
    for _ in range(20):
        data = np.frombuffer(stream.read(CHUNK, exception_on_overflow=False), dtype=np.int16)
        noise.append(np.abs(data).mean())
        time.sleep(0.05)

    noise_level = np.mean(noise)
    THRESHOLD = noise_level * 10.0      # nie 3.0 — 2.0 jest bardziej czułe

    # NOWOŚĆ:
    HOLD_TIME = 0.8      # wydłużone z 0.4 → teraz masz realnie czas powiedzieć „up”
    POST_BUFFER = 0.3    # doda 300 ms nagrywania na końcu, *zawsze*

    recording = False
    buffer_frames = []
    last_voice_time = 0

    while True:
        data = stream.read(CHUNK, exception_on_overflow=False)
        frame = np.frombuffer(data, dtype=np.int16)
        volume = np.abs(frame).mean()
        now = time.time()

        # dźwięk jest ponad progiem → mowa trwa
        if volume > THRESHOLD:
            if not recording:
                paused = True
                recording = True

            last_voice_time = now
            buffer_frames.append(data)
            continue

        # gdy cisza > HOLD_TIME → KONIEC MOWY
        if recording and (now - last_voice_time > HOLD_TIME):
            # DODATKOWE DO-NAGRANIE:
            # 300ms audio po końcu mowy (na wypadek przerwy w środku komendy)
            extra_chunks = int((POST_BUFFER * RATE) / CHUNK)
            for _ in range(extra_chunks):
                buffer_frames.append(stream.read(CHUNK, exception_on_overflow=False))

            # wysyłamy pełen bufor do SR
            audio_queue.put(b"".join(buffer_frames))

            recording = False
            buffer_frames = []

def speech_recognition_worker():
    global change_to, paused

    recognizer = sr.Recognizer()

    while True:
        raw_audio = audio_queue.get()   # czekamy na audio z VAD
        audio_data = sr.AudioData(raw_audio, 16000, 2)

        try:
            text = recognizer.recognize_google(audio_data).lower()
            print(">> Google rozpoznał:", text)

            command_recognized = False

            # ======================================
            #   KOMENDY RUCHU
            # ======================================
            if "snake up" in text:
                print(">> Komenda: UP")
                change_to = "UP"
                command_recognized = True

            elif "snake down" in text:
                print(">> Komenda: DOWN")
                change_to = "DOWN"
                command_recognized = True

            elif "snake left" in text:
                print(">> Komenda: LEFT")
                change_to = "LEFT"
                command_recognized = True

            elif "snake right" in text:
                print(">> Komenda: RIGHT")
                change_to = "RIGHT"
                command_recognized = True

            # ======================================
            #   RESUME — wznawia bez zmiany kierunku
            # ======================================
            elif "snake resume" in text:
                print(">> Komenda: RESUME (wznów grę)")
                command_recognized = True

            # ======================================
            #   TEKST ROZPOZNANY, ALE NIEPRAWIDŁOWA KOMENDA
            # ======================================
            else:
                print(">> Nierozpoznana komenda. Gra pozostaje w pauzie.")

        except Exception as e:
            print(">> Błąd rozpoznawania — gra pozostaje w pauzie.")
            command_recognized = False

        # ======================================
        #   ODPALAMY GRĘ TYLKO JEŚLI KOMENDA POPRAWNA
        # ======================================
        if command_recognized:
            paused = False
            print(">> Gra wznowiona.")

        audio_queue.task_done()



# GUI functions

def show_score(choice, color, font, size):
    score_font = pygame.font.SysFont(font, size)
    score_surface = score_font.render('Score : ' + str(score), True, color)
    score_rect = score_surface.get_rect()
    game_window.blit(score_surface, score_rect)

def game_over():
    my_font = pygame.font.SysFont('times new roman', 90)
    game_over_surface = my_font.render('GAME OVER', True, RED)
    game_over_rect = game_over_surface.get_rect()
    game_over_rect.midtop = (WINDOW_WIDTH/2, WINDOW_HEIGHT/4)
    game_window.blit(game_over_surface, game_over_rect)
    show_score(0, BLACK, 'times new roman', 20)
    pygame.display.flip()
    time.sleep(3)
    pygame.quit()
    quit()

# main game loop
def run_game():
    global direction, change_to, score, food_spawn, food_pos, snake_pos, snake_body

    while True:
        # Keyboard event handling
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    change_to = 'UP'
                if event.key == pygame.K_DOWN:
                    change_to = 'DOWN'
                if event.key == pygame.K_LEFT:
                    change_to = 'LEFT'
                if event.key == pygame.K_RIGHT:
                    change_to = 'RIGHT'
        
        # forbidden direction changes
        if change_to == 'UP' and direction != 'DOWN':
            direction = 'UP'
        if change_to == 'DOWN' and direction != 'UP':
            direction = 'DOWN'
        if change_to == 'LEFT' and direction != 'RIGHT':
            direction = 'LEFT'
        if change_to == 'RIGHT' and direction != 'LEFT':
            direction = 'RIGHT'
        
        if paused:
            show_score(1, WHITE, 'times new roman', 20)
            pygame.display.update()
            fps_controller.tick(SNAKE_SPEED)
            continue

        # snake moves
        if direction == 'UP':
            snake_pos[1] -= 10
        if direction == 'DOWN':
            snake_pos[1] += 10
        if direction == 'LEFT':
            snake_pos[0] -= 10
        if direction == 'RIGHT':
            snake_pos[0] += 10

        # snake growth mechanism
        snake_body.insert(0, list(snake_pos))
        if snake_pos[0] == food_pos[0] and snake_pos[1] == food_pos[1]:
            score += 10
            food_spawn = False
        else:
            snake_body.pop()
            
        # new food spawn
        if not food_spawn:
            food_pos = [random.randrange(1, (WINDOW_WIDTH//10)) * 10,
                        random.randrange(1, (WINDOW_HEIGHT//10)) * 10]
        food_spawn = True

        # draw everything on screen
        game_window.fill(BLACK)
        for pos in snake_body:
            pygame.draw.rect(game_window, GREEN, pygame.Rect(pos[0], pos[1], 10, 10))
        
        pygame.draw.rect(game_window, WHITE, pygame.Rect(food_pos[0], food_pos[1], 10, 10))

        # Game over conditions
        # Collision with boundaries
        if snake_pos[0] < 0 or snake_pos[0] > WINDOW_WIDTH-10:
            game_over()
        if snake_pos[1] < 0 or snake_pos[1] > WINDOW_HEIGHT-10:
            game_over()
        
        # Collision with self
        for block in snake_body[1:]:
            if snake_pos[0] == block[0] and snake_pos[1] == block[1]:
                game_over()

        # refresh game screen and score
        show_score(1, WHITE, 'times new roman', 20)
        pygame.display.update()
        fps_controller.tick(SNAKE_SPEED)

if __name__ == '__main__':
    threading.Thread(target=vad_listener, daemon=True).start()
    threading.Thread(target=speech_recognition_worker, daemon=True).start()
    run_game()