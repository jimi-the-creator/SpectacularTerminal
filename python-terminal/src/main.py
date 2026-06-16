import pygame
from pathlib import Path

pygame.init()

BASE_DIR = Path(__file__).resolve().parent.parent
FRAME_PATH = BASE_DIR / "assets" / "frame.png"

frame = pygame.image.load(FRAME_PATH)

WIDTH, HEIGHT = frame.get_size()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
frame = frame.convert()

pygame.display.set_caption("Spectacular Terminal")

clock = pygame.time.Clock()

# Keep your calibrated active terminal area here.
TERMINAL_RECT = pygame.Rect(165, 95, 1340, 690)

# Inner padding so text does not hug the frame
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

    # Soft glow pass
    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        glow = font.render(text, True, GLOW_COLOR)
        glow.set_alpha(80)
        surface.blit(glow, (x + dx, y + dy))

    # Sharp text pass
    rendered = font.render(text, True, TEXT_COLOR)
    surface.blit(rendered, (x, y))


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

            elif event.key == pygame.K_RETURN:
                buffer += "\n"

            elif event.unicode:
                buffer += event.unicode

    screen.blit(frame, (0, 0))

    # Slight screen tint so text feels embedded, not pasted on
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

    # Cursor position after final visible line
    current_line = visible_lines[-1] if visible_lines else ""
    cursor_x = text_x + font.size(current_line)[0] + 4
    cursor_y = y - line_height + 4

    if cursor_visible:
        pygame.draw.rect(screen, CURSOR_COLOR, (cursor_x, cursor_y, 14, 28))

    pygame.display.flip()

pygame.quit()