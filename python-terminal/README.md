# Spectacular Terminal

Spectacular Terminal is a local AI red-teaming and prompt refinement interface built with Python and Pygame.

It is designed as a cinematic terminal-style tool for testing how language models respond under constraints, adversarial prompts, and unstable prompt framing.

## Current Features

- Retro-futuristic terminal interface
- Mechanical keyboard sound effects
- Constraint Conflict Test mode
- Prompt Refinement mode
- API Key Settings screen
- Local `.env` support for user-provided API keys

## Modes

### Constraint Conflict Test

Tests how AI models respond when forced to answer under strict constraints, such as:

- Yes/no only
- Five words maximum
- No explanation allowed
- Custom constraint

The goal is to detect constraint evasion, contradiction, and weak model behavior under pressure.

### Prompt Refinement

Analyzes prompts for weak framing and patterns that can produce unstable outputs.

Possible flags include:

- Reassurance seeking
- False certainty pressure
- Mind reading
- Catastrophizing
- Low-evidence social inference
- Anxiety-amplifying framing

## How to Run

From the project folder:

```bash
cd /Users/admin/SpectacularTerminalFresh/python-terminal
python3 src/main.py
```

## Requirements

- Python 3
- Pygame

Install Pygame with:

```bash
python3 -m pip install pygame
```

## Status

This project is currently in active development.

The current version focuses on the local terminal interface, interaction flow, visual polish, and preparation for model API integration.

## Goal

Spectacular Terminal aims to become a downloadable local tool for testing, refining, and pressure-checking LLM prompts before they reach production or public use.
