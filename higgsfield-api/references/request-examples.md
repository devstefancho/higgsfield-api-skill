# 요청 예시: 좋은 요청과 아쉬운 요청

사용자에게 보여 주는 용도다. 요청이 막연하면 SKILL.md 의 안내와 함께 이 표에서 상황에 맞는 쌍 두세 개를 골라 보여 준다. 오른쪽 칸의 "왜"는 2026-09-29 시험 결과(prompts/)에서 나온 것이다.

## 요청 문장

| 아쉬운 요청 | 좋은 요청 | 왜 |
|---|---|---|
| "멋진 영상 하나 만들어줘" | "픽셀 기사 파티가 노을 숲길을 걸어가는 5초 영상, 16:9" | 무엇이, 어디서, 무엇을 하는지가 있어야 모델과 작업을 고를 수 있다 |
| "캐릭터 여러 명 나오는 애니 영상" | "픽셀 캐릭터 여섯 명 시트를 먼저 만들고, 그 시트로 행진 영상" | 캐릭터를 먼저 한 장에 확정해야 영상에서 모양이 유지된다 |
| "캐릭터들이 걸어가게 해줘" (정면 시트로) | "옆모습 시트로, 오른쪽 끝에서 들어와 왼쪽으로 화면을 가로질러 걷게" | 정면 시트를 주면 제자리걸음만 했다. 방향과 이동 거리를 말해야 실제로 걷는다 |
| "책상이 정리되는 모션 그래픽" | "캐릭터가 책상을 정리하는 장면" 또는 "픽셀 로봇이 포스트잇을 줄 세운다" | 추상 도형만 움직이는 전환은 동작은 맞았지만 볼 맛이 없었다. 주인공이 있어야 시선이 간다 |
| "타이틀에 '집중 타이머' 글자 넣어줘" | "글자 없이 만들고, 앱 이름은 편집에서 얹을게" | 생성 이미지 속 글자는 깨졌다(Soul 2). 글자는 편집에서 넣는다 |
| "시네마틱하고 다이내믹하게" | "카메라 고정" 또는 "카메라가 왼쪽에서 오른쪽으로 천천히 따라감, 3초 동안" | 빈 수식어는 결과를 흔든다. 카메라는 속도, 방향, 멈추는 지점까지 |
| "1080p 로 바로 API 로 뽑아줘" (처음부터) | "크레딧으로 480p 시험 먼저, 괜찮으면 API 720p" | API 는 최소 시도로 성공해야 한다. Seedance 2.5 API 영상은 최대 720p 다 |
| "이 영상 좀 더 길게" | "행진 v2 영상을 5초 이어서, 파티가 모닥불에 도착하는 장면으로" | 무엇을 이어 붙일지(파일), 뒤에 무엇이 일어날지를 말해야 extend 가 된다 |
| "좀 별로야, 다시" | "캐릭터가 너무 느려, 두 배 빠르게 걷고 마지막 1초도 멈추지 않게" | 무엇이 별로인지 한 가지를 말하면 그것만 고쳐서 한 번에 비교할 수 있다 |

## 에이전트가 쓰는 프롬프트 (영문, 참고)

| 아쉬운 프롬프트 | 좋은 프롬프트 | 왜 |
|---|---|---|
| `Six heroes walking in a forest, cinematic, dynamic` | `Total: 5s / 1 shot / 16:9. 16-bit pixel art side view. The six heroes from the reference image, all facing left, walk in single file from the right edge toward the left ... Static camera. Keep the exact character designs, no cuts, wordless.` | 샷 구조, 방향, 참조 유지, 카메라를 명시했다(pixel-party 11 v2) |
| `A knight with a sword in a pixel forest with the camera zooming and dollying in` | `... Slow dolly-in toward the knight over 3 seconds, stopping at a medium shot.` | dolly 와 zoom 을 섞지 않고, 속도와 멈추는 지점을 쓴다 |
| i2v 에 `A silver knight with a blue plume and a round shield stands in a forest at sunset...` (이미지 내용을 다시 설명) | i2v 에 `The knight raises the shield and takes two steps forward, cape swaying.` | 이미지로 영상은 장면을 이미지가 정한다. 프롬프트는 움직임만 쓴다 |
| `no blur, no text, no extra characters` | `tack sharp, wordless, only the six heroes from the reference` | 주요 영상 모델에는 negative prompt 가 없다. 긍정문으로 쓴다 |
