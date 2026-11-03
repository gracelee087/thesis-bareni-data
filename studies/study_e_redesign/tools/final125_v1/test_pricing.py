"""Cost regression fixtures with hand-calculated expected dollar amounts."""
import copy
import math
import pytest
import pricing as p
from test_telemetry import make, attempt
from test_final import workspace, no_network
from types import SimpleNamespace
import json
import run as runner


@pytest.mark.parametrize('model,expected',[
    ('claude-haiku-4-5-20251001',.007),('claude-opus-5',.035),
    ('gpt-5.4-mini',.006),('gpt-5.4',.02),('gemini-3.8-flash',.00525),
])
def test_known_2000_input_1000_output(model,expected):
    result=p.cost_details(model,dict(input_tokens=2000,output_tokens=1000),p.load_pricing())
    assert result['total']==expected


def test_google_cached_input_and_thoughts_are_not_double_counted():
    raw={'usage_metadata':dict(prompt_token_count=1000,cached_content_token_count=200,
        candidates_token_count=100,thoughts_token_count=300,total_token_count=1400)}
    usage=p.normalize_usage('google',raw)
    result=p.cost_details('gemini-3.8-flash',usage,p.load_pricing())
    assert result['total']==.002115  # 800*.75 + 200*.075 + (100+300)*3.75, /1M
    assert result['reasoning_output_tokens']==.001125
    assert p.usage_details(usage)['total']==1400


def test_anthropic_cache_durations_use_different_rates():
    raw={'usage':dict(input_tokens=1000,cache_read_input_tokens=200,
        cache_creation_input_tokens=300,cache_creation={'ephemeral_1h_input_tokens':100},output_tokens=100)}
    usage=p.normalize_usage('anthropic',raw)
    result=p.cost_details('claude-opus-5',usage,p.load_pricing())
    assert result['total']==.00985  # .005 + .0001 + .00125 + .001 + .0025
    assert p.usage_details(usage)['cache_creation_input_tokens']==200
    assert p.usage_details(usage)['cache_creation_1h_input_tokens']==100


def test_gpt54_long_context_boundary_and_zero_extra_write_surcharge():
    cfg=p.load_pricing()
    assert p.effective_rates('gpt-5.4',272000,cfg)['input']==2.5
    assert p.effective_rates('gpt-5.4',272001,cfg)['input']==5
    details=p.cost_details('gpt-5.4',dict(input_tokens=300000,cached_input_tokens=50000,
        output_tokens=1000,reasoning_tokens=400),cfg)
    assert details['total']==1.2975
    assert p.candidate('gate',cfg)['cache_write_input']==p.candidate('memory',cfg)['cache_write_input']==2.5
    request=dict(model='gpt-5.4',input='fixture',max_output_tokens=1000)
    assert p.reserve('gpt-5.4',request,cfg)==p.reserve(p.candidate('memory',cfg)['model'],request,cfg)


def test_missing_invalid_usage_and_expired_rate_fail_closed():
    with pytest.raises(KeyError):p.normalize_usage('openai',{'usage':{'input_tokens':10}})
    with pytest.raises(p.PricingError):p.normalize_usage('google',{'usage_metadata':{}})
    with pytest.raises(p.PricingError):p.cost_details('gpt-5.4',dict(input_tokens=10,cached_input_tokens=20,output_tokens=2),p.load_pricing())
    with pytest.raises(p.PricingError):p.validate_date(p.load_pricing(),'2027-01-01')
    with pytest.raises(p.PricingError):p.validate_plan({},p.load_pricing())


