from pathlib import Path

from science_parser.desktop.st_app import run_launcher


if __name__ == "__main__":
    root = Path().cwd()
    script_path = root / "src/science_parser/desktop/st_app"
    run_launcher(script_path)