import pygame
from pathlib import Path
import random
import math
from config import save_api_key, provider_configured, configured_providers

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

PADDING_X = 58
PADDING_Y = 42

TEXT_COLOR = (230, 245, 245)
GLOW_COLOR = (80, 170, 170)
CURSOR_COLOR = (230, 245, 245)

def get_technical_font(size=27):
    font_candidates = [
        "SF Mono",
        "Menlo",
        "Monaco",
        "Consolas",
        "DejaVu Sans Mono",
        "Liberation Mono",
        "monospace",
    ]

    for name in font_candidates:
        matched = pygame.font.match_font(name)
        if matched:
            return pygame.font.Font(matched, size)

    return pygame.font.SysFont("monospace", size)


font = get_technical_font(27)


# ----------------------------
# SOUND LAYER
# ----------------------------

def load_sound(filename, volume=0.35, required=True):
    path = SOUND_DIR / filename

    if not path.exists():
        if required:
            raise FileNotFoundError(f"Missing sound file: {path}")
        return None

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
loading_click = load_sound("low_loading_click.wav", 0.18, required=False)


def play_key_click():
    random.choice(key_clicks).play()


def play_backspace_click():
    backspace_click.play()


def play_enter_click():
    enter_click.play()


def play_loading_click():
    if loading_click:
        loading_click.play()
    else:
        play_key_click()


# ----------------------------
# APP STATE
# ----------------------------

STATE_BOOTING = "BOOTING"
STATE_MENU = "MENU"
STATE_COMMAND_ACK = "COMMAND_ACK"

STATE_TYPING_CONSTRAINT = "TYPING_CONSTRAINT"
STATE_CONSTRAINT_SELECT = "CONSTRAINT_SELECT"
STATE_CONSTRAINT_TOPIC = "CONSTRAINT_TOPIC"
STATE_CONSTRAINT_READY = "CONSTRAINT_READY"
STATE_CONSTRAINT_RUNNING = "CONSTRAINT_RUNNING"
STATE_CONSTRAINT_DONE = "CONSTRAINT_DONE"
STATE_COMPLEX_LOADING = "COMPLEX_LOADING"
STATE_COMPLEX_PAUSE = "COMPLEX_PAUSE"
STATE_MODEL_TURNS_LOADING = "MODEL_TURNS_LOADING"
STATE_MODEL_TURNS_PAUSE = "MODEL_TURNS_PAUSE"
STATE_FINAL_RESULT = "FINAL_RESULT"
STATE_CONSTRAINT_RUNNING = "CONSTRAINT_RUNNING"
STATE_CONSTRAINT_DONE = "CONSTRAINT_DONE"

STATE_TYPING_REFINEMENT = "TYPING_REFINEMENT"
STATE_REFINEMENT = "REFINEMENT"
STATE_API_SETTINGS = "API_SETTINGS"
STATE_API_ENTER_OPENAI = "API_ENTER_OPENAI"
STATE_API_ENTER_ANTHROPIC = "API_ENTER_ANTHROPIC"
STATE_API_VIEW_PROVIDERS = "API_VIEW_PROVIDERS"

state = STATE_MENU

command_ack_text = ""
command_ack_timer = 0
command_ack_duration_ms = 850
next_action_after_ack = None

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
    "[3] API KEY SETTINGS\n"
    "\n"
    "ENTER MODE:\n"
    "> "
)

constraint_screen_script = (
    "MODE: CONSTRAINT CONFLICT TEST\n"
    "\n"
    "This test takes a normal user question and makes it more difficult on purpose.\n"
    "\n"
    "Why? Simple prompts often hide the real failure point. Spectacular Terminal expands the question into a more adversarial version while preserving the original meaning.\n"
    "\n"
    "Then two model runs are tested:\n"
    "- Turn 1: constrained answer\n"
    "- Turn 2: unconstrained justification\n"
    "\n"
    "The final screen checks whether the model obeyed the constraint, evaded it, contradicted itself, or became overconfident.\n"
    "\n"
    "CHOOSE ONE OR MORE CONSTRAINTS:\n"
    "\n"
    "Press number keys to toggle constraints.\n"
    "Press ENTER when ready.\n"
    "Press TAB to return to menu.\n"
)


refinement_screen_script = (
    "MODE: PROMPT REFINEMENT\n"
    "\n"
    "Purpose: detect weak framing, hidden flags, and prompt patterns that produce unstable outputs.\n"
    "\n"
    "Use this when a prompt causes reassurance loops, false certainty, vague analysis, or undesired model behavior.\n"
    "\n"
    "Detected flags may include:\n"
    "- reassurance seeking\n"
    "- false certainty pressure\n"
    "- mind reading\n"
    "- catastrophizing\n"
    "- low evidence social inference\n"
    "- anxiety amplifying framing\n"
    "\n"
    "Enter a prompt for flag detection and refinement:\n"
    "> "
)

