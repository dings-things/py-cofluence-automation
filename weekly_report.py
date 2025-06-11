from datetime import datetime, timedelta

import logging
import re
from api.confluence_api import ConfluenceAPI
from api.content_adder import ContentAdder
from api.content_getter import ContentGetter
from api.page_getter import PageGetter
from config import Settings
from logger import JsonLogger
from webhook_sender import WebhookSender, WeeklyReportDTO

settings = Settings()
TITLE_FORMAT = "{timestr} 주간 보고"
TIMESTR_FORMAT = "%Y%m%d"
CONFLUENCE_BASE_PAGE_URL = "{base_url}/pages/viewpage.action?pageId={page_id}"


def get_thursday_of_week(offset_weeks: int = 0) -> str:
    """
    현재 주를 기준으로 offset 주 만큼 이동한 목요일 날짜를 반환한다.
    offset_weeks: 0이면 이번 주, -1이면 저번 주, +1이면 다음 주
    """
    today = datetime.now()
    monday = today - timedelta(days=today.weekday())  # 이번 주 월요일
    target_thursday = monday + timedelta(days=3, weeks=offset_weeks)
    return TITLE_FORMAT.format(timestr=target_thursday.strftime("%Y%m%d"))


def get_this_week_timestr() -> str:
    return get_thursday_of_week(0)


def get_last_week_thursday_title() -> str:
    return get_thursday_of_week(-1)


# 로거 초기화
logger = JsonLogger(
    name="weekly_report_logger",
    level=logging.DEBUG,
)

# Confluence API DI
confluence_api = ConfluenceAPI(
    base_url=settings.CONFLUENCE_BASE_URL,
    token=settings.CONFLUENCE_API_TOKEN,
    logger=logger,
)
page_getter = PageGetter(confluence_api)
content_getter = ContentGetter(confluence_api)
content_adder = ContentAdder(confluence_api)
webhook_sender = WebhookSender(settings.WEEKLY_REPORT_WEBHOOK_URL, logger)

try:
    # Step 1: Root 페이지로부터 가장 최신의 페이지 ID 가져오기
    # 저번주 목요일 제목이 있을 경우 저번주 목요일 제목으로 latest_page_id를 가져옴
    latest_page_id = ""

    pages = page_getter.get(settings.ROOT_PAGE_ID)
    if not pages:
        logger.error("페이지 불러오기에 실패하였습니다.")
        exit(1)

    this_week_title_exists = False
    last_week_page = None
    this_week_title = get_this_week_timestr()
    last_week_title = get_last_week_thursday_title()
    for page in sorted(pages):
        if page.title == this_week_title:
            latest_page_id = page.id
            this_week_title_exists = True
            break
        elif page.title == last_week_title:
            last_week_page = page
        else:
            latest_page_id = page.id

    if this_week_title_exists:
        report_link = CONFLUENCE_BASE_PAGE_URL.format(
            base_url=settings.CONFLUENCE_BASE_URL, page_id=latest_page_id
        )
        logger.info(f"이번 주 목요일 제목이 이미 존재합니다: {report_link}")
        webhook_sender.send_webhook(
            dto=WeeklyReportDTO(report_link=report_link),
        )
        exit(0)

    # 저번주 목요일 제목이 존재할 경우 latest_page_id를 저번주 제목으로 설정
    if last_week_page:
        latest_page_id = last_week_page.id

    # Step 2: 최신 페이지의 컨텐츠 불러오기
    latest_content = content_getter.get(latest_page_id)
    if not latest_content:
        logger.error("최신 페이지의 내용을 가져올 수 없습니다.")
        exit(1)

    # Step 3: 제목 수정 및 새 페이지 업로드
    latest_content.title = this_week_title
    new_page = content_adder.post(latest_content)

    if new_page:
        report_link = CONFLUENCE_BASE_PAGE_URL.format(
            base_url=settings.CONFLUENCE_BASE_URL, page_id=new_page
        )
        logger.info(f"새 페이지가 생성되었습니다: {report_link}")
        webhook_sender.send_webhook(
            dto=WeeklyReportDTO(report_link=report_link),
        )
    else:
        logger.error("새 페이지 생성에 실패했습니다.")

except Exception as e:
    logger.error(f"스크립트 실행 중 예외가 발생했습니다: {e}", exc_info=True)
