import pygame
import sys
import vc_snake 
import dino_chrome as dino_game 

WINDOW_WIDTH = 720
WINDOW_HEIGHT = 480
WHITE = pygame.Color(255, 255, 255)
BLACK = pygame.Color(0, 0, 0)
GREEN = pygame.Color(0, 255, 0)
food_spawn = True
pygame.init()
menu_window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption('Menu')
font_style = pygame.font.SysFont('times new roman', 30)

def draw_text(text, font, color, surface, x, y):
    textobj = font.render(text, 1, color)
    textrect = textobj.get_rect()
    textrect.center = (x, y)
    surface.blit(textobj, textrect)

def main_menu():
    selected_game = 1 
    options = ["1. Snake (wideo)", "2. Dino (głosowy)", "ESC - Wyjście"]
    
    while True:
        menu_window.fill(BLACK)
        draw_text('Main Menu', font_style, WHITE, menu_window, WINDOW_WIDTH/2, 50)
        
        for i, option in enumerate(options):
            color = GREEN if i + 1 == selected_game else WHITE
            draw_text(option, font_style, color, menu_window, WINDOW_WIDTH/2, 
                      WINDOW_HEIGHT/2 + i * 50 - 50) 

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                
                if event.key == pygame.K_DOWN:
                    selected_game = selected_game % 2 + 1
                if event.key == pygame.K_UP:
                    selected_game = (selected_game - 2) % 2 + 1 
                
                if event.key == pygame.K_ESCAPE: 
                    pygame.quit()
                    sys.exit()
                
                if event.key == pygame.K_RETURN: 
                    if selected_game == 1:
                        vc_snake.run_game()  # Automatyczne wykrywanie
                    elif selected_game == 2:
                        dino_game.run_dino_game()  # Automatyczne wykrywanie
                
                # Szybkie skróty klawiszowe
                if event.key == pygame.K_1:
                    vc_snake.run_game()
                if event.key == pygame.K_2:
                    dino_game.run_dino_game()


        pygame.display.update()
        pygame.time.Clock().tick(15) 

if __name__ == '__main__':
    main_menu()