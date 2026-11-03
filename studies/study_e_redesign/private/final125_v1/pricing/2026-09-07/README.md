# Study E 모델 공식 단가 대조 — 2026-09-07

공식 표준 API 가격과 현재 실행 설정의 **입력·캐시 읽기·출력 단가가 모두 일치**한다. 단위는 USD / 100만 토큰이다. 구독료 또는 공급사 Batch 할인 가격이 아니다.

| 공급사 | 모델 | 역할 | 입력 | 캐시 읽기 | 출력 |
|---|---|---|---:|---:|---:|
| Anthropic | claude-haiku-4-5-20251001 | Planner | 1.00 | 0.10 | 5.00 |
| Anthropic | claude-opus-5 | Researcher | 5.00 | 0.50 | 25.00 |
| OpenAI | gpt-5.4-mini | Writer / Critic / Optimizer | 0.75 | 0.075 | 4.50 |
| OpenAI | gpt-5.4 | Gate / Lesson Curator | 2.50 | 0.25 | 15.00 |
| Google | gemini-3.8-flash | 독립 평가자 | 0.75 | 0.075 | 3.75 |

공식 출처: [Anthropic 모델 가격](https://platform.claude.com/docs/en/about-claude/pricing), [OpenAI API 가격](https://developers.openai.com/api/docs/pricing), [Google Gemini 3.8 Flash 가격](https://ai.google.dev/gemini-api/docs/pricing#gemini-3.8-flash).

## 조건과 캐시

- Anthropic의 5분/1시간 캐시 쓰기는 Haiku 1.25/2.00, Opus 6.25/10.00이다. 현재 요청에는 cache_control이 없으며 캐시 읽기/생성 토큰은 응답 사용량에 따라 계산한다. Opus의 US 전용 추론은 할증 조건이지만 현재 inference_geo 지정은 없다.
- GPT-5.4와 Mini에는 별도 캐시 쓰기 할증이 없다. 1.25배 쓰기 요율은 GPT-5.6 이후에 적용된다. [공식 캐시 설명](https://developers.openai.com/api/docs/guides/prompt-caching)
- GPT-5.4 표의 기본 구간은 272K 미만 컨텍스트 기준이며, 장문 구간은 입력 5.00/캐시 0.50/출력 22.50이다. 지역 처리 및 Fast 등 다른 서비스 조건은 별도 확인 대상이다.
- Gemini 가격은 2026-12-31까지의 도입 요율이다. 2027-01-01부터 입력 1.50/캐시 0.15/출력 7.50 예정. 출력에는 thinking 토큰이 포함되며 코드도 이를 합산한다. 명시적 캐시 저장은 현재 100만 토큰·시간당 0.50이지만 현 평가 요청은 저장 리소스를 생성하지 않는다.

## 코드 대조에서 남은 한 가지

`private/final125_v1/execution_plan.json`의 같은 GPT-5.4에 대해 Gate의 `cache_write_input`은 3.125, Curator는 2.5다. 전자는 GPT-5.4의 공식 추가 캐시 쓰기 요율이 아니다.

`tools/gate_v5/run_gate_selection.py`는 OpenAI 실측 계산에서 write=0으로 두므로 관측 비용에는 이 값이 직접 반영되지 않는다. 그러나 reserve()가 max(input, cache_write_input)을 사용하므로 Gate의 **입력 예약 부분**은 일반 입력 기준보다 25% 높다. 전체 요청비 또는 청구액이 25% 높다는 뜻은 아니다. 동결 전에 예약 근거를 정리해야 한다. 이번 가격 확인에서 코드·실행 설정은 변경하지 않았다.

## 확인 범위와 보존 상태

모델 목록·현재 적용 단가·SDK 요청 경로·비용 및 예약 함수를 대조했다. 로컬 SDK의 OpenAI/Anthropic 목적지는 각각 api.openai.com/api.anthropic.com이며 별도 gateway 설정은 확인되지 않았다. 일반 동기 호출이고 공급사 Batch API를 사용하지 않는다. 연구의 네 배치를 공급사 Batch 할인으로 계산하지 않는다.

이 기록은 공식 공개 단가 검증이며 실제 청구서 대사는 아니다. 계정 할인·크레딧·세금, Google 결제 등급, 공급사 콘솔의 기본 service tier는 이번에 독립 검증하지 않았다. 유료 모델 호출은 0건이다.

공식 페이지 캡처는 `screenshots/`에 보존했다. 보존된 125건 파일럿의 실제 사용량 장부를 현재 두 조건의 범위에 맞춰 확장한 계획 추정치는 자연 $19.3603 + 혼합 $11.0603 = **$30.4206**(혼합의 사용량 미확인 예약 $3.9144 포함)이다. 따라서 $49.99 상한 안에 $19.5694의 계획 여유가 남는다. 이는 공급사 청구서나 보장된 상한이 아니며, 실제 출력량·실패·재시도에 따라 달라진다. 계산은 `expected_cost_estimate.json`에 보존했다.

`pricing_audit.json`에는 기계적으로 대조한 역할별 수치, 공식 URL, 확인 시각, 코드 해시 및 미완료 항목이 있다. `manifest.json`은 이 가격 대조 파일들의 무결성 색인이며 실험 조건을 동결하는 manifest가 아니다.

대조 완료(UTC): 2026-09-07T08:29:42.535229+00:00

대조 완료(Europe/Berlin): 2026-09-07T10:29:42.535229+02:00
