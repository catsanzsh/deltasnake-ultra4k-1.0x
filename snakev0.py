import os
import sys
import tkinter as tk
import pygame
import random
import math
from array import array

class SoundManager:
    """
    Manages game sounds by generating simple, retro-style tones (chiptune)
    to mimic classic Famicom/8-bit sound effects.
    """
    def __init__(self):
        # Initialize pygame's mixer at a high quality sample rate.
        pygame.mixer.init(frequency=44100, size=-16, channels=1)
        
        # Pre-generate the sound effects to avoid lag during gameplay.
        # A high-pitched, short square wave for eating food.
        self.eat_sound = self._make_sound(freq=1200, duration=0.05, volume=0.4, shape='square')
        # A low-pitched, descending sawtooth wave for game over.
        self.death_sound = self._make_sound(freq=400, duration=0.5, volume=0.5, shape='sawtooth', decay=True)

    def _make_sound(self, freq, duration, volume, shape='sine', decay=False):
        """
        Internal method to generate a raw audio buffer for a sound.
        
        Args:
            freq (int): The base frequency of the sound in Hz.
            duration (float): The length of the sound in seconds.
            volume (float): The volume, from 0.0 to 1.0.
            shape (str): The waveform shape ('sine', 'square', 'sawtooth').
            decay (bool): If True, the frequency will drop over the duration.
        """
        sample_rate = pygame.mixer.get_init()[0]
        n_samples = int(round(duration * sample_rate))
        
        # Create a buffer array to hold the sound wave data.
        buf = array('h', [0] * n_samples)
        max_amp = int(32767 * volume)

        for i in range(n_samples):
            # Calculate time 't' for the wave function.
            t = float(i) / sample_rate
            
            # Apply frequency decay if enabled.
            current_freq = freq * (1 - t / duration) if decay else freq
            
            # Generate the waveform based on the selected shape.
            if shape == 'square':
                val = max_amp if math.sin(2 * math.pi * current_freq * t) > 0 else -max_amp
            elif shape == 'sawtooth':
                # Creates a saw wave that resets every period.
                val = max_amp * (2 * (t * current_freq - math.floor(0.5 + t * current_freq)))
            else: # Default to sine wave
                val = max_amp * math.sin(2 * math.pi * current_freq * t)
            
            buf[i] = int(val)
            
        return pygame.mixer.Sound(buffer=buf)

    def play_eat(self):
        """Plays the pre-generated 'eat' sound effect."""
        self.eat_sound.play()

    def play_death(self):
        """Plays the pre-generated 'death' sound effect."""
        self.death_sound.play()

