"""Google search command for AutoLlama."""
from __future__ import annotations

import json
from itertools import islice
from typing import TYPE_CHECKING

from duckduckgo_search import DDGS

from autollama.commands.command import command
from autollama.logs import logger

if TYPE_CHECKING:
    from autollama.config import Config


@command(
    "google",
    "Google Search",
    '"query": "<query>"',
    lambda config: not config.google_api_key,
)
def google_search(query: str, config: Config, num_results: int = 8) -> str:
    """Return the results of a Google search using DuckDuckGo as a fallback.

    Args:
        query (str): The search query.
        num_results (int): The number of results to return.

    Returns:
        str: The JSON-encoded results of the search.
    """
    search_results = []
    if not query:
        return json.dumps(search_results)

    results = DDGS().text(query)
    if not results:
        return json.dumps(search_results)

    for item in islice(results, num_results):
        search_results.append(item)

    results_json = json.dumps(search_results, ensure_ascii=False, indent=4)
    logger.debug("SEARCH RESULTS: %s", results_json)
    
    return safe_google_results(results_json)


@command(
    "google",
    "Google Search",
    '"query": "<query>"',
    lambda config: bool(config.google_api_key) and bool(config.custom_search_engine_id),
    "Configure google_api_key and custom_search_engine_id.",
)
def google_official_search(
    query: str, config: Config, num_results: int = 8
) -> str:
    """Return the results of a Google search using the official Google API.

    Args:
        query (str): The search query.
        num_results (int): The number of results to return.

    Returns:
        str: The JSON-encoded results of the search URLs.
    """
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError

    try:
        # Get the Google API key and Custom Search Engine ID from the config file
        service = build("customsearch", "v1", developerKey=config.google_api_key)

        # Send the search query and retrieve the results
        result = service.cse().list(q=query, cx=config.custom_search_engine_id, num=num_results).execute()

        # Extract the search result items from the response
        search_results = result.get("items", [])

        # Create a list of only the URLs from the search results
        search_results_links = [item["link"] for item in search_results]

    except HttpError as e:
        # Handle errors in the API call
        error_details = json.loads(e.content.decode())

        # Check if the error is related to an invalid or missing API key
        if error_details.get("error", {}).get("code") == 403 and "invalid API key" in error_details.get("error", {}).get("message", ""):
            return "Error: The provided Google API key is invalid or missing."
        else:
            return f"Error: {e}"

    # Log the search results
    results_json = json.dumps(search_results_links, ensure_ascii=False, indent=4)
    logger.debug("SEARCH RESULTS: %s", results_json)
    
    return safe_google_results(search_results_links)


def safe_google_results(results: str | list) -> str:
    """Ensure the search results are returned in a safe format.

    Args:
        results (str | list): The search results.

    Returns:
        str: The safely encoded search results.
    """
    if isinstance(results, list):
        safe_message = json.dumps(
            [result.encode("utf-8", "ignore").decode("utf-8") for result in results],
            ensure_ascii=False,
            indent=4
        )
    else:
        safe_message = results.encode("utf-8", "ignore").decode("utf-8")
    return safe_message
