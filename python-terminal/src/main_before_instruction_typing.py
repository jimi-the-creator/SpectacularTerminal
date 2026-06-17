import pygame
from pathlib import Path
import random

# ----------------------------
# INIT
# ----------------------------

pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.init()
pygame.mixer.set_num_channels(48)

print("Mixer initialized as:", pygame.mixer.get_init())

BASE_DIR = Path(__file__).resolve().parent.parent
FRAME_PATH = BASE_DIR / "assets" / "frame.png"
SOUND_DIR = BASE_DIR / "sounds"

try:
    frame = pygame.image.load(FRAME_PATH)
    WIDTH, HEIGHT = frame.get_size()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    frame = frame.convert()
except FileNotFoundError:
    print(f"Asset not found at {FRAME_PATH}. Using a default 1600x900 window.")
    WIDTH, HEIGHT = 1600, 900
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    frame = pygame.Surface((WIDTH, HEIGHT))
    frame.fill((10, 15, 12))

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


# ----------------------------
# SOUND LAYER
# ----------------------------

def load_sound(filename, volume=0.35):
    path = SOUND_DIR / filename

    if not path.exists():
        raise FileNotFoundError(f"Missing sound file: {path}")

    sound = pygame.mixer.Sound(str(path))
    sound.set_volume(volume)
    return sound


key_clicks = []

for i in range(1, 7):
    filename = f"key_{i:02}.wav"
    path = SOUND_DIR / filename
    if path.exists():
        key_clicks.append(load_sound(filename, 0.34))

if not key_clicks:
    raise FileNotFoundError("No key_01.wav/key_02.wav/etc files found in python-terminal/sounds")

backspace_click = load_sound("backspace.wav", 0.42)
enter_click = load_sound("enter.wav", 0.48)


def play_key_click():
    random.choice(key_clicks).play()


def play_backspace_click():
    backspace_click.play()


def play_enter_click():
    enter_click.play()


# ----------------------------
# APP STATE
# ----------------------------

STATE_BOOTING = "BOOTING"
STATE_MENU = "MENU"
STATE_LOADING_CONSTRAINT = "LOADING_CONSTRAINT"
STATE_LOADING_REFINEMENT = "LOADING_REFINEMENT"
STATE_CONSTRAINT = "CONSTRAINT"
STATE_REFINEMENT = "REFINEMENT"

state = STATE_BOOTING

boot_script = (
    "SPECTACULAR TERMINAL INITIALIZING...\n"
    "LOCAL MODE ENABLED\n"
    "SENSORY INPUT LAYER ONLINE\n"
    "FLAG DETECTION CORE STANDBY\n"
    "\n"
    "SELECT OPERATION:\n"
    "\n"
    "[1] CONSTRAINT CONFLICT TEST\n"
    "[2] PROMPT REFINEMENT\n"
    "\n"
    "ENTER MODE:\n"
    "> "
)

constraint_load_script = (
    "LOADING CONSTRAINT CONFLICT TEST MODULE...\n"
    "CONSTRAINT ENGINE ONLINE\n"
    "ADVERSARIAL EVALUATION PATH READY\n"
    "STRICT INSTRUCTION MONITOR STANDBY\n"
    "\n"
)

refinement_load_script = (
    "LOADING PROMPT REFINEMENT MODULE...\n"
    "REFINEMENT ENGINE ONLINE\n"
    "FLAG DETECTION PATH READY\n"
    "PROMPT REWRITE CORE STANDBY\n"
    "\n"
)

boot_index = 0
boot_text = ""

load_index = 0
load_text = ""
active_load_script = ""
next_state_after_load = None

type_timer = 0
type_delay_ms = 24

buffer = ""
cursor_visible = True
cursor_timer = 0


# ----------------------------
# STATE HELPERS
# ----------------------------

def begin_constraint_loading():
    global state, load_index, load_text, active_load_script, next_state_after_load, buffer

    state = STATE_LOADING_CONSTRAINT
    load_index = 0
    load_text = ""
    active_load_script = constraint_load_script
    next_state_after_load = STATE_CONSTRAINT
    buffer = ""


def begin_refinement_loading():
    global state, load_index, load_text, active_load_script, next_state_after_load, buffer

    state = STATE_LOADING_REFINEMENT
    load_index = 0
    load_text = ""
    active_load_script = refinement_load_script
    next_state_after_load = STATE_REFINEMENT
    buffer = ""


