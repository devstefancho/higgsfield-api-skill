---
name: higgsfield-api
description: 이 repo 의 Higgsfield 이미지·영상 생성 단일 입구. 샷 파일에 프롬프트를 다듬고, 웹 플랜 크레딧으로 시험(draft)한 뒤, 통과한 샷만 API 지갑으로 실전 생성(run)하고 결과를 내려받는다. Use when Higgsfield 로 생성, 영상·이미지 만들기, 프롬프트 다듬기·시험, 샷 파일, 모델 고르기, 견적(estimate), API 영상 촬영 데모. 이 repo 에서는 글로벌 higgsfield-generate 등 higgsfield-* 스킬 대신 이것을 쓴다.
---

# Higgsfield API

모든 호출은 `scripts/hfapi.py` 로 한다. 사용법은 `python3 scripts/hfapi.py -h`.

## 스킬만 불렸을 때: 번호 메뉴로 시작한다

스킬만 불렸거나("/higgsfield-api", "힉스필드로 뭐 만들자") 무엇을 할지 정해지지 않았으면, 생성부터 하지 말고 아래 메뉴를 그대로 평문으로 보여 준다. 사용자는 번호만 답해도 된다. 요청에 이미 작업이 드러나 있으면(예: "이 이미지로 5초 영상") 메뉴를 건너뛰고 해당 번호의 절차로 바로 간다.

```
어떤 걸 하시겠어요? 번호로 답해 주세요.

1. 이미지 만들기 (캐릭터 시트, 장면 스틸)
2. 글로 영상 만들기
3. 이미지로 영상 만들기 (첫 프레임, 또는 첫·끝 프레임)
4. 참조로 영상 만들기 (캐릭터 시트로 캐릭터 모양 유지)
5. 영상 이어 붙이기 / 고치기
6. 움직임 옮기기 (원본 영상의 동작을 내 캐릭터에)
7. 이전 샷 이어서 다듬기
8. 쓴 크레딧·비용과 기록 보기
9. 요청하는 법 예시 보기
```

### 번호별로 물을 것

사용자가 번호를 고르면 요청이 얼마나 구체적인지 본다.

- **구체적이면** (무엇이, 어떤 스타일로, 무엇을 하는지가 있음): 아래 표에서 빈칸만 한 번에 묻는다. 칸마다 기본값을 적어 "기본값으로" 한마디로 끝낼 수 있게 한다.
- **막연하면** (한 줄이 안 되거나 "멋있게", "알아서" 뿐): `references/interview.md` 의 인터뷰로 간다. 사용자는 영상 용어도, 스타일·구도·카메라 움직임을 정해야 한다는 것도 모른다고 가정한다. 라운드마다 질문 세 개까지, 용어를 쉬운 말로 풀고, 번호 선택지와 추천을 붙인다. 마지막 요약에서 사용자가 확인하기 전에는 생성하지 않는다.

어느 쪽이든 이미 말한 것은 다시 묻지 않고, 묻는 끝에 `references/request-examples.md` 에서 그 번호에 맞는 좋은·아쉬운 요청 한두 쌍을 "왜"와 함께 붙인다.

| 번호 | 물을 것 (기본값) | 엔드포인트 (시험 CLI 모델) |
|---|---|---|
| 1 | 무엇을 그릴지 한 줄 · 스타일(픽셀, 애니, 모션 그래픽, 실사) · 캐릭터가 여럿이면 시트로 할지 (16:9, 글자 없이) | `xai/grok-imagine-image-2.0` (`grok_image_2_0`), 벡터 그래픽은 `recraft/v4.1/text-to-image` (`recraft_v4_1`) |
| 2 | 장면 한 줄 · 카메라(고정) · 길이(5초) | `bytedance/seedance-2.5/text-to-video` (`seedance_2_5`) |
| 3 | 이미지 경로 1장 또는 첫·끝 2장 · 무엇이 움직이는지 · 카메라(고정) · 길이(5초) | `bytedance/seedance-2.5/image-to-video` (`seedance_2_5` mode omni_reference, start/end image) |
| 4 | 참조 이미지(시트) 경로 · 장면과 동작 · 캐릭터가 보는 방향과 이동 방향 · 길이(5초) | `bytedance/seedance-2.5/reference-to-video` (`seedance_2_5` mode omni_reference, image) |
| 5 | 영상 경로 · 이어 붙이기인지 고치기인지 · 뒤에 일어날 일 또는 바꿀 내용 · 길이(5초) | `bytedance/seedance-2.5/video-extend` · `video-edit` (`seedance_2_5` mode video_extension · video_edit) |
| 6 | 원본 영상 경로 · 캐릭터 이미지 경로(1~8장) · 해상도(480p) | `higgsfield/genjutsu/motion-transfer/v1.0` (예시 코드 `examples/motion_transfer.py`) |
| 7 | `prompts/` 아래 샷 파일 목록을 번호로 보여 주고 고르게 한다 · 무엇이 아쉬웠는지 한 가지 | 샷 파일에 적힌 것 |
| 8 | 묻지 않는다. `~/works/data/higgsfield/requests.jsonl` 을 날짜별·길(크레딧/API)별로 합계, 최근 생성 목록, `higgsfield account status` 잔액을 보여 준다 | 없음 |
| 9 | 묻지 않는다. `references/request-examples.md` 의 요청 문장 표를 보여 주고 다시 메뉴로 | 없음 |

