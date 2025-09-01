import json
from os import getenv
from typing import Optional

from agno.tools import Toolkit
from agno.utils.log import log_info, log_error

try:
    from bravesearch import BraveSearch, BraveSearchAPIError
except ImportError:
    raise ImportError("`brave-search-python-client` not installed. Please install using `pip install brave-search-python-client`")


class BraveSearchTools(Toolkit):
    """
    BraveSearch is a toolkit for searching Brave easily.

    Args:
        api_key (str, optional): Brave API key. If not provided, will use BRAVE_API_KEY environment variable.
        fixed_max_results (Optional[int]): A fixed number of maximum results.
        fixed_language (Optional[str]): A fixed language for the search results.
        wait_time (Optional[int]): The time to wait between retries.
        retries (Optional[int]): The number of retries to attempt.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        fixed_max_results: Optional[int] = None,
        fixed_language: Optional[str] = None,
        wait_time: int = 5,
        retries: int = 3,
        **kwargs,
    ):
        self.api_key = api_key or getenv("BRAVE_API_KEY")
        if not self.api_key:
            raise ValueError("BRAVE_API_KEY is required. Please set the BRAVE_API_KEY environment variable.")

        self.fixed_max_results = fixed_max_results
        self.fixed_language = fixed_language

        self.brave_client = BraveSearch(
            api_key=self.api_key,
            wait_time=wait_time,
            retries=retries,
        )

        tools = []
        tools.append(self.brave_search)

        super().__init__(
            name="brave_search",
            tools=tools,
            **kwargs,
        )

    def brave_search(
        self,
        query: str,
        max_results: int = 5,
        country: str = "US",
        search_lang: str = "en",
    ) -> str:
        """
        Search Brave for the specified query and return the results.

        Args:
            query (str): The query to search for.
            max_results (int, optional): The maximum number of results to return. Default is 5.
            country (str, optional): The country code for search results. Default is "US".
            search_lang (str, optional): The language of the search results. Default is "en".
        Returns:
            str: A JSON formatted string containing the search results.
        """
        final_max_results = self.fixed_max_results if self.fixed_max_results is not None else max_results
        final_search_lang = self.fixed_language if self.fixed_language is not None else search_lang

        if not query:
            return json.dumps({"error": "Please provide a query to search for"})

        try:
            log_info(f"Searching Brave for: {query}")

            search_results = self.brave_client.search(
                q=query,
                count=final_max_results,
                country=country,
                search_lang=final_search_lang,
                result_filter="web",
            )

            filtered_results = {
                "web_results": [],
                "query": query,
                "total_results": 0,
            }

            if search_results and search_results.web and search_results.web.results:
                web_results = []
                for result in search_results.web.results:
                    web_result = {
                        "title": result.title,
                        "url": str(result.url),
                        "description": result.description,
                    }
                    web_results.append(web_result)
                filtered_results["web_results"] = web_results
                filtered_results["total_results"] = len(web_results)

            return json.dumps(filtered_results, indent=2)

        except BraveSearchAPIError as e:
            log_error(f"Brave Search API error for query '{query}': {e}")
            return json.dumps({"error": f"Brave Search API error: {e}"})
        except Exception as e:
            log_error(f"An unexpected error occurred during Brave search for query '{query}': {e}")
            return json.dumps({"error": f"An unexpected error occurred: {e}"})
