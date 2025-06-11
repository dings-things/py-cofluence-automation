from datetime import datetime, timedelta
import logging
from typing import List
from api.confluence_api import ConfluenceAPI
from api.content_adder import ContentAdder
from api.content_getter import ContentGetter
from api.dto import PageDTO
from api.page_getter import PageGetter
from config import Settings
from logger import JsonLogger
from webhook_sender import WebhookSender, WeeklyReportDTO

# 상수 설정
TITLE_FORMAT = "{timestr} 주간 보고"
TIMESTR_FORMAT = "%Y%m%d"
CONFLUENCE_BASE_PAGE_URL = "{base_url}/pages/viewpage.action?pageId={page_id}"


def get_thursday_title(offset_weeks: int = 0) -> str:
    today = datetime.now()
    monday = today - timedelta(days=today.weekday())
    thursday = monday + timedelta(days=3, weeks=offset_weeks)
    return TITLE_FORMAT.format(timestr=thursday.strftime(TIMESTR_FORMAT))


def find_page_by_title(pages: List[PageDTO], title: str):
    return next((page for page in pages if page.title == title), None)


def generate_report() -> WeeklyReportDTO:
    pages = page_getter.get(settings.ROOT_PAGE_ID)
    if not pages:
        return Exception("루트 페이지 하위를 불러오기에 실패하였습니다.")

    this_week_title = get_thursday_title(0)
    last_week_title = get_thursday_title(-1)

    this_week_page = find_page_by_title(pages, this_week_title)
    # 이미 이번주 주간 보고가 있는 경우, 웹훅만 전송
    if this_week_page:
        report_link = CONFLUENCE_BASE_PAGE_URL.format(
            base_url=settings.CONFLUENCE_BASE_URL, page_id=this_week_page.id
        )
        return WeeklyReportDTO(report_link=report_link)

    last_week_page = find_page_by_title(pages, last_week_title)
    # 지난주 주간 보고가 없는 경우, 에러
    if not last_week_page:
        return Exception("지난 주 목요일 제목의 페이지가 존재하지 않습니다.")

    # 지난 주 페이지 내용 가져오기
    base_content = content_getter.get(last_week_page.id)
    if not base_content:
        return Exception("기준 페이지의 내용을 가져올 수 없습니다.")

    # 이번 주 제목으로 새 페이지 생성하기
    base_content.title = this_week_title
    new_page_id = content_adder.post(base_content)

    if new_page_id:
        report_link = CONFLUENCE_BASE_PAGE_URL.format(
            base_url=settings.CONFLUENCE_BASE_URL, page_id=new_page_id
        )
        return WeeklyReportDTO(report_link=report_link)
    else:
        return Exception("새 페이지 생성에 실패했습니다.")


if __name__ == "__main__":
    # DI 구성
    settings = Settings()
    logger = JsonLogger(name="weekly_report_logger", level=logging.DEBUG)

    confluence_api = ConfluenceAPI(
        base_url=settings.CONFLUENCE_BASE_URL,
        token=settings.CONFLUENCE_API_TOKEN,
        logger=logger,
    )
    page_getter = PageGetter(confluence_api)
    content_getter = ContentGetter(confluence_api)
    content_adder = ContentAdder(confluence_api)
    webhook_sender = WebhookSender(settings.WEBHOOK_URL, logger)

    logger.info("주간 보고 생성 스크립트 시작")
    result: WeeklyReportDTO = None
    try:
        result = generate_report()
        logger.info(f"주간 보고 생성 완료 : {result.report_link}")
    except Exception as e:
        logger.error(f"스크립트 실행 중 예외가 발생했습니다: {e}", exc_info=True)

    try:
        webhook_sender.send_webhook(dto=result)
        logger.info("웹훅 전송 성공")
    except Exception as e:
        logger.error(f"웹훅 전송 중 예외가 발생했습니다: {e}", exc_info=True)
