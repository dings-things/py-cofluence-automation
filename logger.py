import logging
import json
import traceback


class JsonFormatter(logging.Formatter):
    def format(self, record):
        # 기본 로그 메시지 생성
        log_record = {
            "level": record.levelname,
            "time": self.formatTime(record),
            "message": record.getMessage(),
            "name": record.name,
        }
        # 예외 정보가 있을 경우 추가
        if record.exc_info:
            log_record["exception"] = "".join(
                traceback.format_exception(*record.exc_info)
            )

        return json.dumps(log_record, ensure_ascii=False)


class JsonLogger(logging.Logger):
    def __init__(self, name: str, level=logging.NOTSET):
        super().__init__(name, level)
        self.addHandler(logging.StreamHandler())  # 기본 핸들러 추가
        self.setLevel(level)  # 로거 레벨 설정

    def log(self, level, msg, *args, **kwargs):
        # 로그 메시지를 JSON 형식으로 출력
        if isinstance(msg, dict):
            msg = json.dumps(msg, ensure_ascii=False)
        super().log(level, msg, *args, **kwargs)