**생성 전에 비용을 먼저 보여 준다.** 크레딧 시험이든 API 실전이든, 생성 명령을 돌리기 전에 사용자에게 두 값을 알린다. (1) 같은 샷을 API 로 뽑을 때의 예상 비용: `hfapi.py estimate <샷>`. API 키가 있으면 POST /estimate 실시간 값, 없으면 `references/api-prices.json` 가격표 기준 추정이다(가격표 날짜와 "할인 끝나면" 값을 같이 말한다). (2) 크레딧 시험 비용: `draft` 가 실행 전에 두 값(API 예상과 크레딧)을 모두 출력한다. 가격표에 없는 모델이면 없다고 말하고 키가 생긴 뒤 estimate 로 확인한다고 알린다.

1~7 은 모두 기본값이 "크레딧 시험까지"다. 형식 기본값은 16:9, 영상 5초, 시험 480p · 실전 720p, 소리 끔. API 실전은 사용자가 "API 로 뽑아줘"라고 할 때만 한다.

결과를 보여 준 뒤 사용자가 "별로야"처럼 막연하게 말하면, `request-examples.md` 마지막 줄처럼 무엇이 별로인지 한 가지를 되묻는다. 시험에서 새로 배운 좋은·아쉬운 사례는 그 파일에 한 줄씩 더한다.

## 지갑이 둘, 길도 둘

이 repo 에서 Higgsfield 생성은 이 스킬 하나로만 한다. 글로벌 `higgsfield-*` 스킬(higgsfield-generate 등)은 부르지 않는다. 어느 지갑에서 돈이 나가는지 명령 이름과 출력 머리표로 구분한다.

| 길 | 명령 | 지갑 | 쓰는 때 |
|---|---|---|---|
| 시험 | `draft` | higgsfield.ai 웹 플랜 크레딧 (공식 `higgsfield` CLI 경유) | 프롬프트·모델·구도 시험. 몇 번이든 |
| 실전 | `estimate` `submit` `run` `upload` | API 콘솔(open.higgsfield.ai) 선불 지갑 | 시험을 통과한 샷만. 최소 시도로 한 번에 |

- 출력 머리표: `[CREDITS web plan]` 은 크레딧, `[API wallet]` 은 API 지갑이다. 둘 다 금액을 먼저 보여 주고 확인을 받는다(`-y` 로 생략).
- 시험과 실전은 같은 모델로 한다. 아래 짝 표에 없는 모델(Nano Banana, GPT Image, Veo 등 CLI 전용)로 시험하면 실전에서 재현할 수 없으니 쓰지 않는다.
- CLI 파라미터 이름은 API 와 다를 수 있다. 시험 블록을 쓰기 전에 `higgsfield model get <job_type>` 으로 확인한다. 입력 이미지는 CLI 에서 `start-image` 에 로컬 경로를 넣으면 자동 업로드된다.

### 모델 짝 (API 엔드포인트 ↔ CLI job_type)

| 모델 | API `endpoint` | CLI `draft.model` | 쓰임 |
|---|---|---|---|
| Soul 2 | `higgsfield-ai/soul/v2/standard` | `text2image_soul_v2` | 사진풍·에디토리얼 이미지. 글자·그래픽에는 약함 |
| Recraft V4.1 | `recraft/v4.1/text-to-image` 외 | `recraft_v4_1` | 벡터·플랫 그래픽, 모션 그래픽 소재 |
| Grok Image 2.0 | `xai/grok-imagine-image-2.0` | `grok_image_2_0` | 강한 대비, 애니풍 스틸 |
| Z Image | `z-image/turbo` | `z_image` | 가장 싸고 빠른 초안 |
| Seedance 2.5 | `bytedance/seedance-2.5/{text,image,reference}-to-video` | `seedance_2_5` | 기본 영상 모델, 멀티샷 |
| Kling 3.0 | `kling-video/v3.0/pro/...` | `kling3_0` | 값싼 단순 모션 |
| Kling 3.0 Turbo | `kling-video/v3.0-turbo/...` | `kling3_0_turbo` | 빠른 움직임 시험 |
| Hailuo 2.3 | `minimax/hailuo-2.3/standard/...` | `minimax_hailuo` | 가장 싼 영상, 물리 표현 |
| MiniMax H3 | `minimax/h3/...` | `minimax_h3` | 긴 프롬프트, 2K |
| Wan 3.0 / Prime | `alibaba/wan-3.0[-prime]/...` | `wan3_0` / `wan3_0_prime` | 스타일라이즈 |
| Grok Video 1.5 | `xai/grok-imagine-video/v1.5/reference-to-video` | `grok_video_v15` | 애니풍·고대비 i2v (시작 이미지 필수) |

