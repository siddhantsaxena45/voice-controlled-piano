import pygame
import sys
import queue
import sounddevice as sd
import vosk
import json
import threading
import time

pygame.init()
should_quit = False
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Voice-Controlled Piano")
font = pygame.font.SysFont(None, 48)

background = pygame.image.load("background.jpg")
background = pygame.transform.smoothscale(background, (800, 600))

key_images = []
key_rects = []
for i in range(10):
    image = pygame.image.load(f"key{i}.png")
    key_images.append(image)
    key_rects.append(pygame.Rect(50 + i * 70, 300, image.get_width(), image.get_height()))


sounds = []
for i in range(10):
    sound = pygame.mixer.Sound(f"note{i}.wav")
    sounds.append(sound)


model = vosk.Model("model")
q = queue.Queue()

def callback(indata, frames, time, status):
    if status:
        print("Sounddevice status:", status)
    q.put(bytes(indata))

def recognize_speech():
    with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16',
                           channels=1, callback=callback):
        rec = vosk.KaldiRecognizer(model, 16000)
        print("Voice recognition started. Speak into the microphone.")
        while True:
            data = q.get()
            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                text = result.get("text", "")
                if text:
                    print(f"Recognized voice command: {text}")  
                    process_command(text)

highlighted_key = -1
highlight_time = 0
game_started = False
game_ended = False

def play_key(index):
    global highlighted_key, highlight_time
    if 0 <= index < len(sounds):
        sounds[index].play()
        highlighted_key = index
        highlight_time = time.time()

word_to_digit = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4,
    "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9
}

def process_command(command):
    global game_started, game_ended
    command = command.lower()
    if "start game" in command:
        game_started = True
        game_ended = False
    elif "end game" in command:
        game_started = False
        game_ended = True
    elif "close" in command:
        print("Close command received.")
        global should_quit
        should_quit = True
    elif game_started:
        # Extract digits and words mapped to digits
        numbers = []
        for s in command.split():
            if s.isdigit():
                numbers.append(int(s))
            elif s in word_to_digit:
                numbers.append(word_to_digit[s])
        for num in numbers:
            play_key(num)
            pygame.time.delay(500)


threading.Thread(target=recognize_speech, daemon=True).start()

running = True
while running:
    screen.blit(background, (0, 0))
    current_time = time.time()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if not game_started and not game_ended:
                if event.key in [pygame.K_RETURN, pygame.K_SPACE]:
                    game_started = True
                elif event.key == pygame.K_ESCAPE:
                    running = False

            elif game_started:
                if event.key == pygame.K_ESCAPE:
                    game_started = False
                    game_ended = True
                elif pygame.K_0 <= event.key <= pygame.K_9:
                    play_key(event.key - pygame.K_0)

            elif game_ended:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key in [pygame.K_RETURN, pygame.K_SPACE]:
                    game_started = True
                    game_ended = False

        if game_started and event.type == pygame.MOUSEBUTTONDOWN:
            pos = pygame.mouse.get_pos()
            for i, rect in enumerate(key_rects):
                if rect.collidepoint(pos):
                    play_key(i)

    if not game_started and not game_ended:
        text = font.render("Say or press Enter/Space to 'start game'", True, (255, 255, 255))
        screen.blit(text, (120, 250))
        hint = font.render("Press ESC to quit", True, (200, 200, 200))
        screen.blit(hint, (260, 310))

    elif game_started:
        for i, img in enumerate(key_images):
            x, y = 50 + i * 70, 300
            screen.blit(img, (x, y))
            if i == highlighted_key and (current_time - highlight_time < 0.3):
                pygame.draw.rect(screen, (255, 255, 0), key_rects[i], 5)


    elif game_ended:
        end_text = font.render("Game Ended", True, (255, 255, 255))
        restart = font.render("Say or press Enter/Space to Restart", True, (200, 200, 200))
        close = font.render("Press ESC to Exit", True, (200, 200, 200))
        screen.blit(end_text, (300, 220))
        screen.blit(restart, (160, 280))
        screen.blit(close, (260, 340))
    if should_quit:
        running = False
    pygame.display.flip()

pygame.quit()
