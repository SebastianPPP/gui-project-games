import pygame
import random
import sys
import threading
import time
import cv2
import mediapipe as mp

# ===== Konfiguracja gry (z dino_chrome_voice) =====
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 400
FPS = 30
GRAVITY = 1
GROUND_LEVEL = 350
JUMP_VELOCITY = 15
BACKGROUND_COLOR = (247, 247, 247)
SCORE_COLOR = (83, 83, 83)


pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('Dino Run - Kamera')
clock = pygame.time.Clock()

# ===== MediaPipe Hands =====
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)
mp_drawing = mp.solutions.drawing_utils

camera_running = False
camera_ready = False
hand_jump_flag = False


def get_default_camera():
    """Automatycznie wykrywa i zwraca indeks dostępnej kamery."""
    for i in range(3):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            backend = cap.getBackendName()
            cap.release()
            print(f"✓ Automatycznie wykryto kamerę: indeks {i} (backend: {backend})")
            return i
    print("⚠ Nie znaleziono działającej kamery.")
    return None


def is_open_hand(hand_landmarks):
    """
    Zwraca True, jeśli dłoń jest otwarta (wszystkie palce wyprostowane).
    Logika bardzo podobna do tej z vc_snake_video.
    """
    tip_ids = [4, 8, 12, 16, 20]  # końcówki palców

    fingers = []

    # Kciuk – oś X
    if hand_landmarks.landmark[tip_ids[0]].x < hand_landmarks.landmark[tip_ids[0] - 1].x:
        fingers.append(1)
    else:
        fingers.append(0)

    # Pozostałe palce – oś Y (końcówka wyżej niż staw środkowy)
    for idx in range(1, 5):
        if hand_landmarks.landmark[tip_ids[idx]].y < hand_landmarks.landmark[tip_ids[idx] - 2].y:
            fingers.append(1)
        else:
            fingers.append(0)

    # Otwarta dłoń: wszystkie palce wyprostowane
    return fingers == [1, 1, 1, 1, 1]


def gesture_control_dino(cam_index):
    """
    Wątek kamery: wykrywa otwartą dłoń i ustawia hand_jump_flag = True, gdy
    pojawi się otwarta dłoń (zbocze narastające).
    """
    global camera_running, camera_ready, hand_jump_flag

    cap = cv2.VideoCapture(cam_index)
    if not cap.isOpened():
        print("Nie można otworzyć kamery!")
        camera_running = False
        return

    backend = cap.getBackendName()
    print(f"✓ Wykryto kamerę: indeks {cam_index} (backend: {backend})")

    prev_open = False

    while camera_running:
        success, image = cap.read()
        if not success:
            if not camera_running:
                break
            continue

        # pierwsza udana klatka -> kamera gotowa
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

                mp_drawing.draw_landmarks(
                    image,
                    hand_landmarks,
                    mp_hands.HAND_CONNECTIONS,
                    mp_drawing.DrawingSpec(color=(255, 0, 0), thickness=2),
                    mp_drawing.DrawingSpec(color=(0, 0, 255), thickness=2)
                )

        # "zbocze narastające" - dopiero zmiana z zamkniętej na otwartą oznacza skok
        if open_now and dino_on_ground:
            print("🖐 Otwarta dłoń -> SKOK")
            hand_jump_flag = True

        prev_open = open_now

        # dodaj info tekstowe
        label = "OPEN HAND = JUMP" if open_now else "SHOW OPEN HAND TO JUMP"
        cv2.putText(image, label, (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                    (0, 255, 0) if open_now else (0, 0, 255),
                    2, cv2.LINE_AA)

        cv2.imshow("Kamera Dino", image)
        if cv2.waitKey(5) & 0xFF == ord('q'):
            camera_running = False
            break

    cap.release()
    cv2.destroyAllWindows()


# ===== Klasy gry (jak w dino_chrome_voice) =====
class Dino(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((20, 40))
        self.image.fill((50, 50, 50))
        self.rect = self.image.get_rect()
        self.rect.midbottom = (50, GROUND_LEVEL)
        self.y_velocity = 0
        self.is_jumping = False

    def update(self):
        global dino_on_ground
        if self.is_jumping:
            self.y_velocity += GRAVITY
            self.rect.y += self.y_velocity

            if self.rect.bottom >= GROUND_LEVEL:
                self.rect.bottom = GROUND_LEVEL
                self.is_jumping = False
                self.y_velocity = 0
                dino_on_ground=True
            else:
                dino_on_ground=False
        else:
            dino_on_ground=True

    def jump(self):
        if not self.is_jumping:
            self.is_jumping = True
            self.y_velocity = -JUMP_VELOCITY


class Cactus(pygame.sprite.Sprite):
    def __init__(self, speed):
        super().__init__()
        height = random.choice([20, 35, 50])
        self.image = pygame.Surface((15, height))
        self.image.fill((0, 100, 0))
        self.rect = self.image.get_rect()
        self.rect.bottomright = (SCREEN_WIDTH, GROUND_LEVEL)
        self.speed = speed

    def update(self):
        self.rect.x -= self.speed
        if self.rect.right < 0:
            self.kill()


def display_score(score):
    font = pygame.font.SysFont('Arial', 24)
    text_surface = font.render(f'Score: {score}', True, SCORE_COLOR)
    text_rect = text_surface.get_rect(center=(SCREEN_WIDTH / 2, 20))
    screen.blit(text_surface, text_rect)


def game_over_screen(score):
    font = pygame.font.SysFont('Arial', 70)
    text_surface = font.render('GAME OVER', True, SCORE_COLOR)
    text_rect = text_surface.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 30))
    screen.blit(text_surface, text_rect)

    font_score = pygame.font.SysFont('Arial', 30)
    score_surface = font_score.render(f'Final Score: {score}', True, SCORE_COLOR)
    score_rect = score_surface.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 30))
    screen.blit(score_surface, score_rect)

    pygame.display.flip()
    time.sleep(2)
    return


