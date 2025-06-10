import logging
import requests


class ConfluenceAPI:
    def __init__(self, base_url: str, token: str, logger: logging.Logger) -> None:
        self.base_url = base_url
        self.token = token
        self.logger = logger

    def __get_header(self) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}",
        }

    def __get_url(self, endpoint: str) -> str:
        return f"{self.base_url}{endpoint}"

    def get(self, endpoint: str) -> requests.Response:
        url = self.__get_url(endpoint)
        headers = self.__get_header()

        self.logger.info(f"GET Request: URL={url}")
        try:
            response = requests.get(url=url, headers=headers)
            response.raise_for_status()
        except requests.RequestException as e:
            self.logger.exception(f"GET Request failed: URL={url}, Error={e}")
            return

        self.logger.info(f"GET Response: URL={url}, Status={response.status_code}")
        return response

    def post(self, endpoint: str, req_body: dict) -> requests.Response:
        url = self.__get_url(endpoint)
        headers = self.__get_header()

        self.logger.info(f"POST Request: URL={url}")
        try:
            response = requests.post(url=url, headers=headers, json=req_body)
            response.raise_for_status()
        except requests.RequestException as e:
            self.logger.exception(f"POST Request failed: URL={url}, Error={e}")
            return

        self.logger.info(f"POST Response: URL={url}, Status={response.status_code}")
        return response
