import pygame
import time
import random
import sys
import threading 
import cv2 
import csv
import mediapipe as mp 
import numpy as np

WINDOW_WIDTH = 850
WINDOW_HEIGHT = 600
SCORE_FILE = "scoreboard.csv"

BLACK = (15, 15, 25)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (50, 255, 50)
NEON_BLUE = (50, 150, 255)
GRAY = (100, 100, 100)

camera_running = True  
camera_ready = False
current_player_name = "Gracz"

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(static_image_mode=False, max_num_hands=1, min_detection_confidence=0.5, min_tracking_confidence=0.5)
mp_drawing = mp.solutions.drawing_utils

def save_score_to_csv(score):
    try:
        with open(SCORE_FILE, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["snake_video", current_player_name, score])
    except: pass

def detect_gesture(hand_landmarks):
    tip_ids = [4, 8, 12, 16, 20]
    fingers = []
    # Kciuk
    if hand_landmarks.landmark[tip_ids[0]].x < hand_landmarks.landmark[tip_ids[0]-1].x: fingers.append(1)
    else: fingers.append(0)
    # Reszta
    for id in range(1, 5):
        if hand_landmarks.landmark[tip_ids[id]].y < hand_landmarks.landmark[tip_ids[id]-2].y: fingers.append(1)
        else: fingers.append(0)
    
    if fingers == [0, 1, 0, 0, 0]: return 'UP'
    if fingers == [0, 0, 0, 0, 0]: return 'RIGHT'
    if fingers == [1, 1, 0, 0, 0]: return 'LEFT'
    if fingers == [0, 1, 1, 0, 0]: return 'DOWN'
    return None

