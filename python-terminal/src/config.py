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


def save_api_key(provider, api_key):
    config = load_env_file()

    provider = provider.lower()

    if provider == "openai":
        config["OPENAI_API_KEY"] = api_key.strip()
    elif provider == "anthropic":
        config["ANTHROPIC_API_KEY"] = api_key.strip()
    else:
        raise ValueError(f"Unknown provider: {provider}")

    lines = [
        f"OPENAI_API_KEY={config.get('OPENAI_API_KEY', '')}",
        f"ANTHROPIC_API_KEY={config.get('ANTHROPIC_API_KEY', '')}",
    ]

    ENV_PATH.write_text("\n".join(lines) + "\n")


def configured_providers():
    providers = []

    if provider_configured("openai"):
        providers.append("OpenAI")

    if provider_configured("anthropic"):
        providers.append("Anthropic")

    return providers
