from typing import Optional
from api.confluence_api import ConfluenceAPI
from api.dto import ContentDTO


class ContentGetter:
    API_ENDPOINT = "/rest/api/content/{page_id}?expand=body.storage,space,ancestors"

    def __init__(self, api: ConfluenceAPI):
        self.api = api

    def get(self, page_id: str) -> Optional[ContentDTO]:
        endpoint = f"{self.API_ENDPOINT.format(page_id=page_id)}"
        response = self.api.get(endpoint)

        if response and response.status_code == 200:
            return ContentDTO(**response.json())
        return None
