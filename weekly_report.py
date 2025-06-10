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
CONFLUENCE_BASE_PAGE_URL = (
    "https://confluence.nexon.com/pages/viewpage.action?pageId={page_id}"
)


def get_this_week_timestr() -> str:
    # 현재 주 목요일 계산
    today = datetime.now()
    days_since_monday = today.weekday()  # 월요일 기준 (0부터 시작)
    days_until_thursday = 3 - days_since_monday  # 목요일은 weekday=3
    this_week_thursday = today + timedelta(days=days_until_thursday)

    # 목요일이 지나면 현재 주 목요일을 다시 앞당기기
    if days_until_thursday < 0:
        this_week_thursday = today - timedelta(days=days_since_monday - 3)

    thursday_date_str = this_week_thursday.strftime("%Y%m%d")

    # 기존 날짜를 현재 주 목요일 날짜로 교체
    return TITLE_FORMAT.format(timestr=thursday_date_str)


def get_last_week_thursday_title() -> str:
    today = datetime.now()
    days_since_monday = today.weekday()  # 0 = 월요일, 3 = 목요일
    this_week_thursday = today + timedelta(days=(3 - days_since_monday))

    # 저번주 목요일은 현재 주 목요일에서 7일 전
    last_week_thursday = this_week_thursday - timedelta(days=7)
    thursday_date_str = last_week_thursday.strftime("%Y%m%d")

    return TITLE_FORMAT.format(timestr=thursday_date_str)


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
        report_link = CONFLUENCE_BASE_PAGE_URL.format(page_id=latest_page_id)
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
        report_link = CONFLUENCE_BASE_PAGE_URL.format(page_id=new_page)
        logger.info(f"새 페이지가 생성되었습니다: {report_link}")
        webhook_sender.send_webhook(
            dto=WeeklyReportDTO(report_link=report_link),
        )
    else:
        logger.error("새 페이지 생성에 실패했습니다.")

except Exception as e:
    logger.error(f"스크립트 실행 중 예외가 발생했습니다: {e}", exc_info=True)
