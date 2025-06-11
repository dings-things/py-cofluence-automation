import logging
from slack_sdk.webhook import WebhookClient, WebhookResponse
from abc import ABC, abstractmethod


# to_json을 implement 하는 pydantic 모델 인터페이스 정의
class WebhookDTOInterface(ABC):
    @abstractmethod
    def to_json(self) -> dict:
        """JSON 형식으로 변환하는 메서드"""
        pass


class WeeklyReportDTO(WebhookDTOInterface):
    def __init__(self, report_link: str):
        self.report_link = report_link

    def to_json(self) -> dict:
        # JSON 문자열 반환
        return {"report_link": self.report_link}


class WebhookSender:
    def __init__(self, webhook_url: str, logger: logging.Logger):
        self.client = WebhookClient(webhook_url)
        self.logger = logger

    def send_webhook(self, dto: WebhookDTOInterface) -> WebhookResponse:
        """웹훅을 보내는 메서드."""
        try:
            # DTO의 데이터를 JSON 문자열로 변환 후 전송
            response = self.client.send_dict(body=dto.to_json())
            self.logger.info(response)
        except Exception as e:
            self.logger.exception(
                f"Webhook Request failed: dto={dto.to_json()}, Error={e}"
            )