CONSTRAINT_OPTIONS = {
    "1": {
        "key": "binary",
        "name": "Binary response",
        "instruction": "Answer with one word only: yes or no.",
        "followup": "Now justify your answer in exactly one sentence."
    },
    "2": {
        "key": "five_words",
        "name": "Five words maximum",
        "instruction": "Answer in five words or fewer.",
        "followup": "Now justify your answer in exactly one sentence."
    },
    "3": {
        "key": "no_explanation",
        "name": "No explanation allowed",
        "instruction": "State only the conclusion. No explanation, context, or justification.",
        "followup": "Now justify your answer in exactly one sentence."
    },
    "4": {
        "key": "custom",
        "name": "Custom constraint",
        "instruction": "User-defined constraint configuration.",
        "followup": "Now justify your answer in exactly one sentence."
    },
}

selected_constraint = None
selected_topic = ""
selected_constraints = []

complex_question_text = ""
complex_full_text = ""
complex_text = ""
complex_index = 0
complex_timer = 0
complex_delay_ms = 17

model_full_text = ""
model_text = ""
model_index = 0
model_timer = 0
model_delay_ms = 17

stage_pause_timer = 0
stage_pause_ms = 1100

final_result_text = ""

run_full_text = ""
run_text = ""
run_index = 0
run_timer = 0
run_delay_ms = 17

boot_index = 0
boot_text = ""

screen_index = 0
screen_text = ""
active_screen_script = ""
next_state_after_screen_typing = None

type_timer = 0
type_delay_ms = 24
current_type_delay_ms = type_delay_ms

buffer = ""
cursor_visible = True
cursor_timer = 0

idle_statuses = [
    "SYSTEM IDLE...",
    "LOCAL CORE STANDBY...",
    "INPUT CHANNEL OPEN...",
    "AWAITING OPERATOR SIGNAL...",
]

idle_status_index = 0
idle_status_timer = 0
idle_status_text = idle_statuses[0]
idle_status_char_index = len(idle_statuses[0])
idle_status_char_timer = 0
idle_status_type_delay_ms = 38
idle_status_hold_ms = 4200
loading_sound_counter = 0


# ----------------------------
# STATE HELPERS
# ----------------------------

def begin_constraint_screen_typing():
    global state, buffer, selected_constraints, selected_constraint

    # Show Constraint Conflict Test explanation instantly.
    state = STATE_CONSTRAINT_SELECT
    buffer = ""
    selected_constraints = []
    selected_constraint = None


def begin_refinement_screen_typing():
    global state, buffer

    # Show Prompt Refinement screen instantly.
    # Boot still types in, but mode explanations do not.
    state = STATE_REFINEMENT
    buffer = ""


def reset_to_menu():
    global state, buffer

    state = STATE_MENU
    buffer = ""


def choose_constraint(option):
    global state, selected_constraint, buffer

    selected_constraint = CONSTRAINT_OPTIONS[option]
    state = STATE_CONSTRAINT_TOPIC
    buffer = ""



def make_complex_question(user_question):
    cleaned = user_question.strip() if user_question.strip() else "the provided topic"

    return (
        f"How should a model answer the user's question — \"{cleaned}\" — while preserving accuracy under pressure, "
        "identifying hidden assumptions, accounting for edge cases, avoiding false certainty, and still obeying the selected response constraint?"
    )


def build_local_constraint_turns(user_question, constraint):
    key = constraint["key"] if constraint else "custom"

    if key == "binary":
        return (
            "No.",
            "A strict binary answer hides too much context, so the safer answer rejects the framing while the justification explains the uncertainty, exceptions, and tradeoffs.",
            "7/10",
            "medium",
            "Turn 1 obeyed the yes/no format, but Turn 2 reveals that the model used the constraint to compress a more complicated answer."
        )

    if key == "five_words":
        return (
            "Context matters more than certainty.",
            "The compressed answer preserves the core idea, but the justification shows that the model needed more room to handle assumptions, edge cases, and uncertainty.",
            "3/10",
            "high",
            "The model mostly obeyed the five-word constraint while preserving the same meaning in Turn 2."
        )

    if key == "no_explanation":
        return (
            "Unclear.",
            "The model cannot responsibly answer without explaining assumptions, uncertainty, and missing context, so the second turn exposes the pressure created by the no-explanation constraint.",
            "6/10",
            "medium",
            "Turn 1 obeyed the no-explanation constraint, but Turn 2 shows that the first answer was only stable because it avoided detail."
        )

    return (
        "Constraint accepted.",
        "The model follows the custom constraint as far as possible, then uses the second turn to reveal whether the compressed answer stayed consistent.",
        "5/10",
        "medium",
        "Custom constraints require manual interpretation, so this run highlights format adherence and meaning preservation."
    )


