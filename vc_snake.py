import pygame
import time
import random

# game config
SNAKE_SPEED = 5
WINDOW_WIDTH = 720
WINDOW_HEIGHT = 480

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
    run_game()