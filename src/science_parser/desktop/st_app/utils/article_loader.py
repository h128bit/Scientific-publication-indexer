import requests
from pathlib import Path

from tenacity import retry, stop_after_attempt, wait_random

from science_parser.desktop.utils.download_utils import check_object_on_file
from science_parser.agregators.crossref import CrossrefAgregatorClient
from science_parser.core.licenses.manager import LicenseMeneger


@retry(stop=stop_after_attempt(3), wait=wait_random(1, 5))
def _request_with_retry(url):
    response = requests.get(url)
    response.raise_for_status()
    return response


class ArticleLoader:
    def __init__(self):
        licenses = LicenseMeneger.get_licenses()
        self.indexator = CrossrefAgregatorClient(licenses)
        self.status = dict()

    def _clear_status(self):
        self.status = dict()

    def download_by_issn(self, date_from: str, date_to: str, issn: str, path_to_save: str|Path):

        self._clear_status()

        page_num = 0
        for page in self.indexator.indexing(date_from, date_to, issn):
            page_num += 1
            for i, d in enumerate(page):
                url = d["pdf_url"]

                try:
                    response = _request_with_retry(url)
                except Exception as e:
                    self.status["status"] = "err"
                    self.status["msg"] = str(e)
                    raise e

                res = check_object_on_file(response, url)

                if res["status"] == "html":
                    self.status["status"] = "err"
                    self.status["msg"] = "html"
                elif res["status"] == "json":
                    self.status["status"] = "err"
                    self.status["msg"] = "json"
                    self.status["json"] = res["json"] 

                filename = res["filename"]

                path_to_save_file = Path(path_to_save) / filename
                with open(path_to_save_file, "wb") as f:
                    f.write(response.content)

                yield {"item": i, "page_size": len(page), "page_num": page_num}

        self.status["status"] = "ok"


    def get_report(self):
        return self.indexator.report
