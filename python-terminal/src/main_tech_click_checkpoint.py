import pygame
from pathlib import Path
import random
import math
import array

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
# SOUND LAYER — TECH CLICK VERSION
# ----------------------------

def clamp(value, low=-32767, high=32767):
    return max(low, min(high, value))


def make_tech_click(
    tone_freq=950,
    duration_ms=18,
    volume=0.32,
    noise_mix=0.70,
    body_mix=0.30
):
    sample_rate = 44100
    n_samples = int(sample_rate * duration_ms / 1000)
    samples = array.array("h")

    for i in range(n_samples):
        t = i / sample_rate

        # Very fast attack so it feels like a physical switch
        attack = min(1.0, t / 0.0015)

        # Sharp noisy transient = tech click
        transient_env = attack * math.exp(-240 * t)

        # Tiny body so it does not sound like pure static
        body_env = attack * math.exp(-85 * t)

        noise = random.uniform(-1.0, 1.0) * transient_env * noise_mix

        body = (
            math.sin(2 * math.pi * tone_freq * t) * body_env * body_mix +
            math.sin(2 * math.pi * tone_freq * 2.4 * t) * transient_env * 0.08
        )

        signal = noise + body
        value = int(32767 * volume * signal)
        value = clamp(value)

        samples.append(value)
        samples.append(value)

    return pygame.mixer.Sound(buffer=samples.tobytes())


key_sounds = [
    make_tech_click(
        tone_freq=random.randint(850, 1450),
        duration_ms=random.randint(12, 20),
        volume=random.uniform(0.24, 0.36),
        noise_mix=random.uniform(0.62, 0.78),
        body_mix=random.uniform(0.22, 0.34)
    )
    for _ in range(18)
]

backspace_sounds = [
    make_tech_click(
        tone_freq=random.randint(420, 700),
        duration_ms=random.randint(18, 28),
        volume=random.uniform(0.30, 0.42),
        noise_mix=random.uniform(0.55, 0.70),
        body_mix=random.uniform(0.35, 0.48)
    )
    for _ in range(6)
]

enter_sounds = [
    make_tech_click(
        tone_freq=random.randint(260, 440),
        duration_ms=random.randint(28, 44),
        volume=random.uniform(0.36, 0.50),
        noise_mix=random.uniform(0.45, 0.60),
        body_mix=random.uniform(0.45, 0.58)
    )
    for _ in range(5)
]


def play_random(sound_bank):
    if sound_bank:
        random.choice(sound_bank).play()


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
                play_random(backspace_sounds)

            elif event.key == pygame.K_RETURN:
                buffer += "\n"
                play_random(enter_sounds)

            elif event.unicode:
                buffer += event.unicode
                play_random(key_sounds)

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