class SnakeGame:
    """
    A classic Snake game embedded in a Tkinter window.
    Uses Pygame for rendering, input, and audio, and supports both
    mouse and keyboard controls.
    """
    def __init__(self):
        # --- Tkinter Window Setup ---
        self.root = tk.Tk()
        self.root.title("#! ULTRA SNAKE 20XX")
        # Ensure the window closes gracefully.
        self.root.protocol("WM_DELETE_WINDOW", self._quit)
        
        # --- Pygame Embedding ---
        # Create a frame in the Tkinter window to hold the pygame display.
        self.embed = tk.Frame(self.root, width=600, height=400)
        self.embed.pack()
        
        # Set environment variables to tell SDL (used by pygame) to draw in our frame.
        os.environ['SDL_WINDOWID'] = str(self.embed.winfo_id())
        os.environ['SDL_VIDEODRIVER'] = 'windib'
        
        # --- Pygame Initialization ---
        pygame.init()
        pygame.display.set_caption("#! ULTRA SNAKE 20XX [C] Team Flames")
        self.screen = pygame.display.set_mode((600, 400))
        self.clock = pygame.time.Clock()
        self.sound = SoundManager()

        # --- Game Parameters ---
        self.fps = 60
        self.move_rate = 10  # Snake moves 10 times per second
        self.frames_per_move = self.fps // self.move_rate
        self.frame_count = 0

        self.cell_size = 20
        self.grid_width = 600 // self.cell_size
        self.grid_height = 400 // self.cell_size

        # --- Fonts and State ---
        self.title_font = pygame.font.Font(pygame.font.get_default_font(), 36)
        self.text_font = pygame.font.Font(pygame.font.get_default_font(), 24)
        self.state = 'menu'  # Game states: 'menu', 'playing', 'gameover'
        
        self.reset()

    def reset(self):
        """Resets the game to its initial state."""
        self.snake = [(self.grid_width // 2, self.grid_height // 2)]
        self.direction = (1, 0)
        self.next_direction = (1, 0)
        self.spawn_food()
        self.score = 0
        self.game_over = False
        self.frame_count = 0 # Reset frame count for move timing

    def spawn_food(self):
        """Places food in a random, unoccupied cell on the grid."""
        while True:
            pos = (random.randrange(self.grid_width), random.randrange(self.grid_height))
            if pos not in self.snake:
                self.food = pos
                return

    def handle_input(self):
        """Processes all user input from both mouse and keyboard."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._quit()
            
            # --- Menu and Game Over Input ---
            if self.state == 'menu' and event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                self.state = 'playing'
                self.reset()
            elif self.state == 'gameover' and event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_y, pygame.K_RETURN):
                    self.state = 'playing'
                    self.reset()
                elif event.key == pygame.K_n:
                    self._quit()

            # --- In-Game Keyboard Input ---
            if self.state == 'playing' and event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_UP, pygame.K_w) and self.direction[1] == 0:
                    self.next_direction = (0, -1)
                elif event.key in (pygame.K_DOWN, pygame.K_s) and self.direction[1] == 0:
                    self.next_direction = (0, 1)
                elif event.key in (pygame.K_LEFT, pygame.K_a) and self.direction[0] == 0:
                    self.next_direction = (-1, 0)
                elif event.key in (pygame.K_RIGHT, pygame.K_d) and self.direction[0] == 0:
                    self.next_direction = (1, 0)

        # --- In-Game Mouse Input ---
        if self.state == 'playing':
            mx, my = pygame.mouse.get_pos()
            head_x, head_y = self.snake[0]
            # Convert grid coordinates to pixel coordinates for comparison.
            head_px = head_x * self.cell_size + self.cell_size / 2
            head_py = head_y * self.cell_size + self.cell_size / 2
            
            dx, dy = mx - head_px, my - head_py
            
            # Determine dominant axis of mouse movement relative to the snake head.
            if abs(dx) > abs(dy):
                new_dir = (1 if dx > 0 else -1, 0)
            else:
                new_dir = (0, 1 if dy > 0 else -1)

            # Update direction if it's not a direct reversal.
            if new_dir != (-self.direction[0], -self.direction[1]):
                self.next_direction = new_dir


    def update(self):
        """Updates the game logic, such as moving the snake and checking for collisions."""
        self.direction = self.next_direction
        head = self.snake[0]
        new_head = (head[0] + self.direction[0], head[1] + self.direction[1])

        # Check for collisions with walls or self.
        if (new_head in self.snake or
            not 0 <= new_head[0] < self.grid_width or
            not 0 <= new_head[1] < self.grid_height):
            self.sound.play_death()
            self.game_over = True
            self.state = 'gameover'
            return
            
        self.snake.insert(0, new_head)
        
        # Check for eating food.
        if new_head == self.food:
            self.score += 1
            self.sound.play_eat()
            self.spawn_food()
        else:
            self.snake.pop()

    def draw(self):
        """Handles all rendering to the screen based on the current game state."""
        self.screen.fill((20, 20, 30)) # Dark blue background

        if self.state == 'menu':
            self.draw_menu()
        elif self.state == 'playing':
            self.draw_game()
        elif self.state == 'gameover':
            self.draw_gameover()
        
        pygame.display.update()
        # Update the Tkinter window to ensure it remains responsive.
        self.root.update()

    def draw_menu(self):
        """Draws the main menu screen."""
        title = self.title_font.render("#! ULTRA SNAKE 20XX", True, (0, 255, 128))
        self.screen.blit(title, ((600 - title.get_width()) // 2, 140))
        
        prompt = self.text_font.render("Click or Press Any Key to Start", True, (255, 255, 0))
        self.screen.blit(prompt, ((600 - prompt.get_width()) // 2, 220))
        
        footer = self.text_font.render("20XX [C] - Team Flames", True, (150, 150, 150))
        self.screen.blit(footer, ((600 - footer.get_width()) // 2, 360))

    def draw_game(self):
        """Draws the game elements: snake, food, and score."""
        # Draw snake with a slight border effect
        for x, y in self.snake:
            pygame.draw.rect(self.screen, (0, 150, 50), 
                             (x * self.cell_size, y * self.cell_size, self.cell_size, self.cell_size))
            pygame.draw.rect(self.screen, (0, 255, 100), 
                             (x * self.cell_size + 2, y * self.cell_size + 2, self.cell_size - 4, self.cell_size - 4))
        
        # Draw food (apple)
        fx, fy = self.food
        pygame.draw.rect(self.screen, (255, 0, 0), 
                         (fx * self.cell_size, fy * self.cell_size, self.cell_size, self.cell_size))

        # Draw score
        score_text = self.text_font.render(f"Score: {self.score}", True, (255, 255, 255))
        self.screen.blit(score_text, (10, 10))

    def draw_gameover(self):
        """Draws the game over screen."""
        lose = self.title_font.render("YOU LOSE", True, (255, 0, 0))
        self.screen.blit(lose, ((600 - lose.get_width()) // 2, 140))

        final_score = self.text_font.render(f"Final Score: {self.score}", True, (255, 255, 255))
        self.screen.blit(final_score, ((600-final_score.get_width())//2, 220))

        prompt = self.text_font.render("Restart? (Y/N)", True, (255, 255, 0))
        self.screen.blit(prompt, ((600 - prompt.get_width()) // 2, 280))

    def run(self):
        """The main game loop."""
        while True:
            self.handle_input()
            
            if self.state == 'playing':
                # Control snake speed independently of frame rate
                self.frame_count += 1
                if self.frame_count >= self.frames_per_move:
                    self.frame_count = 0
                    self.update()
            
            self.draw()
            self.clock.tick(self.fps)

    def _quit(self):
        """A clean exit function to close both pygame and tkinter."""
        pygame.quit()
        self.root.destroy()
        sys.exit()

if __name__ == '__main__':
    game = SnakeGame()
    game.run()
