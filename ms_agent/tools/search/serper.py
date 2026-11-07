# Candidate for etheia-agent-map — no existing equivalent could be inspected.
# See: https://github.com/Etheia-Consulting-LLC/etheia-agent-map
import os
import requests

from ms_agent.tools.search.search_base import (BaseResult, SearchEngine,
                                               SearchEngineType, SearchRequest,
                                               SearchResponse, SearchResult)


class SerperSearchRequest(SearchRequest):
    """Google web discovery request; no scholarly metadata or page scraping."""

    def __init__(self,
                 query: str,
                 num_results: int = 5,
                 location: str = None,
                 **kwargs):
        super().__init__(query, max(1, min(10, int(num_results or 5))),
                         **kwargs)
        self.location = location

    def to_dict(self):
        arguments = {'q': self.query, 'num': self.num_results}
        if self.location:
            arguments['location'] = self.location
        return arguments


class SerperSearchResult(SearchResult):
    """Real source titles, URLs, and snippets in the shared result contract."""

    def __init__(self, query, arguments=None, response=None):
        super().__init__(query, arguments, response)
        self.response = self._process_results()

    def _process_results(self):
        return SearchResponse(results=[
            BaseResult(
                url=item['link'],
                id=item['link'],
                title=item.get('title'),
                summary=item.get('snippet'),
                highlights=[item['snippet']] if item.get('snippet') else None)
            for item in (self.response or {}).get('organic', []) or []
            if item.get('link')
        ])


class SerperSearch(SearchEngine):
    """Optional snippet-only web provider; content fetching stays separate."""

    engine_type = SearchEngineType.SERPER

    def __init__(self,
                 api_key: str = None,
                 base_url: str = None,
                 request_timeout: float = 30.0):
        self.api_key = api_key or os.getenv('SERPER_API_KEY')
        if not self.api_key:
            raise ValueError('SERPER_API_KEY is required')
        self.base_url = (base_url or os.getenv('SERPER_BASE_URL')
                         or 'https://google.serper.dev').rstrip('/')
        self.request_timeout = request_timeout

    def search(self,
               search_request: SerperSearchRequest) -> SerperSearchResult:
        arguments = search_request.to_dict()
        response = requests.post(
            self.base_url + '/search',
            headers={
                'X-API-KEY': self.api_key,
                'Content-Type': 'application/json'
            },
            json=arguments,
            timeout=self.request_timeout)
        response.raise_for_status()
        return SerperSearchResult(search_request.query, arguments,
                                  response.json())

    @classmethod
    def get_tool_definition(cls, server_name: str = 'web_search'):
        tool = super().get_tool_definition(server_name)
        tool['description'] = (
            'Search the web for source titles, URLs, and snippets. '
            'Full pages require the separate content fetcher.')
        return tool

    @classmethod
    def build_request_from_args(cls, **kwargs) -> SerperSearchRequest:
        return SerperSearchRequest(**kwargs)
