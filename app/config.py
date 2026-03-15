import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent



def load_env_file(path: Path) -> None:
    if not path.exists():
        return

    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


load_env_file(BASE_DIR / ".env")


class Settings:
    APP_HOST: str = os.getenv("APP_HOST", "127.0.0.1")
    APP_PORT: int = int(os.getenv("APP_PORT", "8000"))

    DATABASE_PATH: str = os.getenv("DATABASE_PATH", str(BASE_DIR / "data" / "app.db"))
    EXPORT_DIR: str = os.getenv("EXPORT_DIR", str(BASE_DIR / "exports"))
    TELEGRAM_THREAD_ID: str = os.getenv("TELEGRAM_THREAD_ID", "")

    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "")
    API_SECRET: str = os.getenv("API_SECRET", "change_me")

    ADMIN_USERS: list[int] = [
        int(x.strip()) for x in os.getenv("ADMIN_USERS", "").split(",") if x.strip().isdigit()
    ]


settings = Settings()