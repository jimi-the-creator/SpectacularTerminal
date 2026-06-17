import pygame
from pathlib import Path
import random
import math
import array

pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.init()
pygame.mixer.set_num_channels(48)

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
# SOUND LAYER — HACKER TECH CLICK VERSION
# ----------------------------

def clamp(value, low=-32767, high=32767):
    return max(low, min(high, value))


def make_hacker_click(
    high_freq=2200,
    body_freq=520,
    duration_ms=22,
    volume=0.34,
    noise_amount=0.62,
    body_amount=0.34,
    spark_amount=0.18
):
    sample_rate = 44100
    n_samples = int(sample_rate * duration_ms / 1000)
    samples = array.array("h")

    # Tiny stereo variation makes it feel less flat
    pan_offset = random.uniform(-0.08, 0.08)
    left_gain = 1.0 - max(0, pan_offset)
    right_gain = 1.0 + min(0, pan_offset)

    last_noise = 0.0

    for i in range(n_samples):
        t = i / sample_rate

        # Instant switch-like attack
        attack = min(1.0, t / 0.0009)

        # Sharp electric transient
        transient_env = attack * math.exp(-360 * t)

        # Short mechanical body
        body_env = attack * math.exp(-105 * t)

        # Tiny digital sparkle
        spark_env = attack * math.exp(-520 * t)

        # Filtered-ish noise: less hiss, more click
        raw_noise = random.uniform(-1.0, 1.0)
        filtered_noise = (raw_noise * 0.72) + (last_noise * 0.28)
        last_noise = filtered_noise

        noise = filtered_noise * transient_env * noise_amount

        # High tick gives the hacker/cyberdeck feel
        high_tick = math.sin(2 * math.pi * high_freq * t) * transient_env * spark_amount

        # Low body makes it feel like a real key, not just static
        body = math.sin(2 * math.pi * body_freq * t) * body_env * body_amount

        # Subtle square-ish edge for technical sharpness
        edge_wave = 1.0 if math.sin(2 * math.pi * (high_freq * 0.55) * t) > 0 else -1.0
        edge = edge_wave * spark_env * 0.08

        signal = noise + high_tick + body + edge

        value = int(32767 * volume * signal)
        value = clamp(value)

        samples.append(int(value * left_gain))
        samples.append(int(value * right_gain))

    return pygame.mixer.Sound(buffer=samples.tobytes())


key_sounds = [
    make_hacker_click(
        high_freq=random.randint(1800, 3200),
        body_freq=random.randint(430, 720),
        duration_ms=random.randint(14, 24),
        volume=random.uniform(0.26, 0.38),
        noise_amount=random.uniform(0.55, 0.72),
        body_amount=random.uniform(0.24, 0.38),
        spark_amount=random.uniform(0.14, 0.24)
    )
    for _ in range(24)
]

backspace_sounds = [
    make_hacker_click(
        high_freq=random.randint(1200, 2200),
        body_freq=random.randint(260, 460),
        duration_ms=random.randint(22, 34),
        volume=random.uniform(0.34, 0.46),
        noise_amount=random.uniform(0.45, 0.62),
        body_amount=random.uniform(0.40, 0.58),
        spark_amount=random.uniform(0.08, 0.16)
    )
    for _ in range(8)
]

enter_sounds = [
    make_hacker_click(
        high_freq=random.randint(900, 1700),
        body_freq=random.randint(180, 340),
        duration_ms=random.randint(36, 56),
        volume=random.uniform(0.40, 0.55),
        noise_amount=random.uniform(0.34, 0.50),
        body_amount=random.uniform(0.55, 0.72),
        spark_amount=random.uniform(0.06, 0.12)
    )
    for _ in range(6)
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
