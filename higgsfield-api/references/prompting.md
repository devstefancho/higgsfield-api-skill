# 프롬프트 작성 규칙

2026-09-29 조사 기준. 출처 표기: [공식] Higgsfield 문서·블로그, [제작사] 모델 제작사 가이드, [참고] 그 외(검증 안 함). 모델별 필드와 한도는 `hfapi.py show <엔드포인트>` 가 정본이다.

## 공통

- **이미지 먼저, 영상 프롬프트에는 움직임만.** image-to-video 는 입력 이미지가 구도와 화면비를 정한다. 프롬프트에는 이미지 속 대상이 어떻게 움직이는지와 카메라만 쓴다. 이미지와 다른 내용을 쓰면 컷이나 전환이 생긴다. [제작사] kling.ai/quickstart/image-to-video-guide, [공식] Seedance 가이드
- **카메라는 속도, 경로, 멈추는 지점까지.** 생성마다 결과가 흔들리는 것은 말로 정하지 않은 부분 때문이다. 예: "Slow camera pan left across a coastal town at dusk, tripod fixed, horizon level." [공식] higgsfield.ai/blog/ai-video-camera-control
- **dolly 와 zoom 을 한 샷에 섞지 않는다.** dolly 는 카메라가 움직이고 zoom 은 렌즈만 바뀐다. pan(제자리 회전), orbit(피사체 중심 원), tracking(피사체 옆 동행)도 구분해 쓴다. [공식] 같은 글
- **부정문 대신 긍정문.** Kling 3.0, Seedance 2.x, MiniMax H3, Wan 3.0, Cinema Studio 4.0 에는 negative_prompt 가 없다. "no blur" 대신 "tack sharp", "no people" 대신 "empty street". negative_prompt 가 있는 모델은 Kling 2.5 Turbo, PixVerse V6, Wan 2.6·2.7.
- **빈 수식어를 줄인다.** "cinematic", "dynamic" 보다 카메라 동사, 렌즈, 조명, 속도처럼 화면에서 확인되는 말을 쓴다. [참고]
- **먼저 720p 짧은 길이로 움직임을 시험하고** 고해상도는 마지막에. [공식] 카메라 제어 글

## 모델별

| 모델 | 쓰는 법 | 한도 |
|---|---|---|
| Seedance 2.x | 맨 위에 샷 구조 한 줄("Total: 15s / 3 shots / 16:9"), 그다음 조명·필름·색, 이어서 샷 번호별 동작. 시간 구간(0-3s)과 `[VFX: ...]` 표기 가능. POV 고정이면 "No cuts, no zoom". i2v 는 prompt 생략 가능. [공식] higgsfield.ai/blog/seedance-prompting-guide | enhance 필드 없음 |
| Kling 3.0 | 쉬운 단어, 짧은 문장. i2v 는 "Subject + Movement". 멀티샷은 multi_shots=true + multi_prompt(최대 6샷) | 2,500자(Turbo t2v 3,072), 샷당 512자 |
| MiniMax H3 | 긴 서술 가능 | 앞 7,000자만 사용, 2K 고정 |
| Hailuo 2.3 | 싼 모션 시험용 | `prompt_optimizer` 기본 true(끄면 문장 그대로) |
| Cinema Studio 4.0 | 카메라·렌즈·조명·장르·시대·속도·색을 열거값 필드로 고정할 수 있다. 필드를 비우면 자동 선택. 참조는 프롬프트 안 `<<<image_1>>>` | 프롬프트 1자 이상 |
| Soul 2 (이미지) | 구도 시험용, 장당 약 $0.003 | `enhance_prompt` 기본 false, 짧은 프롬프트는 자동 강화 |

## Cinema Studio 4.0 열거값 (어휘 목록으로도 쓴다)

- camera_movement: dolly-in, dolly-out, dolly-zoom, crush-zoom, slow-zoom-in, slow-zoom-out, pan-left, pan-right, tilt-up, tilt-down, arc-left, arc-right, truck-left, truck-right, slider-left, slider-right, side-tracking, tracking, crane-up, crane-down, pedestal-up, pedestal-down, drone-orbit, aerial-pullback, helicopter-shot, handheld, pov, snorricam, robot-arm, rack-focus, bullet-time, whip-pan, static-shot
- camera_lens: clean-sharp, anamorphic, vintage-anamorphic, warm-vintage, halation-vintage
- camera_model: modern, 35mm-film, 8mm-film, dv-camcorder
- camera_aperture: f14-wide-open, f4-moderate, f11-deep-focus
- light: silhouette, practicals, window, overhead-fall, contre-jour, soft-cross
- genre: epic, drama, noir, comedy, horror, action
- era: 1960s, 1980s, 1990s, 2000s, 2020s
- pacing: chaotic, dynamic, calm, single-shot
- color_palette 50종은 `hfapi.py show cinema-studio` 계열 문서에서 확인한다.

## 영상 방향 메모 (2026-09-29 사용자)

실패 확률이 낮고 시선을 끄는 방향을 우선한다. 후보는 모션 그래픽과 일본풍 애니메이션 연출이다. 시험하면서 잘 된 프롬프트와 모델 조합, 안 된 것을 아래에 추가한다.

- 2026-09-29 Soul 2 (`text2image_soul_v2`, 16:9, 1.5k, 0.12 크레딧): "Flat motion graphics style title card, bold geometric shapes, lime green and black, clean vector look" 는 타이틀 카드가 아니라 인쇄물 두 장을 찍은 목업 사진이 나왔고 글자가 깨졌다. Soul 2 는 기본 스타일이 "General"(사진풍)로 붙는다. 모션 그래픽 소재는 Recraft V4.1 이나 Grok Image 2.0 으로 시험한다.
- 2026-09-29 픽셀 캐릭터 시트 → Seedance 2.5 참조 영상. 시트는 Grok Image 2.0 이 잘 만든다(여섯 캐릭터 한 줄, 2 크레딧). 정면 시트를 참조로 주면 캐릭터가 정면을 본 채 제자리걸음을 하고 배경만 흐른다. 원하는 동작 방향의 옆모습 시트를 참조로 주고 "enter from the right edge ... visibly travel across the frame" 처럼 이동을 명시하면 화면을 가로질러 걷는다. Grok 에 "facing right" 를 요청했는데 왼쪽을 보고 나왔으니 시트의 방향을 확인하고 영상 프롬프트를 거기에 맞춘다(prompts/pixel-party/).
- 2026-09-29 모션 그래픽 전환(Seedance 2.5 시작·끝 프레임)은 동작은 맞게 나오지만 사용자 평가가 "너무 별로"였다. 추상 정리 애니메이션보다 캐릭터가 있는 장면이 낫다(prompts/focus-timer/).