## 먼저 알 것
- **인증**: `Authorization: Key <key_id>:<key_secret>`. 값은 env `HF_API_KEY_ID`/`HF_API_KEY_SECRET` 또는 `~/.secrets/higgsfield-api.json`(0600). 키 값을 출력하거나 사용자에게 붙여넣게 하지 않는다. 녹화에 키가 찍혔으면 녹화 뒤 콘솔에서 키를 교체한다.
- **모델 카탈로그의 정본은 콘솔이다.** `docs-sync` 가 만든 catalog.json 은 문서 기준이라, 계정에서 막힌 모델은 404·423·503 으로 돌아온다.
- **생성은 비동기다.** submit 이 request_id 를 돌려주고, status 가 completed·failed·nsfw·canceled 중 하나가 될 때까지 기다린다. failed·nsfw 는 과금되지 않는다. 결과 URL 은 7일 뒤 사라질 수 있어 `wait` 가 바로 `~/works/data/higgsfield/<날짜>/` 로 내려받는다.
- **생성 POST 는 자동 재시도하지 않는다.** 멱등 키가 없어 타임아웃 뒤 다시 보내면 두 번 과금될 수 있다. 끊기면 `requests.jsonl` 에서 request_id 를 찾아 `wait` 로 이어 간다.

## 흐름: 다듬기 먼저, 생성은 나중

1. `docs-sync` (처음 한 번, 또는 문서 갱신 시 `--force`). 문서는 `~/works/data/higgsfield/docs/` 에 떨어진다.
2. 모델 고르기: `models <검색어>` 로 엔드포인트를 찾고 `show <엔드포인트>` 로 스키마와 사용 메모를 읽는다.
3. 샷 파일 쓰기: `prompts/_template.md` 를 복사해 `prompts/<샷>.md`. 목적, 모델 선택 이유, 버전 기록 표를 채우고 마지막 json 블록에 endpoint·params 를 쓴다. 프롬프트는 `references/prompting.md` 규칙을 따른다.
4. `check <샷>`: 필수 필드, 허용값, 최소·최대, 모르는 필드, 프롬프트 길이 한도를 본다. 통과할 때까지 3으로 돌아간다.
5. 시험(크레딧): 샷 파일의 `draft` 블록을 채우고 `draft <샷>`. 이미지로 구도를 먼저 고정하고, 영상은 짧은 길이·낮은 해상도로 움직임만 본다. 고를 것이 있으면 사용자가 고른다. 결과를 버전 기록 표에 적고, 통과할 때까지 3으로 돌아간다.
6. `estimate <샷>`: 실전 비용을 확인한다. 키가 있으면 실시간, 없으면 가격표 추정. 사용자가 정한 한도를 넘으면 해상도·길이·모델을 낮추거나 묻는다.
7. 실전(API): `run <샷>` (check, estimate, 확인, submit, wait, 다운로드). 비대화 환경에서는 `-y` 가 있어야 제출된다. API 지갑이 나가는 명령이므로 사용자가 이 샷의 실전 생성을 허락했을 때만 `-y` 를 붙인다.
8. 결과를 샷 파일 버전 기록 표에 적는다(request_id, estimate, 결과 파일, 무엇이 좋았고 무엇을 바꿀지).

입력 이미지가 로컬 파일이면 `upload <파일>` 이 public_url 을 돌려준다. 그 URL 을 image_url 등에 넣는다.

## 기록

- `~/works/data/higgsfield/requests.jsonl`: submit·done·upload 이벤트를 한 줄씩 남긴다(append-only). 비용 대조와 이어 받기에 쓴다.
- 결과 파일: `~/works/data/higgsfield/<YYYY-MM-DD>/<request_id>.<ext>`. repo 에는 넣지 않는다.

## 종료 코드

0 성공 · 1 실행 실패(HTTP 오류, failed·nsfw, 검사 실패) · 2 사용법 오류. HTTP 오류에는 X-Correlation-ID 가 같이 찍힌다. 지원 문의 때 request_id 와 함께 쓴다.
