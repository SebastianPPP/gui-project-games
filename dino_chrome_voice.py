import pygame
import random
import sys
import threading 
import time
import pyaudio 
import numpy as np 
import struct

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
pygame.display.set_caption('Dino Run')
clock = pygame.time.Clock()

CHUNK_SIZE = 512            
FORMAT = pyaudio.paInt16     
CHANNELS = 1                 
RATE = 44100                 
AMPLITUDE_THRESHOLD = 15000  # Próg głośności

pa = pyaudio.PyAudio()
voice_jump_flag = False 
audio_running = False  

def get_default_microphone():
    """Automatycznie wykrywa i zwraca indeks domyślnego mikrofonu."""
    try:
        default_mic = pa.get_default_input_device_info()
        mic_index = default_mic['index']
        mic_name = default_mic['name']
        print(f"Automatycznie wykryto mikrofon: {mic_name}")
        return mic_index
    except Exception as e:
        print(f"Nie można wykryć domyślnego mikrofonu: {e}")
        for i in range(pa.get_device_count()):
            try:
                device_info = pa.get_device_info_by_index(i)
                if device_info['maxInputChannels'] > 0:
                    print(f"Znaleziono mikrofon: {device_info['name']}")
                    return i
            except:
                continue
        print("Nie znaleziono żadnego mikrofonu!")
        return None

def voice_control_dino(mic_index): 
    """Monitoruje głośność mikrofonu i ustawia flagę skoku po przekroczeniu progu."""
    global voice_jump_flag, audio_running
    
    stream = None
    try:
        mic_info = pa.get_device_info_by_index(mic_index)
        mic_name = mic_info.get('name', 'Nieznany')
        print(f"Mikrofon: {mic_name} \n")
        
        stream = pa.open(format=FORMAT,
                         channels=CHANNELS,
                         rate=RATE,
                         input=True,
                         frames_per_buffer=CHUNK_SIZE,
                         input_device_index=mic_index)
        
        print(f"Monitorowanie głośności")

        while audio_running:
            data = stream.read(CHUNK_SIZE, exception_on_overflow=False)
            
            data_int = struct.unpack(str(CHUNK_SIZE) + 'h', data) 
            
            max_amplitude = np.max(np.abs(data_int))
            
            # Sprawdzenie Progu
            if max_amplitude > AMPLITUDE_THRESHOLD:
                print(f"Głośność {max_amplitude} -> SKOK!")
                voice_jump_flag = True
                
            time.sleep(0.001) 

    except Exception as e:
        print(f"Błąd monitorowania audio: {e}")
        time.sleep(5) 
    finally:
        if stream and stream.is_active():
             stream.stop_stream()
             stream.close()

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

def run_dino_game(mic_index=None):
    global voice_jump_flag
    
    mic_name = "Klawiatura"
    if mic_index is None:
        mic_index = get_default_microphone()
        if mic_index is None:
            print("Gra uruchomi się bez sterowania głosem.")
        else:
            mic_info = pa.get_device_info_by_index(mic_index)
            mic_name = mic_info.get('name', 'Mikrofon')
    else:
        mic_info = pa.get_device_info_by_index(mic_index)
        mic_name = mic_info.get('name', 'Mikrofon')
    
    dino = Dino()
    all_sprites = pygame.sprite.Group()
    cacti_group = pygame.sprite.Group()
    all_sprites.add(dino)

    game_active = True
    score = 0
    obstacle_speed = 5
    
    SPAWN_CACTUS = pygame.USEREVENT + 1
    pygame.time.set_timer(SPAWN_CACTUS, 1500) 

    thread = None
    if mic_index is not None:
        voice_jump_flag = False
        audio_running = True
        thread = threading.Thread(target=voice_control_dino, args=(mic_index,), name="DinoAmplitudeControl")
        thread.daemon = True
        thread.start()
        print("Aby skoczyć należy wydać głośny dźwięk np. klaśnięcie lub HOP!.")
    else:
        print("Użyj SPACJI lub STRZAŁKI W GÓRĘ aby skoczyć.")

    while game_active:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return 
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE or event.key == pygame.K_UP:
                    dino.jump()

            if event.type == SPAWN_CACTUS:
                cacti_group.add(Cactus(obstacle_speed))
                all_sprites.add(cacti_group.sprites()[-1])
        
        if voice_jump_flag:
            dino.jump() 
            voice_jump_flag = False 

        if pygame.sprite.spritecollide(dino, cacti_group, False):
            game_active = False 

        if game_active:
            all_sprites.update()
            
            score += 1
            if score % 500 == 0:
                obstacle_speed += 0.5
                pygame.time.set_timer(SPAWN_CACTUS, max(500, 1500 - (score // 10))) 

        screen.fill(BACKGROUND_COLOR)
        pygame.draw.line(screen, SCORE_COLOR, (0, GROUND_LEVEL), (SCREEN_WIDTH, GROUND_LEVEL), 2) 
        all_sprites.draw(screen)
        display_score(score // 10)        
        pygame.display.flip()
        clock.tick(FPS)

    # zatrzymaj wątek audio przed powrotem do menu
    if mic_index is not None:
        audio_running = False
        if thread is not None:
            thread.join(timeout=1.0)

    game_over_screen(score // 10)
    return 

if __name__ == '__main__':
    run_dino_game()  # Automatyczne wykrywanie