import pygame
import random
import sys
import threading
import time
import cv2
import mediapipe as mp
import csv
import numpy as np
import os

SCREEN_WIDTH = 850
SCREEN_HEIGHT = 600
FPS = 30
GRAVITY = 1
GROUND_LEVEL = 450
JUMP_VELOCITY = 17
SCORE_FILE = "scoreboard.csv"

WHITE = (255, 255, 255)
BLACK = (15, 15, 25)
GRAY = (100, 100, 100)
NEON_GREEN = (50, 255, 50)
NEON_BLUE = (50, 150, 255)
RED = (255, 50, 50)
SCORE_COLOR = (83, 83, 83)
BACKGROUND_COLOR = (240, 240, 240)

camera_running = False
camera_ready = False
hand_jump_flag = False
current_player_name = "Gracz"

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)
mp_drawing = mp.solutions.drawing_utils

def save_score_to_csv(score):
    try:
        with open(SCORE_FILE, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["dino_video", current_player_name, score])
    except Exception as e:
        print(f"Błąd zapisu: {e}")

def is_open_hand(hand_landmarks):
    """Zwraca True, jeśli dłoń jest otwarta (wszystkie palce wyprostowane)."""
    tip_ids = [4, 8, 12, 16, 20]
    fingers = []

    # Kciuk
    if hand_landmarks.landmark[tip_ids[0]].x < hand_landmarks.landmark[tip_ids[0] - 1].x:
        fingers.append(1)
    else:
        fingers.append(0)

    # Pozostałe palce
    for idx in range(1, 5):
        if hand_landmarks.landmark[tip_ids[idx]].y < hand_landmarks.landmark[tip_ids[idx] - 2].y:
            fingers.append(1)
        else:
            fingers.append(0)

    return fingers == [1, 1, 1, 1, 1]