# ===== Główna funkcja gry na kamerę =====
def run_dino_camera_game(cam_index=None):
    global camera_running, camera_ready, hand_jump_flag

    camera_ready = False
    camera_running = False
    hand_jump_flag = False

    # wykrycie kamery
    if cam_index is None:
        print("Szukanie kamery...")
        cam_index = get_default_camera()
        if cam_index is None:
            print("Brak kamery – gra wystartuje tylko na klawiaturze.")
        else:
            camera_running = True
    else:
        camera_running = True

    dino = Dino()
    all_sprites = pygame.sprite.Group()
    cacti_group = pygame.sprite.Group()
    all_sprites.add(dino)

    game_active = True
    score = 0
    obstacle_speed = 5

    SPAWN_CACTUS = pygame.USEREVENT + 1
    pygame.time.set_timer(SPAWN_CACTUS, 2500)

    thread = None
    if camera_running and cam_index is not None:
        thread = threading.Thread(target=gesture_control_dino, args=(cam_index,), name="DinoGestureControl")
        thread.daemon = True
        thread.start()
        print("Sterowanie kamerą: pokaż otwartą dłoń = skok.")
    else:
        print("Sterowanie: SPACJA / STRZAŁKA W GÓRĘ = skok.")

    # Czekamy aż kamera będzie gotowa (jak w vc_snake_video)
    if camera_running and cam_index is not None:
        print("Czekam na kamerę...")
        font = pygame.font.SysFont('times new roman', 40)
        while not camera_ready:
            screen.fill(BACKGROUND_COLOR)
            text = font.render("Ładowanie kamery...", True, SCORE_COLOR)
            rect = text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2))
            screen.blit(text, rect)
            pygame.display.flip()
            clock.tick(10)
        print("Kamera gotowa — start gry!")

    while game_active:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                # zatrzymaj kamerę i wróć do menu
                camera_running = False
                if thread is not None and thread.is_alive():
                    thread.join(timeout=1.0)
                return

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE or event.key == pygame.K_UP:
                    dino.jump()

            if event.type == SPAWN_CACTUS:
                cacti_group.add(Cactus(obstacle_speed))
                all_sprites.add(cacti_group.sprites()[-1])

        # Skok ręką (otwarta dłoń)
        if hand_jump_flag:
            if not dino.is_jumping:   # ← Dino stoi na ziemi
                dino.jump()
            hand_jump_flag = False

        # Kolizja z kaktusami
        if pygame.sprite.spritecollide(dino, cacti_group, False):
            game_active = False

        if game_active:
            all_sprites.update()
            score += 1

            if score % 500 == 0:
                obstacle_speed += 0.5
                pygame.time.set_timer(SPAWN_CACTUS, max(500, 1500 - (score // 10)))

        screen.fill(BACKGROUND_COLOR)
        pygame.draw.line(screen, SCORE_COLOR,
                         (0, GROUND_LEVEL), (SCREEN_WIDTH, GROUND_LEVEL), 2)
        all_sprites.draw(screen)
        display_score(score // 10)
        pygame.display.flip()
        clock.tick(FPS)

    # zatrzymanie kamery po śmierci
    camera_running = False
    if thread is not None and thread.is_alive():
        thread.join(timeout=1.0)

    game_over_screen(score // 10)
    return


if __name__ == "__main__":
    run_dino_camera_game()