def gesture_control_snake(cam_index): 
    global change_to, direction, camera_running, camera_ready
    cap = cv2.VideoCapture(cam_index)
    
    while camera_running and cap.isOpened():
        success, image = cap.read()
        if not success: continue
        camera_ready = True 
        image = cv2.resize(image, (320, 240)) 
        image = cv2.flip(image, 1)
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        results = hands.process(image_rgb)
        gesture = None
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                gesture = detect_gesture(hand_landmarks)
                if gesture:
                    if (gesture == 'UP' and direction != 'DOWN' or
                        gesture == 'DOWN' and direction != 'UP' or
                        gesture == 'LEFT' and direction != 'RIGHT' or
                        gesture == 'RIGHT' and direction != 'LEFT'):
                        change_to = gesture
                        cv2.putText(image, gesture, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                mp_drawing.draw_landmarks(image, hand_landmarks, mp_hands.HAND_CONNECTIONS)
        
        cv2.imshow('Podglad kamery', image)
        if cv2.waitKey(5) & 0xFF == ord('q'): break
    cap.release()
    cv2.destroyAllWindows()

# --- EKRAN KONFIGURACJI (LAUNCHER) ---
def show_config_screen(screen):
    clock = pygame.time.Clock()
    font = pygame.font.SysFont('arial', 24)
    input_active = True
    player_name = "Gracz"
    
    # Wykrywanie kamer
    devices = []
    for i in range(3):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            devices.append(f"Kamera {i}")
            cap.release()
    if not devices: devices = ["Brak Kamery"]
    selected_dev_idx = 0
    current_cam = cv2.VideoCapture(0)
    
    while True:
        screen.fill(BLACK)
        
        # UI
        pygame.draw.rect(screen, (30, 30, 40), (100, 100, 600, 400), border_radius=10)
        pygame.draw.rect(screen, NEON_BLUE, (100, 100, 600, 400), 2, border_radius=10)
        
        title = font.render("KONFIGURACJA: SNAKE WIDEO", True, WHITE)
        screen.blit(title, (250, 50))

        screen.blit(font.render("Nazwa Gracza:", True, GRAY), (150, 150))
        pygame.draw.rect(screen, NEON_BLUE if input_active else GRAY, (150, 180, 300, 40), 2)
        screen.blit(font.render(player_name, True, WHITE), (160, 190))
        
        screen.blit(font.render("Wybór Kamery (Strzałki):", True, GRAY), (150, 250))
        dev_txt = font.render(f"< {devices[selected_dev_idx]} >", True, GREEN)
        screen.blit(dev_txt, (150, 280))
        
        screen.blit(font.render("Test Kamery:", True, GRAY), (500, 150))
        pygame.draw.rect(screen, GRAY, (500, 180, 160, 120), 2)
        
        if current_cam.isOpened():
            ret, frame = current_cam.read()
            if ret:
                frame = cv2.resize(frame, (156, 116))
                frame = cv2.flip(frame, 1)
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame = np.rot90(frame)
                surf = pygame.surfarray.make_surface(frame)
                screen.blit(surf, (502, 182))
        
        info = font.render("GRAJ: Enter | ANULUJ: Esc", True, WHITE)
        screen.blit(info, (280, 420))

        pygame.display.flip()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                current_cam.release()
                return None, None
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    current_cam.release()
                    return None, None
                if event.key == pygame.K_RETURN:
                    current_cam.release()
                    try: dev_id = int(devices[selected_dev_idx].split()[-1])
                    except: dev_id = 0
                    return player_name, dev_id
                    
                if input_active:
                    if event.key == pygame.K_BACKSPACE: player_name = player_name[:-1]
                    else: 
                        if len(player_name) < 12: player_name += event.unicode
                else:
                    pass
                
                if event.key == pygame.K_RIGHT:
                    selected_dev_idx = (selected_dev_idx + 1) % len(devices)
                    current_cam.release()
                    try: dev_id = int(devices[selected_dev_idx].split()[-1])
                    except: dev_id = 0
                    current_cam = cv2.VideoCapture(dev_id)
                if event.key == pygame.K_LEFT:
                    selected_dev_idx = (selected_dev_idx - 1) % len(devices)
                    current_cam.release()
                    try: dev_id = int(devices[selected_dev_idx].split()[-1])
                    except: dev_id = 0
                    current_cam = cv2.VideoCapture(dev_id)

        clock.tick(30)

def run_game():
    global direction, change_to, score, food_spawn, snake_pos, snake_body, food_pos, camera_running, camera_ready, current_player_name
    
    pygame.init()
    win = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    
    name, cam_idx = show_config_screen(win)
    if name is None: return # Powrót do menu
    
    current_player_name = name
    
    camera_ready = False
    camera_running = True
    
    snake_pos = [100, 50]
    snake_body = [[100, 50], [90, 50], [80, 50]]
    food_pos = [random.randrange(1, (WINDOW_WIDTH//10)) * 10, random.randrange(1, (WINDOW_HEIGHT//10)) * 10]
    direction, change_to = 'RIGHT', 'RIGHT'
    score = 0
    food_spawn = True
    
    thread = threading.Thread(target=gesture_control_snake, args=(cam_idx,), daemon=True)
    thread.start()

    fps = pygame.time.Clock()
    while not camera_ready:
        win.fill(BLACK)
        txt = pygame.font.SysFont('arial', 30).render("Uruchamianie kamery...", True, NEON_BLUE)
        win.blit(txt, (WINDOW_WIDTH/2 - 140, WINDOW_HEIGHT/2))
        pygame.display.update()
        for event in pygame.event.get():
             if event.type == pygame.QUIT: 
                 camera_running = False
                 return
        fps.tick(10)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: running = False
                if event.key == pygame.K_UP and direction != 'DOWN': change_to = 'UP'
                if event.key == pygame.K_DOWN and direction != 'UP': change_to = 'DOWN'
                if event.key == pygame.K_LEFT and direction != 'RIGHT': change_to = 'LEFT'
                if event.key == pygame.K_RIGHT and direction != 'LEFT': change_to = 'RIGHT'
        
        if change_to == 'UP' and direction != 'DOWN': direction = 'UP'
        if change_to == 'DOWN' and direction != 'UP': direction = 'DOWN'
        if change_to == 'LEFT' and direction != 'RIGHT': direction = 'LEFT'
        if change_to == 'RIGHT' and direction != 'LEFT': direction = 'RIGHT'
        
        if direction == 'UP': snake_pos[1] -= 10
        if direction == 'DOWN': snake_pos[1] += 10
        if direction == 'LEFT': snake_pos[0] -= 10
        if direction == 'RIGHT': snake_pos[0] += 10

        snake_body.insert(0, list(snake_pos))
        if snake_pos == food_pos:
            score += 10
            food_spawn = False
        else: snake_body.pop()
            
        if not food_spawn:
            food_pos = [random.randrange(1, WINDOW_WIDTH//10) * 10, random.randrange(1, WINDOW_HEIGHT//10) * 10]
            food_spawn = True

        win.fill(BLACK)
        for pos in snake_body: pygame.draw.rect(win, GREEN, pygame.Rect(pos[0], pos[1], 10, 10))
        pygame.draw.rect(win, WHITE, pygame.Rect(food_pos[0], food_pos[1], 10, 10))

        if (snake_pos[0] < 0 or snake_pos[0] > WINDOW_WIDTH-10 or 
            snake_pos[1] < 0 or snake_pos[1] > WINDOW_HEIGHT-10 or 
            any(snake_pos == block for block in snake_body[1:])):
            
            save_score_to_csv(score)
            time.sleep(1)
            running = False

        score_surf = pygame.font.SysFont('consolas', 20).render(f'Wynik: {score}', True, WHITE)
        win.blit(score_surf, (10, 10))
        pygame.display.update()
        fps.tick(10)

    camera_running = False
    if thread.is_alive(): thread.join(timeout=1.0)
    return

if __name__ == '__main__':
    run_game()