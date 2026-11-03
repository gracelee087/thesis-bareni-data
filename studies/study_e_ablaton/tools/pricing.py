"""Verified prices for the final experiment only; no network or model clients."""
from __future__ import annotations
import copy
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
import math
from pathlib import Path

PATH = Path(__file__).resolve().parents[1] / 'private/pricing.json'
RATE_KEYS = ('input', 'cached_input', 'cache_write_input', 'output')


class PricingError(ValueError):
    pass


def load_pricing(path=PATH):
    value = json.loads(Path(path).read_text(encoding='utf-8'))
    if value['currency'] != 'USD' or value['unit'] != 'per_1m_tokens':
        raise PricingError('Unsupported pricing units')
    for rate in value['models'].values():
        for key in RATE_KEYS:
            if type(rate[key]) not in (int, float) or not math.isfinite(rate[key]) or rate[key] < 0:
                raise PricingError('Invalid model rate')
    return value


def pricing_hash():
    return hashlib.sha256(PATH.read_bytes()).hexdigest()


def candidate(role, config):
    model = config['roles'][role]
    return dict(model=model, **{k: config['models'][model][k] for k in ('provider', *RATE_KEYS)})


def apply_to_plan(plan, config):
    result = copy.deepcopy(plan)
    for role, template in result['templates'].items():
        rate = candidate(role, config)
        if template['candidate']['model'] != rate['model']:
            raise PricingError('Pricing must not change a selected model')
        template['candidate'].update(rate)
    result['pricing_sha256'] = pricing_hash()
    result['pricing_verified_date'] = config['verified_date']
    result['pricing_file'] = 'pricing.json'
    return result


def validate_plan(plan, config):
    if plan.get('pricing_sha256') != pricing_hash():
        raise PricingError('Plan/pricing hash mismatch; update before freeze')
    for role, template in plan['templates'].items():
        expected = candidate(role, config)
        if any(template['candidate'].get(k) != v for k, v in expected.items()):
            raise PricingError('Plan/model price mismatch: ' + role)


def validate_date(config, day=None):
    day = day or datetime.now(timezone.utc).date().isoformat()
    if day < config['valid_from']:
        raise PricingError('Pricing date is before verified validity')
    if any(day > rate.get('valid_through', '9999-12-31') for rate in config['models'].values()):
        raise PricingError('Verified introductory pricing has expired')


def count(value):
    if type(value) is not int or value < 0:
        raise PricingError('Usage must be a nonnegative integer')
    return value


def normalize_usage(provider, raw):
    if provider == 'google':
        u = raw['usage_metadata']
        result = {k: count(u.get(k) or 0) for k in ('prompt_token_count', 'cached_content_token_count',
            'candidates_token_count', 'thoughts_token_count', 'total_token_count')}
        if result['total_token_count'] != result['prompt_token_count'] + result['candidates_token_count'] + result['thoughts_token_count']:
            raise PricingError('Google usage totals disagree')
        # Missing required counts are never silently priced as free.
        if 'prompt_token_count' not in u or not any(k in u for k in ('candidates_token_count', 'thoughts_token_count')):
            raise PricingError('Missing Google usage')
    else:
        u = raw['usage']
        if provider == 'openai':
            details = u.get('input_tokens_details') or {}
            if count(details.get('cache_write_tokens') or 0):
                raise PricingError('Unexpected billed OpenAI cache writes for selected models')
            result = dict(input_tokens=count(u['input_tokens']),
                cached_input_tokens=count(details.get('cached_tokens') or 0), cache_write_input_tokens=0,
                output_tokens=count(u['output_tokens']),
                reasoning_tokens=count((u.get('output_tokens_details') or {}).get('reasoning_tokens') or 0))
        elif provider == 'anthropic':
            cache = count(u.get('cache_read_input_tokens') or 0)
            write = count(u.get('cache_creation_input_tokens') or 0)
            hour = count((u.get('cache_creation') or {}).get('ephemeral_1h_input_tokens') or 0)
            if hour > write:
                raise PricingError('Invalid Anthropic cache duration counts')
            result = dict(input_tokens=count(u['input_tokens']) + cache + write,
                cached_input_tokens=cache, cache_write_input_tokens=write,
                output_tokens=count(u['output_tokens']), reasoning_tokens=None)
            if hour:
                result['cache_write_1h_input_tokens'] = hour
        else:
            raise PricingError('Unsupported provider')
    usage_details(result)
    return result


