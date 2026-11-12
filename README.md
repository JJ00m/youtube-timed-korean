# youtube-timed-korean

YouTube 링크를 **시간표시와 원문 근거가 있는 한국어 주제별 요약**으로 정리하는 오픈소스 에이전트 스킬입니다.

Python 도구는 자막 수집·시간 검증·링크 생성을 담당하고, 스킬을 실행하는 AI 에이전트가 한국어 요약과 의미 검토를 담당합니다. 독립 실행형 AI 번역 서비스는 아닙니다.

## 설치

Python 3.10 이상이 필요합니다. Codex의 개인 스킬 경로에 복제하거나, 사용하는 에이전트의 스킬 경로에 배치하세요. 이미 같은 폴더가 있다면 덮어쓰지 마세요.

```sh
git clone https://github.com/JJ00m/youtube-timed-korean.git ~/.codex/skills/youtube-timed-korean
cd ~/.codex/skills/youtube-timed-korean
python -m venv .venv
```

가상환경 활성화:

- Windows PowerShell: `.venv\Scripts\Activate.ps1`
- macOS/Linux: `source .venv/bin/activate`

```sh
python -m pip install -r requirements.txt
```

자막 JSON 가져오기·검사·요약 출력에는 표준 라이브러리만 사용합니다. `youtube-transcript-api`는 YouTube 직접 수집에만 필요합니다. Firecrawl은 선택 경로이며 필수 서비스가 아닙니다.

## 에이전트에서 사용

```text
$youtube-timed-korean
이 유튜브 영상을 시간대별 한국어 요약으로 정리해줘: <URL>
자동자막 오인식은 표시하고, 숫자와 제작 도구 이름은 정확하게 보존해줘.
```

## 직접 실행

```sh
python scripts/captions.py fetch "https://www.youtube.com/watch?v=VIDEO_ID" --out .private/captions.json
python scripts/captions.py inspect .private/captions.json
```

에이전트가 자막을 읽고 아래 형식의 요약 JSON을 작성합니다. `source_ids`는 실제 자막 ID여야 합니다. 요약 생성 자체를 CLI가 대신하지 않습니다.

```json
{
  "mode": "summary",
  "items": [
    {"source_ids": ["s0001", "s0002"], "text": "템포와 스네어로 기본 비트를 구성한다."}
  ]
}
```

```sh
python scripts/captions.py render .private/captions.json .private/summary.json --out .private/summary.ko.md
```

시간 범위와 클릭 가능한 YouTube 링크는 근거 자막에서 계산됩니다. 기존 출력 파일은 덮어쓰지 않습니다. 원본 자막과 실제 산출물은 `.private/`에 보관하고 Git에 올리지 마세요.

## 네트워크 없이 시험

다음 자료는 이 프로젝트에서 직접 작성한 합성 예시입니다.

```sh
python scripts/captions.py import examples/captions.json --provider synthetic --out .private/example.json
python scripts/captions.py render .private/example.json examples/summary.json --out .private/example.ko.md
python -m unittest discover -s tests -v
```

## 범위와 한계

- 제공 기능: 기존 자막 수집, JSON 가져오기, 시간 메타데이터 검사, 근거 기반 Markdown 요약 출력.
- 미제공 기능: 무자막 음성 인식, 영상 화면 분석, 자동 더빙, 전체 자막 번역, SRT 생성.
- 자동자막 겹침은 정상일 수 있어 보존합니다. 오인식과 화면에만 나오는 수치는 별도 검토가 필요합니다.
- YouTube 차단·요청 제한은 발생할 수 있습니다. 오류를 자막 부재로 바꾸어 보고하지 않으며 접근 제한을 우회하지 않습니다.
- 요약문은 전체 영상의 대체 번역문이 아닙니다. 타인의 원문 자막은 이 저장소에 재배포하지 않습니다.
- 오픈소스 코드 라이선스가 영상·자막의 이용 권한을 부여하지는 않습니다.

[실제 검증 기록](docs/validation.md) · [스킬 지침](SKILL.md) · [MIT License](LICENSE)
