import pygame
import time
import random
import sys
import threading 
import cv2 
import mediapipe as mp 

camera_ready = False   # ← DODANE: Kamera gotowa dopiero po pierwszej klatce


# game config
SNAKE_SPEED = 5
WINDOW_WIDTH = 720
WINDOW_HEIGHT = 480

# Color definitions (RGB)
BLACK = pygame.Color(0, 0, 0)
WHITE = pygame.Color(255, 255, 255)
RED = pygame.Color(255, 0, 0)
GREEN = pygame.Color(0, 255, 0)

direction = 'RIGHT'
change_to = direction 
food_spawn = True
score = 0
camera_running = True  # Flaga do kontrolowania wątku kamery

pygame.init()
pygame.display.set_caption('Gesture Controlled Snake')
game_window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))

# FPS controller
fps_controller = pygame.time.Clock()


mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)
mp_drawing = mp.solutions.drawing_utils

def get_default_camera():
    """Automatycznie wykrywa i zwraca indeks dostępnej kamery."""
    for i in range(3):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            backend_name = cap.getBackendName()
            cap.release()
            print(f"✓ Automatycznie wykryto kamerę: Indeks {i} (Backend: {backend_name})")
            return i
    return None

def detect_gesture(hand_landmarks):
    """Zwraca kierunek na podstawie pozycji palców."""
    
    tip_ids = [4, 8, 12, 16, 20] # Końcówki palców
    
    fingers = []
    
    # 1. Kciuk
    if hand_landmarks.landmark[tip_ids[0]].x < hand_landmarks.landmark[tip_ids[0]-1].x:
        fingers.append(1)
    else:
        fingers.append(0)

    # 2. Pozostałe palce
    for id in range(1, 5):
        if hand_landmarks.landmark[tip_ids[id]].y < hand_landmarks.landmark[tip_ids[id]-2].y:
            fingers.append(1)
        else:
            fingers.append(0)
    
    if fingers == [0, 1, 0, 0, 0]:
        return 'UP'
    if fingers == [0, 0, 0, 0, 0]:
        return 'RIGHT'
    if fingers == [1, 1, 0, 0, 0]:
        return 'LEFT'
    if fingers == [0, 1, 1, 0, 0]:
        return 'DOWN'
        
    return None

