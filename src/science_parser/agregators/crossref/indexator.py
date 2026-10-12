import re
import time
import logging
import requests
from datetime import datetime
from collections.abc import Generator

import jmespath

from science_parser.agregators.crossref.utils import normalize_url
from science_parser.agregators.crossref.templates import CROSSREF_URL, CURSOR_PATH


def request_all_crossref(issn: str, 
                         date_from: str, 
                         date_to: str, 
                         rows: int=100, 
                         sleep: int=1) -> Generator:
    """Fetch all Crossref API results for a given ISSN within a date range using cursor-based pagination.

    This generator makes successive requests to the Crossref API, automatically handling
    cursor pagination until all results are retrieved.

    Args:
        issn (str): International Standard Serial Number of the journal to query.
        date_from (str): Start date for filtering articles, in format 'YYYY-MM-DD'.
        date_to (str): End date for filtering articles, in format 'YYYY-MM-DD'.
        rows (int, optional): Number of results per page. Defaults to 100.
        sleep (int, optional): Seconds to wait between API requests to respect rate limits.
            Defaults to 1.

    Yields:
        dict: JSON response from Crossref API for each page of results.

    Raises:
        requests.exceptions.HTTPError: If the API request fails with a non-200 status code.
        requests.exceptions.RequestException: For network-related errors.
        jmespath.exceptions.JMESPathError: If the cursor path extraction fails.

    Example:
        >>> for page in request_all_crossref("1234-5678", "2024-01-01", "2024-12-31"):
        ...     items = page.get("message", {}).get("items", [])
        ...     process_articles(items)

    Note:
        The generator continues until the API response contains no cursor value,
        indicating the last page has been reached.
    """

    url = CROSSREF_URL.format(issn=issn)

    params = {
        "filter": f"from-pub-date:{date_from},until-pub-date:{date_to}",
        "rows": rows,
    }
    cursor = "*"

    while True:
        params["cursor"] = cursor
        res = requests.get(url, params=params)
        res.raise_for_status()
        res = res.json()

        yield res

        cursor = jmespath.search(CURSOR_PATH, res)
        if not cursor:
            break
        time.sleep(sleep)


def get_prefers_jouranl_links(urls_list: list[dict]) -> str|None:
    """Extracts the preferred URL from a list of Crossref link dictionaries.

    Prioritizes links based on content version and intended application in the 
    following order:
    1. Version of Record ('vor') for 'text-mining'.
    2. Accepted Manuscript ('am') for 'text-mining'.
    3. The first available link in the list as a fallback.

    Args:
        urls_list (list[dict]): A list of dictionaries containing URL metadata, 
            where each dictionary is expected to have 'content-version', 
            'intended-application', and 'URL' keys.

    Returns:
        str | None: The preferred URL string, or None if the input list is empty.
    """

    article_url = None
    if urls_list:
        if (var:=list(filter(lambda x: x["content-version"] == "vor" and x["intended-application"] == "text-mining", urls_list))):
            article_url = var[0]
        elif (var:=list(filter(lambda x: x["content-version"] == "am" and x["intended-application"] == "text-mining", urls_list))):
            article_url = var[0]
        else:
            article_url = urls_list[0]
        article_url = article_url["URL"]
    return article_url



def unpack_crossref_dict(d: dict):
    """Parses and standardizes a raw Crossref article metadata dictionary.

    Extracts key information such as publication date, title, DOI, preferred 
    PDF and HTML URLs, abstract (with HTML tags stripped), and license details.

    Args:
        d (dict): The raw dictionary containing article metadata from the Crossref API.

    Returns:
        dict: A standardized dictionary with the following keys:
            - publish_date (datetime): The publication date of the article.
            - article_name (str): The title of the article.
            - doi (str): The Digital Object Identifier.
            - pdf_url (str | None): The preferred PDF URL for text mining.
            - html_url (str | None): The preferred HTML URL for text mining.
            - abstract (str | None): The article abstract with HTML tags removed.
            - license (list[dict]): The license information associated with the article.
    """
    
    result = dict()
    result["created_date"] = datetime(*d["created"]["date-parts"][0])
    result["indexing_date"] = datetime(*d["indexed"]["date-parts"][0])
    try:
        result["published_date"] = datetime(*d["published-online"]["date-parts"][0])
    except KeyError as e:
        result["published_date"] = None
    result["article_name"] = d["title"][0]
    result["doi"] = d["DOI"]

    urls = d["link"]
    pdf_urls = list(filter(lambda x: x["content-type"] == "application/pdf", urls))
    html_urls = list(filter(lambda x: x["content-type"] == "text/html", urls))
    result["pdf_url"] = get_prefers_jouranl_links(pdf_urls)
    result["html_url"] = get_prefers_jouranl_links(html_urls)

    if "abstract" in d and isinstance(d["abstract"], str):
        text = re.sub(r'<[^>]*>', '', d["abstract"])
        result["abstract"] = text
    else: 
        result["abstract"] = None

    result["license"] = d["license"] 

    return result


