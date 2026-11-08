"""Offline reproduction of the historical N=125 rationale and two H3 scenarios."""
import hashlib
import importlib.util
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import scipy
from scipy.stats import binom, norm

ROOT = Path(__file__).resolve().parents[3]
source = ROOT / "code/bareni_pipeline/sample_size.py"
spec = importlib.util.spec_from_file_location("historical_sample_size", source)
historical = importlib.util.module_from_spec(spec)
spec.loader.exec_module(historical)
paths = [source, ROOT / "최종실험_표본수결정_v1.0.md",
         ROOT / "code/tests/test_sample_size.py",
         ROOT / "studies/study_e_redesign/193_H123_SAMPLE_SIZE_PLANNING.md",
         ROOT / "studies/study_e_redesign/tools/pilot125_v1/plan_h123_n.py",
         ROOT / "studies/study_e_redesign/private/pilot125_v1/h123_n_planning_scenarios.json"]
def hashes():
    return {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
before = hashes()
conditional = []
for d in range(126):
    x = np.arange(d + 1)
    reject = np.minimum(1, 2 * np.minimum(binom.cdf(x, d, .5), binom.sf(x - 1, d, .5))) <= .05
    conditional.append(float(binom.pmf(x, d, .9)[reject].sum()))
oracle = {n: float(binom.pmf(np.arange(n + 1), n, .1) @ np.array(conditional[:n + 1]))
          for n in range(1, 126)}
original = {n: historical.unconditional_mcnemar_power(n, .1, .9) for n in [100, 120, 124, 125]}
assert all(abs(v - oracle[n]) < 1e-12 for n, v in original.items())
assert next(n for n, v in oracle.items() if v >= .8) == 125

saved = json.loads(paths[-1].read_text(encoding="utf-8"))["H3"]["scenarios"][:2]
scenarios = []
for old in saved:
    p, r, h = old["initial_low_rate"], old["repair_rate"], old["worsening_rate"]
    probabilities = np.array([p*r, (1-p)*h, p*(1-r), (1-p)*(1-h)])
    values = np.array([.7, -1., -.3, 0.])
    mu = float(probabilities @ values)
    variance = float(probabilities @ values**2 - mu**2)
    n = math.ceil((norm.ppf(.95) + norm.ppf(.8))**2 * variance / mu**2)
    rng = np.random.default_rng(202609061931 + round(p*10000) + round(h*100000))
    def simulate(size, probs):
        counts = rng.multinomial(size, probs, size=100000)
        means = counts @ values / size
        sample_variance = (counts @ values**2 - size*means**2) / (size-1)
        statistic = np.divide(means, np.sqrt(sample_variance/size),
                              out=np.full_like(means, -np.inf), where=sample_variance > 0)
        return float(np.mean(statistic > norm.ppf(.95)))
    boundary_r = .3 + (1-p)/p*h
    null = np.array([p*boundary_r, (1-p)*h, p*(1-boundary_r), (1-p)*(1-h)])
    reproduced = dict(approx_n=n, mc_power_at_n=simulate(n, probabilities),
                      mc_null_size_at_n=simulate(n, null), mc_power_at_125=simulate(125, probabilities))
    assert all(reproduced[k] == old[k] for k in reproduced)
    scenarios.append(dict(initial_low_rate=p, repair_rate=r, worsening_rate=h, **reproduced))
assert before == hashes()
result = dict(verified_at=datetime.now(timezone.utc).isoformat(),
              numpy=np.__version__, scipy=scipy.__version__, source_hashes=before,
              sources_unchanged=True, original_mcnemar_power=original,
              independent_first_n_at_80_percent=125, independent_oracle_matches=True,
              h3_scenarios_reproduced=scenarios, new_model_calls=0)
destination = ROOT / "studies/study_e_redesign/private/sample_size_review_v1/historical_calculation_verification.json"
with destination.open("x", encoding="utf-8") as f:
    json.dump(result, f, indent=2, ensure_ascii=False)
    f.write("\n")
print(json.dumps(result, indent=2, ensure_ascii=False))