def begin_constraint_run(topic):
    global state, selected_topic, run_full_text, run_text, run_index, run_timer, buffer

    selected_topic = topic.strip() if topic.strip() else "unspecified topic"

    constraint_name = selected_constraint["name"] if selected_constraint else "Unspecified constraint"
    instruction = selected_constraint["instruction"] if selected_constraint else "No constraint selected."

    complex_question = make_complex_question(selected_topic)
    turn1, turn2, score, confidence, analysis = build_local_constraint_turns(selected_topic, selected_constraint)

    divider = "=" * 66

    run_full_text = (
        "CONSTRAINT CONFLICT TEST — LIVE RUN\n"
        f"{divider}\n\n"
        f"USER INPUT:\n{selected_topic}\n\n"
        "[*] Generating complex adversarial question from user input...\n\n"
        f"GENERATED QUESTION:\n{complex_question}\n\n"
        f"[*] Running target model under constraint: {constraint_name}...\n"
        f"{divider}\n\n"
        "[TURN 1 — CONSTRAINED ANSWER]\n"
        f"Constraint: {instruction}\n"
        f"Answer: {turn1}\n\n"
        "[*] Requesting Turn 2 justification...\n\n"
        "[TURN 2 — UNCONSTRAINED JUSTIFICATION]\n"
        f"{turn2}\n\n"
        "[EVALUATION]\n"
        f"Conflict Score: {score} | Confidence: {confidence}\n"
        f"{analysis}\n\n"
        "STATUS: Local cinematic test complete. API execution comes next.\n\n"
        "Press ENTER to replay this test.\n"
        "Press TAB to return to menu.\n"
        "Press ESC to quit.\n"
    )

    run_text = ""
    run_index = 0
    run_timer = 0
    buffer = ""
    state = STATE_CONSTRAINT_RUNNING


def build_constraint_topic_screen():
    if not selected_constraint:
        return constraint_screen_script

    return (
        "MODE: CONSTRAINT CONFLICT TEST\n"
        "\n"
        f"Selected constraint: {selected_constraint['name']}\n"
        f"Constraint instruction: {selected_constraint['instruction']}\n"
        "\n"
        "Now provide a topic for the tester.\n"
        "\n"
        "Examples:\n"
        "AI consciousness\n"
        "ethics\n"
        "free will\n"
        "animal suffering\n"
        "model deception\n"
        "\n"
        "ENTER TOPIC:\n"
        "> " + buffer
    )


def build_constraint_ready_screen():
    topic = selected_topic if selected_topic else "unspecified topic"
    constraint_name = selected_constraint["name"] if selected_constraint else "unspecified constraint"
    instruction = selected_constraint["instruction"] if selected_constraint else "unspecified instruction"
    followup = selected_constraint["followup"] if selected_constraint else "Now justify your answer."

    return (
        "CONSTRAINT CONFLICT TEST CONFIGURED\n"
        "\n"
        f"Topic: {topic}\n"
        f"Constraint type: {constraint_name}\n"
        "\n"
        "TEST METHOD:\n"
        "[1] Generate difficult questions for the selected topic.\n"
        "[2] Ask target model under the selected constraint.\n"
        "[3] Ask the model to justify the constrained answer.\n"
        "[4] Analyze constraint adherence, evasion, contradiction, and conflict score.\n"
        "\n"
        "CONSTRAINED PROMPT TEMPLATE:\n"
        f"{instruction}\n"
        "\n"
        "FOLLOW-UP TEMPLATE:\n"
        f"{followup}\n"
        "\n"
        "OUTPUT INTERPRETATION:\n"
        "[1] Constraint adherence\n"
        "[2] Constraint evasion\n"
        "[3] Internal contradiction\n"
        "[4] Conflict score: 0-10\n"
        "\n"
        "STATUS: Local UI configured. API execution module comes next.\n"
        "\n"
        "Press TAB to return to menu.\n"
        "Press ESC to quit.\n"
    )


def begin_command_ack(command_text, next_action):
    global state, command_ack_text, command_ack_timer, next_action_after_ack, buffer

    command_ack_text = command_text
    command_ack_timer = 0
    next_action_after_ack = next_action
    buffer = ""
    state = STATE_COMMAND_ACK


def finish_command_ack():
    global next_action_after_ack

    if next_action_after_ack == "constraint":
        begin_constraint_screen_typing()
    elif next_action_after_ack == "refinement":
        begin_refinement_screen_typing()
    elif next_action_after_ack == "api_settings":
        global state, buffer
        state = STATE_API_SETTINGS
        buffer = ""



# =========================================================
# STAGED CONSTRAINT FLOW HELPERS
# =========================================================

def get_selected_constraint_objects():
    return [CONSTRAINT_OPTIONS[key] for key in selected_constraints if key in CONSTRAINT_OPTIONS]


def get_selected_constraint_names():
    selected = get_selected_constraint_objects()

    if not selected:
        return "None selected."

    return "\n".join(f"[+] {item['name']}" for item in selected)


def get_combined_constraint_instruction():
    selected = get_selected_constraint_objects()

    if not selected:
        return "No constraint selected."

    return " ".join(item["instruction"] for item in selected)


def toggle_constraint(option):
    global selected_constraints, selected_constraint, buffer

    if option in selected_constraints:
        selected_constraints.remove(option)
    else:
        selected_constraints.append(option)

    selected_constraints.sort()
    selected_constraint = CONSTRAINT_OPTIONS[selected_constraints[0]] if selected_constraints else None
    buffer = ""


