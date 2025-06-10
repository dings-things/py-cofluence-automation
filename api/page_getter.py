from pydantic import TypeAdapter
from api.confluence_api import ConfluenceAPI
from typing import List, Optional, Dict

from api.dto import PageDTO


class PageGetter:
    API_ENDPOINT = "/rest/api/content/{parent_page_id}/child/page?expand=version"

    def __init__(self, api: ConfluenceAPI):
        self.api = api
        # PageDTO 리스트 검증 어댑터 생성
        self.page_list_adapter = TypeAdapter(List[PageDTO])

    def get_latest(self, parent_page_id: str) -> Optional[PageDTO]:
        endpoint = f"{self.API_ENDPOINT.format(parent_page_id=parent_page_id)}"
        response = self.api.get(endpoint)
        if response:
            # JSON 데이터를 PageDTO 리스트로 매핑
            pages = self.page_list_adapter.validate_python(response.json()["results"])
            if pages:
                # 최신 페이지가 먼저 오도록 내림차순 정렬
                sorted_pages = sorted(pages, reverse=True)
                return sorted_pages[0] if sorted_pages else None
        return None

    def get(self, parent_page_id: str) -> List[PageDTO]:
        endpoint = f"{self.API_ENDPOINT.format(parent_page_id=parent_page_id)}"
        response = self.api.get(endpoint)
        if response:
            # JSON 데이터를 PageDTO 리스트로 매핑
            pages = self.page_list_adapter.validate_python(response.json()["results"])
            return pages
        return None
