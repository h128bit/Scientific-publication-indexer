import os
import sys
from pathlib import Path

from science_parser.desktop.st_app.launcher import run_launcher


def get_base_path() -> Path:
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS)
    else:
        return Path().cwd() / "src"


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "__run_streamlit__":
        ## Enter if run as building app
        script_path = sys.argv[2]
        port = sys.argv[3]

        sys.argv = [
            "streamlit", "run", script_path,
            "--server.headless", "true",
            "--server.port", port,
            "--server.address", "127.0.0.1",
            "--global.developmentMode", "false",
            "--logger.level", "info"
        ]
        from streamlit.web import cli as stcli
        sys.exit(stcli.main())

    else:
        ## Entry on run in dev and builded app modes
        from science_parser.desktop.st_app import run_launcher
        root = get_base_path()
        os.environ["_inner_SCIPARSER_ROOT"] = str(root)
        script_path = root / "science_parser/desktop/st_app"
        
        run_launcher(str(script_path))