class CrossrefAgregatorClient:
    """Class for indexing scientific articles from Crossref.

    This class fetches article metadata from the Crossref API, filters them
    based on a predefined list of open access licenses, and yields the valid
    records in batches. Indexing statistics are accumulated in the `report`
    attribute during the indexing process.

    Attributes:
        licenses (list[str]): List of normalized open access license URLs 
            that are considered valid for filtering articles.
        report (dict): Dictionary containing indexing statistics. Updated 
            during the execution of the `indexing` method.
    """
    
    def __init__(self, licenses: list[str]):
        """Initializes the CrossrefAgregatorClient.

        Args:
            licenses (list[str]): List of license URLs to be considered as valid
                open access licenses. They will be normalized during initialization
                using the `normalize_url` function.
        """

        self._logger = logging.getLogger(self.__class__.__name__)
        self.licenses = [normalize_url(item) for item in licenses]

        self.report = {
            "number_articles": 0,
            "successful_num": 0,
            "error_num": 0,
            "with_oa_num": 0,
            "date_from": None,
            "date_to": None,
            }


    def _clear_report_template(self):
        self.report = {
            "number_articles": 0,
            "successful_num": 0,
            "error_num": 0,
            "with_oa_num": 0,
            "date_from": None,
            "date_to": None,
            }

        
    def indexing(self, date_from: str, date_to: str, issn: str) -> Generator[list[dict], None, None]:
        """Indexes scientific articles for a specific journal from Crossref.

        Fetches articles for the given ISSN within the specified date range,
        unpacks the metadata, filters them by the allowed open access licenses,
        and yields matching records in batches.

        This method is a generator that yields batches of unpacked article 
        dictionaries. Indexing statistics are accumulated in `self.report` 
        and can be accessed after the generator is exhausted.

        Args:
            date_from (str): Start date for the indexing period (e.g., 'YYYY-MM-DD').
            date_to (str): End date for the indexing period (e.g., 'YYYY-MM-DD').
            issn (str): The International Standard Serial Number of the journal
                to be indexed.

        Yields:
            list[dict]: A batch of unpacked article dictionaries that match 
            the allowed open access licenses. Each dictionary contains article
            metadata with the following keys:
                - issn (str): The ISSN of the journal.
                - license (str): The normalized URL of the matching open access license.
                - Additional metadata fields from the Crossref API response.

        Note:
            Statistics are accumulated in `self.report` during execution. After 
            exhausting the generator, access the report via `self.report` to get:
                - number_articles (int): Total number of articles processed.
                - successful_num (int): Number of articles successfully unpacked and matched.
                - error_num (int): Number of articles that failed during unpacking.
                - with_oa_num (int): Number of articles with a matching open access license.
        """

        self._clear_report_template()

        for page in request_all_crossref(issn=issn, date_from=date_from, date_to=date_to):
            unpacked_page = []
            for item in page["message"]["items"]:
                self.report["number_articles"] += 1
                try:
                    unpack_d = unpack_crossref_dict(item)
                    unpack_d["issn"] = issn
                except Exception as e:
                    self._logger.error(f"ERROR IN UNPACK CROSSREF DICT: MSG: {e}")
                    self.report["error_num"] += 1
                    continue

                # check on open access license
                llist = unpack_d["license"]
                for item in llist:
                    url = item["URL"]
                    if normalize_url(url) in self.licenses:
                        unpack_d["license"] = url 
                        self.report["with_oa_num"] += 1
                        break 
                else:
                    continue
            
                unpacked_page.append(unpack_d)
                self.report["successful_num"] += 1

                #  find published indexed articles date range
                publish_date = unpack_d["published_date"]
                if publish_date:
                    if self.report["date_from"] is None:
                        self.report["date_from"] = publish_date
                    else:
                        self.report["date_from"] = min(publish_date, self.report["date_from"])

                    if self.report["date_to"] is None:
                        self.report["date_to"] = publish_date
                    else:
                        self.report["date_to"] = max(publish_date, self.report["date_to"])


            if unpacked_page:
                yield unpacked_page 
              
            