def reset_to_menu():
    global state, buffer

    state = STATE_MENU
    buffer = ""


# ----------------------------
# TEXT HELPERS
# ----------------------------

def wrap_text(text, font_obj, max_width):
    wrapped_lines = []

    for raw_line in text.split("\n"):
        current = ""

        for char in raw_line:
            test_line = current + char

            if font_obj.size(test_line)[0] <= max_width:
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


def get_screen_text():
    if state == STATE_BOOTING:
        return boot_text

    if state == STATE_MENU:
        return boot_script + buffer

    if state == STATE_LOADING_CONSTRAINT:
        return load_text

    if state == STATE_LOADING_REFINEMENT:
        return load_text

    if state == STATE_CONSTRAINT:
        return (
            "MODE: CONSTRAINT CONFLICT TEST\n"
            "\n"
            "Purpose: pressure-test an LLM under strict instruction constraints.\n"
            "\n"
            "Enter a constraint to test:\n"
            "> " + buffer
        )

    if state == STATE_REFINEMENT:
        return (
            "MODE: PROMPT REFINEMENT\n"
            "\n"
            "Purpose: detect weak framing, hidden flags, and refine prompts.\n"
            "\n"
            "Enter a prompt for flag detection and refinement:\n"
            "> " + buffer
        )

    return buffer


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

    # Boot auto-typing
    if state == STATE_BOOTING:
        type_timer += dt

        if type_timer >= type_delay_ms and boot_index < len(boot_script):
            type_timer = 0
            char = boot_script[boot_index]
            boot_text += char
            boot_index += 1

            if char not in ["\n", " "]:
                play_key_click()

        if boot_index >= len(boot_script):
            state = STATE_MENU
            buffer = ""

    # Module loading auto-typing
    elif state in [STATE_LOADING_CONSTRAINT, STATE_LOADING_REFINEMENT]:
        type_timer += dt

        if type_timer >= type_delay_ms and load_index < len(active_load_script):
            type_timer = 0
            char = active_load_script[load_index]
            load_text += char
            load_index += 1

            if char not in ["\n", " "]:
                play_key_click()

        if load_index >= len(active_load_script):
            state = next_state_after_load
            buffer = ""

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False

            # Ignore keyboard input while booting or loading modules
            if state in [STATE_BOOTING, STATE_LOADING_CONSTRAINT, STATE_LOADING_REFINEMENT]:
                continue

            elif state == STATE_MENU:
                if event.unicode == "1":
                    play_enter_click()
                    begin_constraint_loading()

                elif event.unicode == "2":
                    play_enter_click()
                    begin_refinement_loading()

                elif event.key == pygame.K_BACKSPACE:
                    buffer = buffer[:-1]
                    play_backspace_click()

                elif event.key == pygame.K_RETURN:
                    play_enter_click()

                elif event.unicode and event.unicode.isprintable():
                    buffer += event.unicode
                    play_key_click()

            elif state in [STATE_CONSTRAINT, STATE_REFINEMENT]:
                if event.key == pygame.K_BACKSPACE:
                    buffer = buffer[:-1]
                    play_backspace_click()

                elif event.key == pygame.K_RETURN:
                    buffer += "\n"
                    play_enter_click()

                elif event.key == pygame.K_TAB:
                    reset_to_menu()
                    play_enter_click()

                elif event.unicode and event.unicode.isprintable():
                    buffer += event.unicode
                    play_key_click()

    screen.blit(frame, (0, 0))

    overlay = pygame.Surface((TERMINAL_RECT.width, TERMINAL_RECT.height), pygame.SRCALPHA)
    overlay.fill((0, 25, 22, 28))
    screen.blit(overlay, TERMINAL_RECT.topleft)

    text_x = TERMINAL_RECT.x + PADDING_X
    text_y = TERMINAL_RECT.y + PADDING_Y
    max_text_width = TERMINAL_RECT.width - (PADDING_X * 2)

    full_text = get_screen_text()
    lines = wrap_text(full_text, font, max_text_width)

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

    if cursor_visible and state not in [STATE_BOOTING, STATE_LOADING_CONSTRAINT, STATE_LOADING_REFINEMENT]:
        pygame.draw.rect(screen, CURSOR_COLOR, (cursor_x, cursor_y, 14, 28))

    pygame.display.flip()

pygame.quit()
