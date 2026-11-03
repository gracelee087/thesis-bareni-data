# 가격 대조 후 구현 반영 — 2026-09-07

같은 폴더의 README.md, pricing_audit.json, manifest.json은 08:29 UTC 대조 당시의 기록으로 보존한다. 그 기록의 미해결 Gate 예약값과 service tier 확인 상태는 아래 후속 구현으로 갱신됐다. 원본 manifest의 대상 파일은 수정하지 않았다.

- 단일 설정: `../../pricing.json`. 입력·캐시·출력의 다섯 공식 기본 단가는 그대로 유지했다. Gate의 `cache_write_input`만3.125에서2.5로 수정해 Curator와 일치시켰다. OpenAI에서 별도 쓰기 할증을 청구한다는 뜻이 아니며 예약 호환 필드다.
- 표준 요청: OpenAI `service_tier=default`를 명시하고 응답의 다른 tier는 비용 미확인으로 중단한다. 가격 파일·계획 해시가 다르거나 Gemini 도입 요율이 만료되면 실행을 중단한다.
- 관측비: 성공·검증 실패의 실제 응답 사용량에 동일 가격 계산을 적용한다. 캐시 읽기/쓰기와 가시 출력/thinking을 중복 없이 분리한다. Anthropic5분/1시간 캐시 쓰기를 구분한다. GPT-5.4는 총 입력이272,000토큰을 **초과**할 때 장문 요율을 적용한다(정확히272,000은 기본 구간). 원본 README의 '272K 미만' 표현은 이 정확한 경계로 정정한다.
- Langfuse: 새 프로젝트의 다섯 custom model을 토큰당 USD로 등록·재조회했다. generation에는 로컬 비용 세부항목을 직접 전송하며 Cloud 자동 추정에 의존하지 않는다. 검증 영수증은 `../../langfuse_pricing_verification_2026-09-07.json`이다.
- 실제 Cloud 검증: 합성 generation7개에 대해 사용량·항목별 비용·ERROR·검증 설명을 재조회했다. `pricing-verification` 환경과 `synthetic=true`, `exclude_from_experiment=true`로 표시했다. 모델 공급사 호출0건, 실제 공급사 청구0달러다. 합성 비용은 실험 지출이 아니다.
- 오류 기록: API/응답 검증 실패는 ERROR로 남긴다. 비용 미확인 토큰은 metadata에만 남겨 잘못된 Cloud 비용 추정을 방지한다. 내용 결함은 Gate 결과에 남기며 전송 실패는 로컬 telemetry_events에 기록한다.

수정 전 실행 코드·계획·프로토콜은 `../../pricing_changes/20260907T094222/before/`에 보존했다. 최종 오프라인 검사는 `../../offline_test_receipt.json`이 가리키는 시각별 영수증으로 확인한다. 실험 과제·순서·결함 배정·모델 선택·49.99달러 상한은 유지했다.

공식 공개 단가를 검증한 것이며 실제 청구서·계정 크레딧·세금 대사를 수행한 것은 아니다. 공식 페이지 스크린샷, 두 조건 예상 총비용 산정, 최종 동결 및 AsPredicted 등록은 아직 미완료다.
