import os
import json

from pathlib import Path

LICENSE_FILE_PATH = "science_parser/core/licenses/licenses.json"


class LicenseMeneger:
    @staticmethod
    def get_licenses():
        root = Path(os.environ.get("_inner_SCIPARSER_ROOT", ""))

        print(f"IN LICENSE MANAGER PATH TO LICENSES {root}")

        license_path = os.environ.get("SCIPARSER_LICENSES_FILE", root/LICENSE_FILE_PATH)
        with open(license_path, "r", encoding="utf-8") as f:
            s = f.read()
        return json.loads(s)