def gesture_control_dino(cam_index):
    """Wątek przetwarzający obraz z kamery."""
    global camera_running, camera_ready, hand_jump_flag
    
    cap = cv2.VideoCapture(cam_index)
    if not cap.isOpened():
        camera_running = False
        return

    prev_open = False

    while camera_running:
        success, image = cap.read()
        if not success: continue

        camera_ready = True

        image = cv2.resize(image, (320, 240))
        image = cv2.flip(image, 1)
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        results = hands.process(image_rgb)
        open_now = False

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                if is_open_hand(hand_landmarks):
                    open_now = True
                
                mp_drawing.draw_landmarks(image, hand_landmarks, mp_hands.HAND_CONNECTIONS)

        if open_now and not prev_open:
            hand_jump_flag = True
        
        prev_open = open_now

        color = (0, 255, 0) if open_now else (0, 0, 255)
        txt = "SKOK!" if open_now else "Zacisnij piesc"
        cv2.putText(image, txt, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        
        cv2.imshow('Kamera - Detekcja', image)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            camera_running = False
            break

    cap.release()
    cv2.destroyAllWindows()

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

def show_config_screen(screen):
    clock = pygame.time.Clock()
    font = pygame.font.SysFont('arial', 24)
    font_title = pygame.font.SysFont('arial', 40, bold=True)
    
    input_active = True
    player_name = "Gracz Dino"
    
    # Wykrywanie kamer
    devices = []
    for i in range(3):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            devices.append(f"Kamera {i}")
            cap.release()
    if not devices: devices = ["Brak Kamery"]
    selected_dev_idx = 0
    
    # Podgląd kamery w configu
    current_cam = cv2.VideoCapture(0)
    
    while True:
        screen.fill(BLACK)
        
        # Ramka
        pygame.draw.rect(screen, (30, 30, 40), (100, 50, 650, 500), border_radius=10)
        pygame.draw.rect(screen, NEON_BLUE, (100, 50, 650, 500), 2, border_radius=10)
        
        # Tytuł
        title = font_title.render("KONFIGURACJA: DINO WIDEO", True, WHITE)
        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 70))

        # Imię
        screen.blit(font.render("Nazwa Gracza:", True, GRAY), (150, 150))
        pygame.draw.rect(screen, NEON_BLUE if input_active else GRAY, (150, 180, 300, 40), 2)
        screen.blit(font.render(player_name, True, WHITE), (160, 190))
        
        # Wybór kamery
        screen.blit(font.render("Wybór Kamery (Strzałki L/P):", True, GRAY), (150, 250))
        dev_txt = font.render(f"< {devices[selected_dev_idx]} >", True, NEON_GREEN)
        screen.blit(dev_txt, (150, 280))
        
        # Podgląd
        screen.blit(font.render("Test Kamery:", True, GRAY), (500, 150))
        pygame.draw.rect(screen, GRAY, (500, 180, 200, 150), 2)
        
        if current_cam.isOpened():
            ret, frame = current_cam.read()
            if ret:
                frame = cv2.resize(frame, (196, 146))
                frame = cv2.flip(frame, 1)
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame = np.rot90(frame)
                surf = pygame.surfarray.make_surface(frame)
                screen.blit(surf, (502, 182))
        
        # Instrukcja
        btn_txt = font.render("GRAJ (Enter)", True, BLACK)
        btn_rect = pygame.Rect(SCREEN_WIDTH//2 - 100, 480, 200, 50)
        pygame.draw.rect(screen, NEON_GREEN, btn_rect, border_radius=5)
        screen.blit(btn_txt, (btn_rect.centerx - btn_txt.get_width()//2, btn_rect.centery - btn_txt.get_height()//2))

        esc_txt = font.render("ESC - Powrót", True, RED)
        screen.blit(esc_txt, (120, 500))

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
                    elif len(player_name) < 12: player_name += event.unicode
                
                if not input_active or (input_active and event.key in [pygame.K_LEFT, pygame.K_RIGHT]):
                    pass 
                
                if event.key == pygame.K_RIGHT:
                    selected_dev_idx = (selected_dev_idx + 1) % len(devices)
                    current_cam.release()
                    try: dev_id = int(devices[selected_dev_idx].split()[-1])
                    except: dev_id = 0
                    current_cam = cv2.VideoCapture(dev_id)
                elif event.key == pygame.K_LEFT:
                    selected_dev_idx = (selected_dev_idx - 1) % len(devices)
                    current_cam.release()
                    try: dev_id = int(devices[selected_dev_idx].split()[-1])
                    except: dev_id = 0
                    current_cam = cv2.VideoCapture(dev_id)

        clock.tick(30)

def run_dino_camera_game(cam_index=None):
    global camera_running, camera_ready, hand_jump_flag, current_player_name

    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Dino - Sterowanie Wideo")
    
    name, dev_id = show_config_screen(screen)
    if name is None: return # Anulowano
    current_player_name = name
    cam_index = dev_id

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

    camera_ready = False
    camera_running = True
    hand_jump_flag = False
    
    thread = threading.Thread(target=gesture_control_dino, args=(cam_index,), daemon=True)
    thread.start()

    while not camera_ready:
        screen.fill(BACKGROUND_COLOR)
        font = pygame.font.SysFont('arial', 30)
        txt = font.render("Uruchamianie kamery...", True, BLACK)
        screen.blit(txt, (SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT//2))
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                camera_running = False
                return
        clock.tick(10)

    while game_active:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game_active = False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE or event.key == pygame.K_UP:
                    dino.jump()
                if event.key == pygame.K_ESCAPE:
                    game_active = False

            if event.type == SPAWN_CACTUS:
                cacti_group.add(Cactus(obstacle_speed))
                all_sprites.add(cacti_group.sprites()[-1])

        if hand_jump_flag:
            dino.jump()
            hand_jump_flag = False

        if pygame.sprite.spritecollide(dino, cacti_group, False):
            save_score_to_csv(score)
            
            screen.fill(BACKGROUND_COLOR)
            font_big = pygame.font.SysFont('arial', 60, bold=True)
            txt = font_big.render("GAME OVER", True, RED)
            score_txt = pygame.font.SysFont('arial', 30).render(f"Wynik: {score}", True, BLACK)
            screen.blit(txt, (SCREEN_WIDTH//2 - 150, SCREEN_HEIGHT//2 - 50))
            screen.blit(score_txt, (SCREEN_WIDTH//2 - 60, SCREEN_HEIGHT//2 + 20))
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

    camera_running = False
    if thread.is_alive():
        thread.join(timeout=1.0)

if __name__ == '__main__':
    run_dino_camera_game()