import os
import json


LICENSE_FILE_PATH = "src/science_parser/core/licenses/licenses.json"


class LicenseMeneger:
    @staticmethod
    def get_licenses():
        license_path = os.environ.get("NEUROLINGV_LICENSES_FILE", LICENSE_FILE_PATH)
        with open(license_path, "r", encoding="utf-8") as f:
            s = f.read()
        return json.loads(s)