from pydantic import BaseModel


class StorageDTO(BaseModel):
    value: str  # 페이지 본문 (HTML 형식)
    representation: str  # 페이지 본문 형식 (storage[HTML], view[마크다운])


class BodyDTO(BaseModel):
    storage: StorageDTO  # 페이지 본문 정보


class AncestorDTO(BaseModel):
    id: str  # 부모 페이지 ID


class VersionDTO(BaseModel):
    when: str  # 페이지 수정 날짜 및 시간
    number: int  # 버전 번호
    minorEdit: bool  # 사소한 수정 여부


class SpaceDTO(BaseModel):
    key: str  # 공간 키 (Space Key)


class ContentDTO(BaseModel):
    title: str  # 페이지 제목
    space: SpaceDTO  # 공간 키 (Space Key)
    body: BodyDTO  # 페이지 본문 (HTML 형식)
    ancestors: list[AncestorDTO]  # 부모 페이지 ID

    def model_dump(self) -> dict:
        """
        Confluence API에서 요구하는 형식으로 데이터를 반환
        """
        return {
            "type": "page",
            "title": self.title,
            "space": self.space.model_dump(),
            "body": self.body.model_dump(),
            "ancestors": [self.ancestors[-1].model_dump()],
        }


class PageDTO(BaseModel):
    id: str  # 페이지 ID
    type: str  # 페이지 타입
    title: str  # 페이지 제목 (markdown)
    status: str  # 페이지 상태 (current[활성화], trashed[휴지통], draft[초안], deleted[영구삭제])
    version: VersionDTO  # 페이지 버전 정보

    # sort 하면 가장 최신의 Page가 return 되도록 iterator overide
    def __lt__(self, other: "PageDTO") -> bool:
        """
        상태가 current인 페이지가 우선, 그 다음 최신 version.when 기준으로 정렬
        """
        if self.status == "current" and other.status != "current":
            return False
        if self.status != "current" and other.status == "current":
            return True
        # 둘 다 current이거나 둘 다 current가 아닌 경우 날짜 비교
        return self.version.when < other.version.when