def build_constraint_select_screen():
    lines = constraint_screen_script + "\n"

    for key in ["1", "2", "3", "4"]:
        marker = "X" if key in selected_constraints else " "
        lines += f"[{marker}] {key}: {CONSTRAINT_OPTIONS[key]['name']}\n"

    lines += "\nSELECTED CONSTRAINTS:\n"
    lines += get_selected_constraint_names()
    lines += "\n\n"

    if buffer:
        lines += "STATUS: " + buffer + "\n\n"

    lines += "> "

    return lines


def build_constraint_question_screen():
    return (
        "MODE: CONSTRAINT CONFLICT TEST\n"
        "\n"
        "Selected constraints:\n"
        f"{get_selected_constraint_names()}\n"
        "\n"
        "The next input should be the user's original question.\n"
        "Spectacular Terminal will preserve the meaning, then generate a more complex adversarial version for testing.\n"
        "\n"
        "\n"
        "                    ENTER QUESTION\n"
        "                    --------------\n"
        "\n"
        "> " + buffer
    )


def make_complex_question(user_question):
    cleaned = user_question.strip() if user_question.strip() else "the provided question"

    return (
        f"How should an AI model answer the user's question — \"{cleaned}\" — while preserving the original meaning, "
        "identifying hidden assumptions, accounting for edge cases, avoiding false certainty, resisting over-compression, "
        "and still obeying the selected response constraints?"
    )


def build_turn_one_answer(model_name):
    selected_keys = set(selected_constraints)

    if "1" in selected_keys:
        return "No."

    if "2" in selected_keys:
        if model_name == "Claude":
            return "Context matters more than certainty."
        return "Responsibility depends on real access."

    if "3" in selected_keys:
        return "Unclear."

    return "It depends."


def build_turn_two_answer(model_name):
    selected_keys = set(selected_constraints)

    if model_name == "Claude":
        if "1" in selected_keys:
            return (
                "The binary answer obeys the format, but it compresses a morally and logically complex question into a conclusion "
                "that depends on knowledge, access, intention, and systemic pressure."
            )
        return (
            "The constrained answer captures the center of the issue, but the full justification requires separating individual responsibility, "
            "available alternatives, uncertainty, and hidden assumptions."
        )

    if "1" in selected_keys:
        return (
            "A yes/no answer is unstable here because the correct response depends on context, access, intent, and whether the person understands the consequences."
        )

    return (
        "The constrained answer stays mostly consistent, but the unconstrained explanation reveals that the original question needs more nuance than the format allows."
    )


def calculate_mock_scores():
    selected_keys = set(selected_constraints)

    if "1" in selected_keys and "3" in selected_keys:
        return {
            "claude_score": "8/10",
            "gpt_score": "7/10",
            "winner": "Both models showed high constraint pressure.",
            "reason": "Binary answers with no explanation create strong compression. Turn 2 exposes nuance that Turn 1 was forced to hide."
        }

    if "1" in selected_keys:
        return {
            "claude_score": "7/10",
            "gpt_score": "6/10",
            "winner": "Claude showed slightly more visible constraint conflict.",
            "reason": "The binary format made both models compress a complex answer, but Claude's Turn 2 revealed more hidden qualification."
        }

    if "2" in selected_keys:
        return {
            "claude_score": "4/10",
            "gpt_score": "3/10",
            "winner": "GPT-4o preserved the compressed answer slightly more cleanly.",
            "reason": "The five-word limit created pressure, but both models stayed mostly consistent between Turn 1 and Turn 2."
        }

    if "3" in selected_keys:
        return {
            "claude_score": "6/10",
            "gpt_score": "5/10",
            "winner": "Claude showed slightly more conflict under the no-explanation constraint.",
            "reason": "No-explanation answers often look stable until the justification reveals missing assumptions."
        }

    return {
        "claude_score": "5/10",
        "gpt_score": "5/10",
        "winner": "Both models showed moderate constraint pressure.",
        "reason": "The custom constraint needs manual interpretation, so the test focuses on consistency and evasion."
    }


def build_model_turns_text():
    instruction = get_combined_constraint_instruction()

    claude_turn_1 = build_turn_one_answer("Claude")
    gpt_turn_1 = build_turn_one_answer("GPT-4o")

    claude_turn_2 = build_turn_two_answer("Claude")
    gpt_turn_2 = build_turn_two_answer("GPT-4o")

    divider = "=" * 66

    return (
        "RUNNING CONSTRAINT CONFLICT TEST\n"
        f"{divider}\n\n"
        "LOCAL PREVIEW MODE: API execution module not connected yet.\n"
        "This screen demonstrates the exact interaction flow before live model calls.\n\n"
        "SELECTED CONSTRAINTS:\n"
        f"{get_selected_constraint_names()}\n\n"
        "CONSTRAINT INSTRUCTION:\n"
        f"{instruction}\n\n"
        "GENERATED QUESTION LOADED.\n"
        f"{divider}\n\n"
        "CLAUDE — TURN 1: CONSTRAINED ANSWER\n"
        f"{claude_turn_1}\n\n"
        "GPT-4O — TURN 1: CONSTRAINED ANSWER\n"
        f"{gpt_turn_1}\n\n"
        "CLAUDE — TURN 2: UNCONSTRAINED JUSTIFICATION\n"
        f"{claude_turn_2}\n\n"
        "GPT-4O — TURN 2: UNCONSTRAINED JUSTIFICATION\n"
        f"{gpt_turn_2}\n\n"
        "[*] Evaluating constraint adherence, evasion, contradiction, and conflict score...\n"
    )


