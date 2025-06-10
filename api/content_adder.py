from typing import Optional
from api.confluence_api import ConfluenceAPI
from api.dto import ContentDTO


class ContentAdder:
    API_ENDPOINT = "/rest/api/content"

    def __init__(self, api: ConfluenceAPI):
        self.api = api

    def post(self, content: ContentDTO) -> Optional[str]:
        response = self.api.post(
            endpoint=self.API_ENDPOINT, req_body=content.model_dump()
        )
        if response:
            return response.json()["id"]
        return
