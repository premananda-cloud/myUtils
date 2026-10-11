# src/make_env.py
"""Interactively generate a .env file for the database config."""

import getpass
import os
from pathlib import Path
from urllib.parse import quote_plus

DEFAULTS = {
    "DB_NAME": "db_learn",
    "DB_OWNER": "premananda",
    "DB_HOST": "localhost",
    "DB_PORT": "5432",
    "DB_USER": "postgres",
    "DB_PASSWORD": "",
}

ENV_FILENAME = ".env"


def ask(prompt: str, default: str = "", secret: bool = False) -> str:
    """Prompt the user; return default if they just press Enter."""
    if secret:
        value = getpass.getpass(f"{prompt} [{'hidden' if default else ''}]: ")
    else:
        shown = f" [{default}]" if default else ""
        value = input(f"{prompt}{shown}: ").strip()
    return value or default


def ask_port(default: str = "5432") -> str:
    """Prompt for a port number and validate it's numeric."""
    while True:
        value = ask("DB_PORT", default).strip()
        if value.isdigit():
            return value
        print("  ⚠️  Port must be a number. Try again.")


def collect_values() -> dict[str, str]:
    print("Enter values (press Enter to accept the default):\n")
    values: dict[str, str] = {}
    for key, default in DEFAULTS.items():
        if key == "DB_PORT":
            values[key] = ask_port(default)
        else:
            values[key] = ask(key, default, secret=(key == "DB_PASSWORD"))
    return values


def prompt_output_dir(default: str = ".") -> Path:
    """Ask for the output directory. On invalid input, offer default or retry."""
    while True:
        raw = input(f"\nSave .env in which directory? [{default}]: ").strip() or default
        candidate = Path(raw).expanduser()

        # Resolve to absolute path, raising if it doesn't exist
        try:
            resolved = candidate.resolve(strict=True)
        except FileNotFoundError:
            print(f"  ⚠️  Path does not exist: {raw}")
            if _fallback_to_default(default):
                return Path(default).resolve()
            continue
        except OSError as e:
            print(f"  ⚠️  Invalid path: {e}")
            if _fallback_to_default(default):
                return Path(default).resolve()
            continue

        if not resolved.is_dir():
            print(f"  ⚠️  Not a directory: {raw}")
            if _fallback_to_default(default):
                return Path(default).resolve()
            continue

        if not os.access(resolved, os.W_OK):
            print(f"  ⚠️  Directory is not writable: {raw}")
            if _fallback_to_default(default):
                return Path(default).resolve()
            continue

        return resolved


def _fallback_to_default(default: str) -> bool:
    """Ask whether to fall back to the default directory. Returns True for yes."""
    answer = input(f"  Use default ({default}) instead? [Y/n]: ").strip().lower()
    return answer != "n"


def build_env_text(v: dict[str, str]) -> str:
    user = quote_plus(v["DB_USER"])
    password = quote_plus(v["DB_PASSWORD"])
    host = v["DB_HOST"]
    port = v["DB_PORT"]
    name = quote_plus(v["DB_NAME"])
    url = f"postgresql://{user}:{password}@{host}:{port}/{name}"

    return f"""# Database Configuration
DB_NAME={v["DB_NAME"]}
DB_OWNER={v["DB_OWNER"]}
DB_PASSWORD={v["DB_PASSWORD"]}
DB_HOST={v["DB_HOST"]}
DB_PORT={v["DB_PORT"]}
DB_USER={v["DB_USER"]}

# Optional: Full Database URL
DATABASE_URL={url}
"""


def confirm_overwrite(path: Path) -> bool:
    if not path.exists():
        return True
    answer = input(f"\n{path} already exists. Overwrite? [y/N]: ").strip().lower()
    return answer == "y"


def main() -> None:
    values = collect_values()
    out_dir = prompt_output_dir(default=".")
    out_path = out_dir / ENV_FILENAME

    if not confirm_overwrite(out_path):
        print("Aborted.")
        return

    out_path.write_text(build_env_text(values))
    print(f"\n✅ Wrote {out_path}")


if __name__ == "__main__":
    main()