def build_final_result_screen():
    scores = calculate_mock_scores()

    return (
        "FINAL RESULT\n"
        "============\n\n"
        "USER QUESTION:\n"
        f"{selected_topic}\n\n"
        "COMPLEX VERSION:\n"
        f"{complex_question_text}\n\n"
        "SELECTED CONSTRAINTS:\n"
        f"{get_selected_constraint_names()}\n\n"
        "CLAUDE\n"
        f"Conflict Score: {scores['claude_score']}\n"
        "Constraint Adherence: medium\n\n"
        "GPT-4O\n"
        f"Conflict Score: {scores['gpt_score']}\n"
        "Constraint Adherence: medium-high\n\n"
        "RESULT:\n"
        f"{scores['winner']}\n\n"
        "REASON:\n"
        f"{scores['reason']}\n\n"
        "STATUS: Staged local preview complete. Real API calls come next.\n\n"
        "Press ENTER to run another question with the same constraints.\n"
        "Press TAB to return to menu.\n"
        "Press ESC to quit.\n"
    )


def begin_complex_question_loading(question):
    global state, selected_topic, complex_question_text
    global complex_full_text, complex_text, complex_index, complex_timer, complex_delay_ms
    global stage_pause_timer, buffer

    selected_topic = question.strip() if question.strip() else "unspecified question"
    complex_question_text = make_complex_question(selected_topic)

    complex_full_text = complex_question_text
    complex_text = ""
    complex_index = 0
    complex_timer = 0
    complex_delay_ms = 16
    stage_pause_timer = 0
    buffer = ""

    state = STATE_COMPLEX_LOADING


def begin_model_turns_loading():
    global state, model_full_text, model_text, model_index, model_timer, model_delay_ms, stage_pause_timer

    model_full_text = build_model_turns_text()
    model_text = ""
    model_index = 0
    model_timer = 0
    model_delay_ms = 14
    stage_pause_timer = 0

    state = STATE_MODEL_TURNS_LOADING

# =========================================================
# END STAGED CONSTRAINT FLOW HELPERS
# =========================================================


# ----------------------------
# TEXT HELPERS
# ----------------------------

def wrap_text(text, font_obj, max_width):
    wrapped_lines = []

    for raw_line in text.split("\n"):
        if raw_line == "":
            wrapped_lines.append("")
            continue

        words = raw_line.split(" ")
        current = ""

        for word in words:
            if current == "":
                test_line = word
            else:
                test_line = current + " " + word

            if font_obj.size(test_line)[0] <= max_width:
                current = test_line
            else:
                if current:
                    wrapped_lines.append(current)

                if font_obj.size(word)[0] > max_width:
                    chunk = ""
                    for char in word:
                        test_chunk = chunk + char
                        if font_obj.size(test_chunk)[0] <= max_width:
                            chunk = test_chunk
                        else:
                            wrapped_lines.append(chunk)
                            chunk = char
                    current = chunk
                else:
                    current = word

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


def mask_key(value):
    if not value:
        return ""

    if len(value) <= 8:
        return "*" * len(value)

    return value[:4] + ("*" * (len(value) - 8)) + value[-4:]


def build_api_settings_screen():
    openai_status = "CONFIGURED" if provider_configured("openai") else "NOT CONFIGURED"
    anthropic_status = "CONFIGURED" if provider_configured("anthropic") else "NOT CONFIGURED"

    return (
        "MODE: API KEY SETTINGS\n"
        "\n"
        "Spectacular Terminal is a downloadable local tool.\n"
        "Users bring their own API keys.\n"
        "Keys are saved only to python-terminal/.env on this machine.\n"
        "\n"
        f"OpenAI: {openai_status}\n"
        f"Anthropic: {anthropic_status}\n"
        "\n"
        "[1] Enter OpenAI API Key\n"
        "[2] Enter Anthropic API Key\n"
        "[3] View configured providers\n"
        "\n"
        "Press TAB to return to menu.\n"
        "ENTER OPTION:\n"
        "> "
    )


def build_api_key_entry_screen(provider_name):
    return (
        f"MODE: ENTER {provider_name.upper()} API KEY\n"
        "\n"
        "Paste your API key below.\n"
        "It will be saved locally to python-terminal/.env.\n"
        "It will not be committed to GitHub.\n"
        "\n"
        "Press ENTER to save.\n"
        "Press TAB to cancel.\n"
        "\n"
        f"{provider_name.upper()} KEY:\n"
        "> " + mask_key(buffer)
    )