def usage_details(usage):
    if not usage:
        return None
    if 'prompt_token_count' in usage:
        inp = count(usage['prompt_token_count']); cache = count(usage.get('cached_content_token_count') or 0)
        visible = count(usage.get('candidates_token_count') or 0); reasoning = count(usage.get('thoughts_token_count') or 0)
        if cache > inp:
            raise PricingError('Cache exceeds input')
        result = dict(input=inp-cache, cache_read_input_tokens=cache,
                      output=visible, reasoning_output_tokens=reasoning)
    else:
        inp = count(usage['input_tokens']); cache = count(usage.get('cached_input_tokens') or 0)
        write = count(usage.get('cache_write_input_tokens') or 0)
        hour = count(usage.get('cache_write_1h_input_tokens') or 0)
        output = count(usage['output_tokens']); reasoning = count(usage.get('reasoning_tokens') or 0)
        if cache+write > inp or reasoning > output or hour > write:
            raise PricingError('Usage subsets exceed totals')
        result = dict(input=inp-cache-write, cache_read_input_tokens=cache,
                      cache_creation_input_tokens=write-hour, output=output-reasoning,
                      reasoning_output_tokens=reasoning)
        if hour:
            result['cache_creation_1h_input_tokens'] = hour
    result['total'] = sum(result.values())
    return result


def effective_rates(model, input_tokens, config):
    base = config['models'][model]
    long = base.get('long_context')
    return {**base, **long} if long and input_tokens > long['input_tokens_gt'] else base


def unit_prices(rate):
    prices = dict(input=rate['input'], cache_read_input_tokens=rate['cached_input'],
        cache_creation_input_tokens=rate['cache_write_input'], output=rate['output'],
        reasoning_output_tokens=rate['output'])
    if 'cache_write_1h' in rate:
        prices['cache_creation_1h_input_tokens'] = rate['cache_write_1h']
    return prices


def cost_details(model, usage, config):
    bins = usage_details(usage)
    if bins is None:
        raise PricingError('Cannot price missing usage')
    inp = usage.get('prompt_token_count', usage.get('input_tokens'))
    rate = effective_rates(model, inp, config)
    prices = unit_prices(rate)
    values = {key: Decimal(tokens) * Decimal(str(prices[key])) / Decimal(1_000_000)
              for key, tokens in bins.items() if key != 'total'}
    result = {key: float(value) for key, value in values.items()}
    result['total'] = float(sum(values.values()).quantize(Decimal('0.00000001')))
    return result


def reserve(model, request, config):
    # Conservative reservation; not a provider-certified billing upper bound.
    estimated_input = len(json.dumps(request, ensure_ascii=False).encode('utf-8')) + 4096
    max_output = request.get('max_tokens', request.get('max_output_tokens'))
    if max_output is None:
        max_output = request['config']['max_output_tokens']
    rate = effective_rates(model, estimated_input, config)
    return (estimated_input * max(rate['input'], rate['cache_write_input']) + max_output * rate['output']) / 1e6


def langfuse_model(model, config):
    rate = config['models'][model]
    prices = lambda r: {k: v / 1e6 for k, v in unit_prices(r).items()}
    tiers = [dict(name='Standard 2026-09-07', isDefault=True, priority=0, conditions=[], prices=prices(rate))]
    if 'long_context' in rate:
        tiers.append(dict(name='Input above 272K', isDefault=False, priority=1,
            conditions=[dict(usageDetailPattern='^(input|cache_read_input_tokens|cache_creation_input_tokens)$',
                             operator='gt', value=rate['long_context']['input_tokens_gt'], caseSensitive=True)],
            prices=prices({**rate, **rate['long_context']})))
    return dict(modelName=model, matchPattern=rate['match_pattern'], unit='TOKENS',
                startDate='2026-09-06T22:00:00Z', pricingTiers=tiers)