def test_telemetry_exports_exact_breakdown_and_safe_error_fields():
    tel,client=make()
    usage=dict(input_tokens=1000,cached_input_tokens=200,output_tokens=400,reasoning_tokens=300)
    details=p.cost_details('gpt-5.4-mini',usage,p.load_pricing())
    with tel.task('pricing-test'):
        with attempt(tel) as handle:
            handle.finish(dict(status='validation_failure',usage=usage,cost_usd=details['total'],
                cost_details=details,error_kind='ValueError',error_code='invalid_json',http_status=200,
                validation_detail='Missing required body field',pricing_sha256=p.pricing_hash()))
    update=client.calls[1][1].updates[0]
    assert update['cost_details']==details and update['level']=='ERROR'
    assert update['metadata']['error_code']=='invalid_json'
    assert update['metadata']['validation_detail']=='Missing required body field'
    assert math.isclose(sum(v for k,v in details.items() if k!='total'),details['total'],abs_tol=1e-8)


def test_price_mismatch_is_rejected_and_per_token_cloud_prices_match():
    cfg=p.load_pricing()
    plan={'templates':{'gate':{'candidate':p.candidate('gate',cfg)}}}
    plan=p.apply_to_plan(plan,cfg)
    bad=copy.deepcopy(plan);bad['templates']['gate']['candidate']['output']=1
    with pytest.raises(p.PricingError):p.validate_plan(bad,cfg)
    for model,rate in cfg['models'].items():
        cloud=p.langfuse_model(model,cfg)
        assert cloud['pricingTiers'][0]['prices']['input']==rate['input']/1e6
        assert cloud['pricingTiers'][0]['prices']['reasoning_output_tokens']==rate['output']/1e6


def test_pricing_failure_still_exports_error_without_inferred_cost():
    tel,client=make()
    with tel.task('pricing-failure'):
        with attempt(tel) as handle:
            handle.finish(dict(status='pricing_failure',usage={'input_tokens':10},
                cost_usd=None,pricing_error_kind='PricingError'))
    update=client.calls[1][1].updates[0]
    assert update['level']=='ERROR'
    assert update['metadata']['local_usage']=={'input_tokens':10}
    assert 'usage_details' not in update and 'cost_details' not in update


@pytest.mark.parametrize('case', ['success', 'invalid_json', 'missing_usage', 'unexpected_tier'])
def test_real_runner_prices_failed_responses_and_enforces_service_tier(workspace, case):
    plan,path=workspace
    task=plan['tasks'][0]
    pl=dict(steps=[dict(instruction='Suggest a manual check.')])
    research=runner.p.research_input(task,pl,[])
    payload=runner.p.production(dict(task,research=research),'writer',plan=pl,ledger={'ledger':[]})
    out=dict(item_id=payload['item_id'],title='Saved response',body='A'*1300)
    raw=dict(model='gpt-5.4-mini',status='completed',service_tier='default',
        usage=dict(input_tokens=1000,input_tokens_details={'cached_tokens':200},
                   output_tokens=400,output_tokens_details={'reasoning_tokens':300}))
    if case=='missing_usage':raw.pop('usage')
    if case=='unexpected_tier':raw['service_tier']='priority'
    requests=[]
    def create(**kw):
        requests.append(kw)
        return SimpleNamespace(model_dump=lambda **_:raw,
            output_text='invalid json' if case=='invalid_json' else json.dumps(out))
    tel,client=make()
    r=runner.Runner(dict(plan,minimum_provider_interval_seconds=0),
        {'openai':SimpleNamespace(responses=SimpleNamespace(create=create))},tel)
    r.context.set(dict(task_id=task['task_id'],cohort='natural',batch_id=1))
    with tel.task(task['task_id']):
        row=r.once('pricing-fixture','writer',payload,())
    assert len(requests)==1 and requests[0]['service_tier']=='default'
    saved=runner.read(path/'results/pricing-fixture.json')
    update=client.calls[1][1].updates[0]
    if case in ('success','invalid_json'):
        assert saved['cost_usd']==.002415
        assert update['cost_details']==saved['cost_details']
        assert saved['pricing_sha256']==p.pricing_hash()
        assert row['status']==('success' if case=='success' else 'validation_failure')
    else:
        assert row['status']=='pricing_failure' and saved['cost_usd'] is None
        assert saved['unknown_cost_reservation_usd']>0
        assert 'cost_details' not in update and 'usage_details' not in update
    assert update['level']==('DEFAULT' if case=='success' else 'ERROR')