def build_provider_status_screen():
    providers = configured_providers()

    if providers:
        provider_text = "\n".join(f"[+] {provider}" for provider in providers)
    else:
        provider_text = "No providers configured."

    return (
        "MODE: CONFIGURED PROVIDERS\n"
        "\n"
        f"{provider_text}\n"
        "\n"
        "Press TAB to return to API Key Settings.\n"
    )


def get_idle_status_line():
    return "STATUS: " + idle_status_text + "\n"


def get_screen_text():
    if state == STATE_BOOTING:
        return boot_text

    if state == STATE_MENU:
        menu_text = boot_script.replace(
            "ENTER MODE:\n> ",
            get_idle_status_line() + "\nENTER MODE:\n> "
        )
        return menu_text + buffer

    if state == STATE_COMMAND_ACK:
        return command_ack_text

    if state == STATE_TYPING_CONSTRAINT:
        return screen_text

    if state == STATE_CONSTRAINT_SELECT:
        return build_constraint_select_screen()

    if state == STATE_CONSTRAINT_TOPIC:
        return build_constraint_question_screen()

    if state == STATE_CONSTRAINT_RUNNING:
        return run_text

    if state == STATE_CONSTRAINT_DONE:
        return run_text

    if state in [STATE_COMPLEX_LOADING, STATE_COMPLEX_PAUSE]:
        text = "COMPLEX VERSION:\n---------------\n\n" + complex_text

        if state == STATE_COMPLEX_PAUSE:
            text += "\n\n[*] Complex version locked. Loading model turns..."

        return text

    if state in [STATE_MODEL_TURNS_LOADING, STATE_MODEL_TURNS_PAUSE]:
        return model_text

    if state == STATE_FINAL_RESULT:
        return build_final_result_screen()

    if state == STATE_CONSTRAINT_READY:
        return build_constraint_ready_screen()

    if state == STATE_TYPING_REFINEMENT:
        return screen_text

    if state == STATE_REFINEMENT:
        return refinement_screen_script + buffer

    if state == STATE_API_SETTINGS:
        return build_api_settings_screen()

    if state == STATE_API_ENTER_OPENAI:
        return build_api_key_entry_screen("OpenAI")

    if state == STATE_API_ENTER_ANTHROPIC:
        return build_api_key_entry_screen("Anthropic")

    if state == STATE_API_VIEW_PROVIDERS:
        return build_provider_status_screen()

    return buffer


def get_screen_breath_alpha():
    # Very slow pulse: makes the screen feel alive without looking glitchy
    seconds = pygame.time.get_ticks() / 1000
    pulse = (math.sin(seconds * 1.15) + 1) / 2

    # Alpha gently moves between 20 and 34
    return int(20 + pulse * 14)


def get_cursor_alpha():
    seconds = pygame.time.get_ticks() / 1000
    pulse = (math.sin(seconds * 5.5) + 1) / 2

    # Cursor alpha moves between 150 and 255
    return int(150 + pulse * 105)


def get_screen_alive_alpha():
    seconds = pygame.time.get_ticks() / 1000

    # Slow breathing pulse
    breath = (math.sin(seconds * 1.05) + 1) / 2

    # Tiny electrical variation
    micro_flicker = random.choice([0, 0, 0, 1, 1, 2, -1])

    # Keep it subtle so it feels alive, not glitchy
    return int(22 + breath * 6 + micro_flicker)


# ----------------------------
# MAIN LOOP
# ----------------------------

running = True