def gesture_control_snake(cam_index): 
    global change_to, direction, camera_running, camera_ready
    
    cap = cv2.VideoCapture(cam_index)
    
    if not cap.isOpened():
        print("Nie można otworzyć kamery!")
        camera_running = False
        return
    
    backend_name = cap.getBackendName()
    print(f"✓ Wykryto kamerę: Indeks {cam_index} (Backend: {backend_name})")

    while camera_running:
        success, image = cap.read()
        if not success:
            if not camera_running:
                break
            continue

        # Kamera dopiero teraz jest gotowa!
        camera_ready = True  # ← KLUCZOWE

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
                        cv2.putText(image, gesture, (10, 30),
                                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                
                mp_drawing.draw_landmarks(
                    image,
                    hand_landmarks,
                    mp_hands.HAND_CONNECTIONS,
                    mp_drawing.DrawingSpec(color=(255, 0, 0), thickness=2),
                    mp_drawing.DrawingSpec(color=(0, 0, 255), thickness=2)
                )

        cv2.imshow('Kamera', image)
        
        if cv2.waitKey(5) & 0xFF == ord('q'):
            camera_running = False
            break

    cap.release()
    cv2.destroyAllWindows()


def show_score(choice, color, font, size):
    score_font = pygame.font.SysFont(font, size)
    score_surface = score_font.render('Score : ' + str(score), True, color)
    score_rect = score_surface.get_rect()
    game_window.blit(score_surface, score_rect)

def game_over():
    global camera_running
    
    camera_running = False 
    
    time.sleep(0.5)
    
    my_font = pygame.font.SysFont('times new roman', 90)
    game_over_surface = my_font.render('GAME OVER', True, RED)
    game_over_rect = game_over_surface.get_rect()
    game_over_rect.midtop = (WINDOW_WIDTH/2, WINDOW_HEIGHT/4)
    game_window.blit(game_over_surface, game_over_rect)
    show_score(0, BLACK, 'times new roman', 20)
    pygame.display.flip()
    time.sleep(2)
    return True


# main game loop
def run_game(cam_index=None): 
    global direction, change_to, score, food_spawn, snake_pos, snake_body, food_pos, camera_running, camera_ready

    camera_ready = False  # ← Reset flagi na starcie

    if cam_index is None:
        print("Szukanie kamery...")
        cam_index = get_default_camera()
        if cam_index is None:
            print("Nie znaleziono kamery! Gra działa bez sterowania gestami.")
            pass
        else:
            camera_running = True
    else:
        camera_running = True
        
    snake_pos = [100, 50]
    snake_body = [[100, 50], [90, 50], [80, 50]]
    food_pos = [random.randrange(1, (WINDOW_WIDTH//10)) * 10, 
                random.randrange(1, (WINDOW_HEIGHT//10)) * 10]
    direction = 'RIGHT'
    change_to = direction 
    food_spawn = True 
    score = 0
    
    thread = None
    if cam_index is not None:
        thread = threading.Thread(target=gesture_control_snake, args=(cam_index,), daemon=True)
        thread.start()
        print("Gesty: Góra=Wskazujący, Dół=V, Lewo=L, Prawo=Pięść")

    # ===========================================
    # CZEKAJ NA KAMERĘ → Snake NIE RUSZA
    # ===========================================
    if cam_index is not None:
        print("Czekam na kamerę...")
        while not camera_ready:
            game_window.fill(BLACK)
            font = pygame.font.SysFont('times new roman', 40)
            loading_text = font.render("Ładowanie kamery...", True, WHITE)
            game_window.blit(loading_text, (WINDOW_WIDTH/2 - 160, WINDOW_HEIGHT/2 - 20))
            pygame.display.update()
            fps_controller.tick(10)
        print("Kamera gotowa — start gry!")

    # ===========================================
    # GŁÓWNA PĘTLA GRY
    # ===========================================
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:

                if thread is not None and thread.is_alive():
                    camera_running = False
                    thread.join(timeout=1.0)

                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP and direction != 'DOWN':
                    change_to = 'UP'
                if event.key == pygame.K_DOWN and direction != 'UP':
                    change_to = 'DOWN'
                if event.key == pygame.K_LEFT and direction != 'RIGHT':
                    change_to = 'LEFT'
                if event.key == pygame.K_RIGHT and direction != 'LEFT':
                    change_to = 'RIGHT'
        
        # Zabronione cofanie się
        if change_to == 'UP' and direction != 'DOWN':
            direction = 'UP'
        if change_to == 'DOWN' and direction != 'UP':
            direction = 'DOWN'
        if change_to == 'LEFT' and direction != 'RIGHT':
            direction = 'LEFT'
        if change_to == 'RIGHT' and direction != 'LEFT':
            direction = 'RIGHT'
        
        # RUCH WĘŻA
        if direction == 'UP':
            snake_pos[1] -= 10
        if direction == 'DOWN':
            snake_pos[1] += 10
        if direction == 'LEFT':
            snake_pos[0] -= 10
        if direction == 'RIGHT':
            snake_pos[0] += 10

        snake_body.insert(0, list(snake_pos))
        if snake_pos == food_pos:
            score += 10
            food_spawn = False
        else:
            snake_body.pop()
            
        if not food_spawn:
            food_pos = [
                random.randrange(1, WINDOW_WIDTH//10) * 10,
                random.randrange(1, WINDOW_HEIGHT//10) * 10
            ]
        food_spawn = True

        game_window.fill(BLACK)
        for pos in snake_body:
            pygame.draw.rect(game_window, GREEN, pygame.Rect(pos[0], pos[1], 10, 10))
        
        pygame.draw.rect(game_window, WHITE, pygame.Rect(food_pos[0], food_pos[1], 10, 10))

        # Kolizje
        collision_self = any(snake_pos == block for block in snake_body[1:])
        
        if (snake_pos[0] < 0 or snake_pos[0] > WINDOW_WIDTH-10 or 
            snake_pos[1] < 0 or snake_pos[1] > WINDOW_HEIGHT-10 or 
            collision_self):
            
            if game_over():
                if thread is not None and thread.is_alive():
                    thread.join(timeout=1.0)
                return

        show_score(1, WHITE, 'times new roman', 20)
        pygame.display.update()
        fps_controller.tick(SNAKE_SPEED)


if __name__ == '__main__':
    run_game()
