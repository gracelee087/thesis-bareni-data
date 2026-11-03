"""Frozen deterministic fault operators. No judge scores, model calls or retuning."""
import difflib
import hashlib
import random
import re

TYPES = ['fabricated_evidence', 'wrong_audience', 'no_actionable_step', 'incoherent']


def mutate(original, defect_type, variant, topic):
    body = original['body']
    if defect_type == 'fabricated_evidence':
        claim = (f'Bareni has already deployed this approach for {27 + variant * 3} paying customers '
                 f'and verified a {43 + variant * 2}% reduction in their weekly administrative work.')
        # Cap deterministically, without inspecting any quality result.
        changed = body[:2000-len(claim)-2].rstrip() + '\n\n' + claim
    elif defect_type == 'wrong_audience':
        opening = (f'This guidance is for the executive board of a {5000 + variant * 500}-employee multinational. '
                   'Its central transformation office, regional directors and dedicated governance committee own this programme. ')
        changed = re.sub(r'\b(?:small[- ]business owner|small business owner|solo entrepreneur|owner-operator)\b',
                         'enterprise transformation director', body, flags=re.I)
        changed = opening + changed[:2000-len(opening)]
    elif defect_type == 'no_actionable_step':
        # Deliberately broad semantic corruption: replace actionable passages with reflection.
        blocks = [
            f'The topic of {topic} can matter to a small-business owner without having a settled meaning. '
            'Its importance may feel apparent while the relationship to everyday work remains uncertain.',
            'A situation can seem clear from one perspective and unsettled from another. '
            'Familiar language can make that ambiguity feel ordinary without resolving it.',
            'There can be a difference between feeling confident about a possibility and understanding its place in the business. '
            'Both impressions may exist at the same time.',
            'Uncertainty can persist even when the surrounding conversation sounds practical. '
            'The subject can remain significant without a concrete account of what follows from it.',
            'For the owner, this can be an ongoing consideration rather than a settled answer. '
            'Its relevance depends on circumstances that may be difficult to describe completely.',
        ]
        random.Random(20260907 + variant).shuffle(blocks)
        changed = '\n\n'.join(blocks)[:2000]
    elif defect_type == 'incoherent':
        words = body.split()
        random.Random(20260907 + variant).shuffle(words)
        changed = ' '.join(words)[:2000]
        if len(changed)<150 or changed==body:
            # Predefined mechanical fallback, independent of quality/evaluator scores.
            changed=('Because it therefore before this without the which and then. '*24).strip()
            if changed==body:
                changed=('Before which it therefore after the because without then. '*24).strip()
    else:
        raise ValueError('Unknown defect type')
    if not 150 <= len(changed) <= 2000 or changed == body:
        raise ValueError('Fault transformation violates frozen mechanical contract')
    modified = dict(original, body=changed)
    return dict(modified=modified, defect_type=defect_type, variant=variant,
                original_sha256=hashlib.sha256(body.encode()).hexdigest(),
                modified_sha256=hashlib.sha256(changed.encode()).hexdigest(),
                diff='\n'.join(difflib.unified_diff(body.splitlines(), changed.splitlines(), fromfile='original', tofile='modified', lineterm='')),
                interpretation='Intended synthetic fault, not human ground truth. May affect multiple rubric dimensions; no score-based regeneration.')
