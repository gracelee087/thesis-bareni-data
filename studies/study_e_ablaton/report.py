"""Post-execution integrity checks and descriptive reporting. No model calls."""
import csv
import hashlib
import json
from collections import Counter,defaultdict
from datetime import datetime,timezone
from pathlib import Path
import sys
BASE=Path(__file__).resolve().parent;W=BASE/'private'
sys.path.insert(0,str(BASE/'tools'))
import pricing
from ledger import hash_json
from analysis import analyze
from run import verify_freeze

def read(p):return json.loads(p.read_text(encoding='utf-8'))
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')

def main():
    freeze_hash=verify_freeze()
    starts={p.name:read(p) for p in (W/'ledger/started').glob('*.json')}
    results={p.name:read(p) for p in (W/'ledger/results').glob('*.json')}
    issues=[];costs=defaultdict(float);latencies=defaultdict(float);unknown=[]
    prices=pricing.load_pricing()
    for key,start in starts.items():
        if hash_json(start['request'])!=start['request_sha256']:issues.append([key,'request_hash'])
        if start['request']['freeze_sha256']!=freeze_hash:issues.append([key,'freeze_hash'])
        row=results.get(key)
        if row is None or row.get('cost_usd') is None:
            unknown.append(key);continue
        c=start['request']['compiled']
        usage=pricing.normalize_usage(c['provider'],row['provider_response'])
        recomputed=pricing.cost_details(c['model'],usage,prices)
        if usage!=row['usage'] or recomputed!=row['cost_details'] or recomputed['total']!=row['cost_usd']:
            issues.append([key,'usage_cost_recomputation'])
        meta=row['metadata'];arm=meta['arm'];role=row['role']
        costs[(arm,role)]+=row['cost_usd'];latencies[(arm,role)]+=row['latency_ms']/1000
    if set(results)-set(starts):issues.append(['ledger','orphan_results'])
    schedule=read(W/'schedule.json');items=read(W/'inputs.json')['items']
    # Exact first-cycle provider request equality apart from Critic guidance.
    controlled=0
    for pair in schedule['pairs']:
        payloads=[]
        for arm in ('critic_on','critic_off'):
            candidates=sorted(k for k in starts if k.startswith(pair['pair_id']+'-'+arm+'-1-optimizer__'))
            if not candidates:break
            request=starts[candidates[0]]['request']['compiled']['request']
            request=json.loads(json.dumps(request))
            user=json.loads(request['input'][1]['content']);user['critic_repairs']=[]
            request['input'][1]['content']=user;payloads.append(request)
        if len(payloads)==2:
            controlled+=1
            if payloads[0]!=payloads[1]:issues.append([pair['pair_id'],'first_cycle_control_mismatch'])
    rows=[read(p) for p in sorted((W/'evaluations').glob('*.json'))]
    analysis=analyze(rows,[x['item_id'] for x in items])
    if (W/'analysis.json').exists() and analysis!=read(W/'analysis.json'):issues.append(['analysis','recomputation_mismatch'])
    summary=dict(study_id='STUDY-E-ABLATON',at=datetime.now(timezone.utc).isoformat(),
        freeze_sha256=freeze_hash,planned_pairs=375,controlled_pairs_verified=controlled,
        physical_attempts=len(starts),attempt_statuses=dict(Counter(r['status'] for r in results.values())),
        unknown_cost_attempts=unknown,known_usage_cost_usd=sum(r['cost_usd'] or 0 for r in results.values()),
        budget_charge_usd=sum(results[k]['cost_usd'] if k in results and results[k].get('cost_usd') is not None else s['reserved_usd'] for k,s in starts.items()),
        provider_invoice_reconciled=False,issues=issues,analysis=analysis,arms={})
    for arm in ('critic_on','critic_off'):
        subset=[r for r in rows if r['arm']==arm and r['status']=='complete']
        histories=[read(p)['arms'][arm]['history'] for p in (W/'pairs').glob('*.json')]
        production=sum(v for (a,r),v in costs.items() if a==arm and r!='evaluator')+costs[('shared','gate')]/2
        summary['arms'][arm]=dict(valid_evaluations=len(subset),
            mean_total=sum(r['rating']['total_score'] for r in subset)/len(subset) if subset else None,
            low_quality=sum(r['rating']['low_quality'] for r in subset),
            production_cost_usd_including_half_shared_gate=production,evaluation_cost_usd=costs[(arm,'evaluator')],
            mean_refinements=sum(len(h) for h in histories)/len(histories) if histories else None)
    summary['local_integrity_passed']=not issues and not unknown and analysis['status']=='complete' and controlled==375
    succeeded={k.rsplit('__a',1)[0] for k,r in results.items() if r['status']=='success'}
    attempted={k.rsplit('__a',1)[0] for k in starts}
    summary['unrecovered_logical_calls']=sorted(attempted-succeeded)
    summary['all_logical_calls_recovered']=not summary['unrecovered_logical_calls']
    summary['input_result_analysis_integrity_passed']=not issues and analysis['status']=='complete' and controlled==375
    summary['complete_usage_available']=not unknown
    summary['unknown_usage_reservation_usd']=sum(starts[k]['reserved_usd'] for k in unknown)
    out=BASE/'reports';out.mkdir(exist_ok=True)
    save(out/'RESULTS.json',summary)
    with (out/'evaluations.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=['item_id','repeat','arm','total','low_quality']);writer.writeheader()
        writer.writerows(dict(item_id=r['item_id'],repeat=r['repeat'],arm=r['arm'],total=r['rating']['total_score'],low_quality=r['rating']['low_quality']) for r in rows)
    with (out/'costs.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.writer(f);writer.writerow(['arm','role','known_cost_usd','summed_call_seconds'])
        for key,cost in sorted(costs.items()):writer.writerow([*key,f'{cost:.8f}',latencies[key]])
    a=summary['arms']['critic_on'];b=summary['arms']['critic_off']
    text='# STUDY-E-ABLATON 결과\n\n'
    text+='STUDY-E-1의 혼합 초기 입력 125개를 재사용한 별도 후속 비교다. 과제당 3반복이며 두 Optimizer 모두 Gate 정보를 직접 받는다. Critic 지시의 추가 효과를 검토하며, 기존 최종실험의 H1–H3 결과에 합산하지 않는다.\n\n'
    text+=f"완료 평가: {len(rows)}/750. 물리적 API 시도: {len(starts)}회. 사용량으로 계산한 알려진 비용: USD{summary['known_usage_cost_usd']:.8f}. 제공자 청구서 대조는 미완료다.\n\n"
    if analysis['status']=='complete':
        text+='| 항목 | Critic 사용 | Critic 미사용 |\n|---|---:|---:|\n'
        text+=f"| 평균 총점(4–20) | {a['mean_total']:.4f} | {b['mean_total']:.4f} |\n"
        text+=f"| 최종 저품질 | {a['low_quality']}/375 | {b['low_quality']}/375 |\n"
        text+=f"| 생산 비용(공유 Gate 반액 포함) | USD{a['production_cost_usd_including_half_shared_gate']:.6f} | USD{b['production_cost_usd_including_half_shared_gate']:.6f} |\n\n"
        diff=analysis['mean_difference_on_minus_off'];p=analysis['paired_randomization']['p_two_sided'];lo,hi=analysis['reference_t_interval_95']
        text+=f'과제별 3반복 평균 차이(Critic 사용−미사용)의 전체 평균은 {diff:.4f}점이다. 과제 단위 부호 반전 검정의 양측 p={p:.6g}, 95% t 참고구간은 [{lo:.4f}, {hi:.4f}]이다.\n\n'
        text+='고정된 혼합 입력과 이번 통제 구조에 한정된 결과다. 750개의 독립 주제로 해석하지 않으며 자연 조건이나 전체 멀티에이전트 구조로 일반화하지 않는다. 비유의 결과는 동등성이나 효과 부재의 증명이 아니다.\n'
    else:text+='예정된 평가에 결측이 있으므로 전체 코호트의 주 검정을 확정하지 않았다.\n'
    text+=f"\n입력·결과·분석 무결성 검사 통과: {summary['input_result_analysis_integrity_passed']}. 모든 논리 호출 복구: {summary['all_logical_calls_recovered']}. 통신 실패 {len(unknown)}시도의 사용량은 미확인으로 보존했으며 예약액 USD{summary['unknown_usage_reservation_usd']:.8f}를 한도 계산에 포함했다. 미확인 비용을 0으로 가정하지 않는다. 전체 Langfuse 대조는 별도 cloud_audit receipt를 확인한다.\n"
    (out/'RESULTS_KO.md').write_text(text,encoding='utf-8')
    print(json.dumps({k:summary[k] for k in ['local_integrity_passed','physical_attempts','known_usage_cost_usd','issues']}))

if __name__=='__main__':main()
