from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"


def load_env_file():
    config = {}

    if not ENV_PATH.exists():
        return config

    for line in ENV_PATH.read_text().splitlines():
        line = line.strip()

        if not line or line.startswith("#"):
            continue

        if "=" in line:
            key, value = line.split("=", 1)
            config[key.strip()] = value.strip()

    return config


def get_api_key(provider):
    config = load_env_file()

    if provider.lower() == "openai":
        return config.get("OPENAI_API_KEY", "")

    if provider.lower() == "anthropic":
        return config.get("ANTHROPIC_API_KEY", "")

    return ""


def provider_configured(provider):
    return bool(get_api_key(provider))