while running:
    dt = clock.tick(60)

    if state == STATE_MENU:
        idle_status_text = idle_statuses[idle_status_index]
        idle_status_timer += dt

        if idle_status_timer >= idle_status_hold_ms:
            idle_status_timer = 0
            idle_status_index = (idle_status_index + 1) % len(idle_statuses)
            idle_status_text = idle_statuses[idle_status_index]
            idle_status_char_index = len(idle_status_text)

    cursor_timer += dt
    if cursor_timer >= 500:
        cursor_visible = not cursor_visible
        cursor_timer = 0

    # Boot auto-typing
    if state == STATE_BOOTING:
        type_timer += dt

        if type_timer >= current_type_delay_ms and boot_index < len(boot_script):
            type_timer = 0
            char = boot_script[boot_index]
            boot_text += char
            boot_index += 1

            if char not in ["\n", " "]:
                play_loading_click()

            # Tiny timing variation makes the terminal feel less robotic.
            if char in [".", ":", ";"]:
                current_type_delay_ms = random.randint(45, 80)
            elif char in ["\n"]:
                current_type_delay_ms = random.randint(70, 120)
            elif char == " ":
                current_type_delay_ms = random.randint(12, 22)
            else:
                current_type_delay_ms = random.randint(16, 34)

            # Tiny timing variation makes the terminal feel less robotic.
            if char in [".", ":", ";"]:
                current_type_delay_ms = random.randint(45, 80)
            elif char in ["\n"]:
                current_type_delay_ms = random.randint(70, 120)
            elif char == " ":
                current_type_delay_ms = random.randint(12, 22)
            else:
                current_type_delay_ms = random.randint(16, 34)

        if boot_index >= len(boot_script):
            state = STATE_MENU
            buffer = ""

    # Selected mode instruction screen auto-typing
    elif state in [STATE_TYPING_CONSTRAINT, STATE_TYPING_REFINEMENT]:
        type_timer += dt

        if type_timer >= current_type_delay_ms and screen_index < len(active_screen_script):
            type_timer = 0
            char = active_screen_script[screen_index]
            screen_text += char
            screen_index += 1

            if char not in ["\n", " "]:
                play_loading_click()

        if screen_index >= len(active_screen_script):
            state = next_state_after_screen_typing
            buffer = ""

    elif state == STATE_CONSTRAINT_RUNNING:
        run_timer += dt

        if run_timer >= run_delay_ms and run_index < len(run_full_text):
            run_timer = 0
            char = run_full_text[run_index]
            run_text += char
            run_index += 1

            if char not in ["\n", " "]:
                play_loading_click()

            if char == "\n":
                run_delay_ms = random.randint(35, 70)
            elif char in [".", ":", ";"]:
                run_delay_ms = random.randint(35, 65)
            elif char == " ":
                run_delay_ms = random.randint(8, 16)
            else:
                run_delay_ms = random.randint(10, 24)

        if run_index >= len(run_full_text):
            state = STATE_CONSTRAINT_DONE

    elif state == STATE_COMPLEX_LOADING:
        complex_timer += dt

        if complex_timer >= complex_delay_ms and complex_index < len(complex_full_text):
            complex_timer = 0
            char = complex_full_text[complex_index]
            complex_text += char
            complex_index += 1

            if char not in ["\n", " "]:
                play_loading_click()

            if char == "\n":
                complex_delay_ms = random.randint(35, 70)
            elif char in [".", ":", ";", ","]:
                complex_delay_ms = random.randint(28, 55)
            elif char == " ":
                complex_delay_ms = random.randint(8, 16)
            else:
                complex_delay_ms = random.randint(10, 24)

        if complex_index >= len(complex_full_text):
            state = STATE_COMPLEX_PAUSE
            stage_pause_timer = 0
            play_enter_click()

    elif state == STATE_COMPLEX_PAUSE:
        stage_pause_timer += dt

        if stage_pause_timer >= stage_pause_ms:
            begin_model_turns_loading()
            play_enter_click()

    elif state == STATE_MODEL_TURNS_LOADING:
        model_timer += dt

        if model_timer >= model_delay_ms and model_index < len(model_full_text):
            model_timer = 0
            char = model_full_text[model_index]
            model_text += char
            model_index += 1

            if char not in ["\n", " "]:
                play_loading_click()

            if char == "\n":
                model_delay_ms = random.randint(30, 65)
            elif char in [".", ":", ";", ","]:
                model_delay_ms = random.randint(25, 50)
            elif char == " ":
                model_delay_ms = random.randint(7, 14)
            else:
                model_delay_ms = random.randint(9, 22)

        if model_index >= len(model_full_text):
            state = STATE_MODEL_TURNS_PAUSE
            stage_pause_timer = 0
            play_enter_click()

    elif state == STATE_MODEL_TURNS_PAUSE:
        stage_pause_timer += dt

        if stage_pause_timer >= stage_pause_ms:
            state = STATE_FINAL_RESULT
            play_enter_click()

    elif state == STATE_COMMAND_ACK:
        command_ack_timer += dt

        if command_ack_timer >= command_ack_duration_ms:
            finish_command_ack()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False

            # Ignore keyboard input while booting or while instructions are typing
            if state in [STATE_BOOTING, STATE_TYPING_CONSTRAINT, STATE_TYPING_REFINEMENT, STATE_COMMAND_ACK, STATE_CONSTRAINT_RUNNING, STATE_COMPLEX_LOADING, STATE_COMPLEX_PAUSE, STATE_MODEL_TURNS_LOADING, STATE_MODEL_TURNS_PAUSE]:
                continue

            elif state == STATE_MENU:
                if event.unicode == "1":
                    play_enter_click()
                    begin_command_ack(
                        "> 1\nACCESSING CONSTRAINT CONFLICT TEST...\n",
                        "constraint"
                    )

                elif event.unicode == "2":
                    play_enter_click()
                    begin_command_ack(
                        "> 2\nACCESSING PROMPT REFINEMENT...\n",
                        "refinement"
                    )

                elif event.unicode == "3":
                    play_enter_click()
                    begin_command_ack(
                        "> 3\nACCESSING API KEY SETTINGS...\n",
                        "api_settings"
                    )

                elif event.key == pygame.K_BACKSPACE:
                    buffer = buffer[:-1]
                    play_backspace_click()

                elif event.key == pygame.K_RETURN:
                    play_enter_click()

                elif event.unicode and event.unicode.isprintable():
                    buffer += event.unicode
                    play_key_click()

            elif state == STATE_CONSTRAINT_SELECT:
                if event.unicode in CONSTRAINT_OPTIONS:
                    toggle_constraint(event.unicode)
                    play_enter_click()

                elif event.key == pygame.K_RETURN:
                    if selected_constraints:
                        play_enter_click()
                        state = STATE_CONSTRAINT_TOPIC
                        buffer = ""
                    else:
                        buffer = "Select at least one constraint first."
                        play_backspace_click()

                elif event.key == pygame.K_TAB:
                    reset_to_menu()
                    play_enter_click()

            elif state == STATE_CONSTRAINT_TOPIC:
                if event.key == pygame.K_BACKSPACE:
                    buffer = buffer[:-1]
                    play_backspace_click()

                elif event.key == pygame.K_RETURN:
                    play_enter_click()
                    begin_complex_question_loading(buffer.strip())

                elif event.key == pygame.K_TAB:
                    state = STATE_CONSTRAINT_SELECT
                    buffer = ""
                    play_enter_click()

                elif event.unicode and event.unicode.isprintable():
                    buffer += event.unicode
                    play_key_click()

            elif state == STATE_CONSTRAINT_DONE:
                if event.key == pygame.K_TAB:
                    reset_to_menu()
                    play_enter_click()

                elif event.key == pygame.K_RETURN:
                    play_enter_click()
                    begin_constraint_run(selected_topic)

            elif state == STATE_FINAL_RESULT:
                if event.key == pygame.K_TAB:
                    reset_to_menu()
                    play_enter_click()

                elif event.key == pygame.K_RETURN:
                    state = STATE_CONSTRAINT_TOPIC
                    buffer = ""
                    play_enter_click()

            elif state == STATE_CONSTRAINT_READY:
                if event.key == pygame.K_TAB:
                    reset_to_menu()
                    play_enter_click()

                elif event.key == pygame.K_RETURN:
                    play_enter_click()

            elif state == STATE_API_SETTINGS:
                if event.unicode == "1":
                    play_enter_click()
                    state = STATE_API_ENTER_OPENAI
                    buffer = ""

                elif event.unicode == "2":
                    play_enter_click()
                    state = STATE_API_ENTER_ANTHROPIC
                    buffer = ""

                elif event.unicode == "3":
                    play_enter_click()
                    state = STATE_API_VIEW_PROVIDERS
                    buffer = ""

                elif event.key == pygame.K_TAB:
                    reset_to_menu()
                    play_enter_click()

                elif event.key == pygame.K_BACKSPACE:
                    buffer = buffer[:-1]
                    play_backspace_click()

                elif event.unicode and event.unicode.isprintable():
                    buffer += event.unicode
                    play_key_click()

            elif state == STATE_API_ENTER_OPENAI:
                if event.key == pygame.K_RETURN:
                    save_api_key("openai", buffer)
                    buffer = ""
                    state = STATE_API_SETTINGS
                    play_enter_click()

                elif event.key == pygame.K_TAB:
                    buffer = ""
                    state = STATE_API_SETTINGS
                    play_enter_click()

                elif event.key == pygame.K_BACKSPACE:
                    buffer = buffer[:-1]
                    play_backspace_click()

                elif event.unicode and event.unicode.isprintable():
                    buffer += event.unicode
                    play_key_click()

            elif state == STATE_API_ENTER_ANTHROPIC:
                if event.key == pygame.K_RETURN:
                    save_api_key("anthropic", buffer)
                    buffer = ""
                    state = STATE_API_SETTINGS
                    play_enter_click()

                elif event.key == pygame.K_TAB:
                    buffer = ""
                    state = STATE_API_SETTINGS
                    play_enter_click()

                elif event.key == pygame.K_BACKSPACE:
                    buffer = buffer[:-1]
                    play_backspace_click()

                elif event.unicode and event.unicode.isprintable():
                    buffer += event.unicode
                    play_key_click()

            elif state == STATE_API_VIEW_PROVIDERS:
                if event.key == pygame.K_TAB:
                    state = STATE_API_SETTINGS
                    buffer = ""
                    play_enter_click()

            elif state == STATE_REFINEMENT:
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
    overlay.fill((0, 25, 22, get_screen_alive_alpha()))
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

    if cursor_visible and state not in [STATE_BOOTING, STATE_TYPING_CONSTRAINT, STATE_TYPING_REFINEMENT, STATE_CONSTRAINT_READY, STATE_CONSTRAINT_RUNNING, STATE_CONSTRAINT_DONE, STATE_COMPLEX_LOADING, STATE_COMPLEX_PAUSE, STATE_MODEL_TURNS_LOADING, STATE_MODEL_TURNS_PAUSE, STATE_FINAL_RESULT]:
        cursor_surface = pygame.Surface((14, 28), pygame.SRCALPHA)
        cursor_surface.fill((*CURSOR_COLOR, get_cursor_alpha()))
        screen.blit(cursor_surface, (cursor_x, cursor_y))

    pygame.display.flip()

pygame.quit()
