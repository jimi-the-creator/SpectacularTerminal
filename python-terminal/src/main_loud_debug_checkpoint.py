import pygame
from pathlib import Path
import random
import math
import array

# Audio setup
pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.init()
pygame.mixer.set_num_channels(32)

print("Mixer initialized as:", pygame.mixer.get_init())

BASE_DIR = Path(__file__).resolve().parent.parent
FRAME_PATH = BASE_DIR / "assets" / "frame.png"

frame = pygame.image.load(FRAME_PATH)

WIDTH, HEIGHT = frame.get_size()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
frame = frame.convert()

pygame.display.set_caption("Spectacular Terminal")

clock = pygame.time.Clock()

TERMINAL_RECT = pygame.Rect(165, 95, 1340, 690)

PADDING_X = 35
PADDING_Y = 35

TEXT_COLOR = (120, 255, 235)
GLOW_COLOR = (40, 180, 170)
CURSOR_COLOR = (120, 255, 235)

font = pygame.font.SysFont("menlo", 28)
if font is None:
    font = pygame.font.SysFont("monospace", 28)

buffer = ""
cursor_visible = True
cursor_timer = 0


# ----------------------------
# SOUND LAYER — LOUD DEBUG VERSION
# ----------------------------

def make_tone(freq=650, duration_ms=180, volume=0.8):
    sample_rate = 44100
    n_samples = int(sample_rate * duration_ms / 1000)
    samples = array.array("h")

    for i in range(n_samples):
        t = i / sample_rate

        # This is intentionally audible, like the working sound_test.py
        envelope = math.exp(-8 * t)
        wave = math.sin(2 * math.pi * freq * t)

        value = int(32767 * volume * wave * envelope)

        samples.append(value)
        samples.append(value)

    return pygame.mixer.Sound(buffer=samples.tobytes())


key_sounds = [
    make_tone(
        freq=random.randint(550, 850),
        duration_ms=random.randint(90, 140),
        volume=0.65
    )
    for _ in range(8)
]

backspace_sounds = [
    make_tone(
        freq=random.randint(300, 480),
        duration_ms=random.randint(120, 180),
        volume=0.75
    )
    for _ in range(4)
]

enter_sounds = [
    make_tone(
        freq=random.randint(220, 360),
        duration_ms=random.randint(180, 260),
        volume=0.85
    )
    for _ in range(4)
]


def play_random(sound_bank, label):
    sound = random.choice(sound_bank)
    channel = sound.play()
    print(f"played {label}:", channel)


# Startup sound test
startup_sound = make_tone(freq=650, duration_ms=400, volume=0.9)
startup_sound.play()
pygame.time.delay(500)


# ----------------------------
# TEXT RENDERING
# ----------------------------

def wrap_text(text, font, max_width):
    wrapped_lines = []

    for raw_line in text.split("\n"):
        current = ""

        for char in raw_line:
            test_line = current + char

            if font.size(test_line)[0] <= max_width:
                current = test_line
            else:
                wrapped_lines.append(current)
                current = char

        wrapped_lines.append(current)

    return wrapped_lines


def draw_glow_text(surface, text, pos):
    x, y = pos

    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        glow = font.render(text, True, GLOW_COLOR)
        glow.set_alpha(80)
        surface.blit(glow, (x + dx, y + dy))

    rendered = font.render(text, True, TEXT_COLOR)
    surface.blit(rendered, (x, y))


# ----------------------------
# MAIN LOOP
# ----------------------------

running = True

while running:
    dt = clock.tick(60)
    cursor_timer += dt

    if cursor_timer >= 500:
        cursor_visible = not cursor_visible
        cursor_timer = 0

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False

            elif event.key == pygame.K_BACKSPACE:
                buffer = buffer[:-1]
                play_random(backspace_sounds, "backspace")

            elif event.key == pygame.K_RETURN:
                buffer += "\n"
                play_random(enter_sounds, "enter")

            elif event.unicode:
                buffer += event.unicode
                play_random(key_sounds, "key")

    screen.blit(frame, (0, 0))

    overlay = pygame.Surface((TERMINAL_RECT.width, TERMINAL_RECT.height), pygame.SRCALPHA)
    overlay.fill((0, 25, 22, 28))
    screen.blit(overlay, TERMINAL_RECT.topleft)

    text_x = TERMINAL_RECT.x + PADDING_X
    text_y = TERMINAL_RECT.y + PADDING_Y
    max_text_width = TERMINAL_RECT.width - (PADDING_X * 2)

    lines = wrap_text(buffer, font, max_text_width)

    line_height = 36
    max_visible_lines = (TERMINAL_RECT.height - (PADDING_Y * 2)) // line_height
    visible_lines = lines[-max_visible_lines:]

    y = text_y

    for line in visible_lines:
        draw_glow_text(screen, line, (text_x, y))
        y += line_height

    current_line = visible_lines[-1] if visible_lines else ""
    cursor_x = text_x + font.size(current_line)[0] + 4
    cursor_y = y - line_height + 4

    if cursor_visible:
        pygame.draw.rect(screen, CURSOR_COLOR, (cursor_x, cursor_y, 14, 28))

    pygame.display.flip()

pygame.quit()
