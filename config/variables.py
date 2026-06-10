import os
from dotenv import load_dotenv


load_dotenv()

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))


# -----------------------------------------------------------------------
def get_env_var(key: str, default=None) -> str:
    """Read an environment variable and return its value.

    If the variable is not set and no default is provided, raises RuntimeError so missing required config is caught at startup.
    """
    env_var = os.getenv(key, default)
    if env_var is None:
        raise RuntimeError(f"Environment variable '{key}' was not found.")
    return env_var


# -----------------------------------------------------------------------
def load_environment() -> str:
    """Resolve the environment-specific .env file path based on the ENVIRONMENT variable.

    Reads ENVIRONMENT (e.g. 'local'), maps it to the matching file in env_config/,
    and returns the full path so it can be loaded by python-dotenv.
    Raises ValueError for unknown environments and FileNotFoundError if the file is missing.
    """
    env_config_dir = os.path.join(ROOT_DIR, "..", "env_config")

    environment = get_env_var("ENVIRONMENT")
    print(f"[config] Environment: {environment}")

    env_files = {
        "local": ".env.local",
    }

    env_file = env_files.get(environment)
    if not env_file:
        raise ValueError(f"Invalid environment: '{environment}'. Must be one of: {list(env_files)}")

    env_path = os.path.join(env_config_dir, env_file)

    if not os.path.exists(env_path):
        raise FileNotFoundError(f"Environment file not found: {env_path}")

    print(f"[config] Environment file loaded: {env_path}")
    return env_path


load_dotenv(load_environment(), override=False)

# ===============================================================================================
# CONSTANTS
# ===============================================================================================

# OpenAI
OPENAI_API_KEY: str = get_env_var("OPENAI_API_KEY")
OPENAI_MODEL: str = get_env_var("OPENAI_MODEL", "gpt-4o-mini")

# File upload
MAX_FILE_SIZE_MB: int = int(get_env_var("MAX_FILE_SIZE_MB", "10"))

# Logging
LOG_LEVEL: str = get_env_var("LOG_LEVEL", "INFO")

# Service URLs
API_BASE_URL: str = get_env_var("API_BASE_URL", "http://localhost:8000")

# MongoDB
MONGODB_URL: str = get_env_var("MONGODB_URL")
DATABASE_NAME: str = get_env_var("DATABASE_NAME", "resume_parser")
