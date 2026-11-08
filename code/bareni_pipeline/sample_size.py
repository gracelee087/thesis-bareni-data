"""Reproducible unconditional power sensitivity for exact McNemar tests."""

from __future__ import annotations

from functools import lru_cache
from math import comb


def _binomial_probability(k: int, n: int, probability: float) -> float:
    return comb(n, k) * probability**k * (1.0 - probability) ** (n - k)


@lru_cache(maxsize=None)
def exact_two_sided_binomial_pvalue(successes: int, trials: int) -> float:
    """Return the conventional doubled-tail exact p-value under p=.5."""
    if trials == 0:
        return 1.0
    lower = sum(_binomial_probability(k, trials, 0.5)
                for k in range(successes + 1))
    upper = sum(_binomial_probability(k, trials, 0.5)
                for k in range(successes, trials + 1))
    return min(1.0, 2.0 * min(lower, upper))


def unconditional_mcnemar_power(
    tasks: int,
    discordance_probability: float,
    improvement_probability: float,
    *,
    alpha: float = 0.05,
) -> float:
    """Integrate exact McNemar rejection over D~Bin(N,q), X|D~Bin(D,p)."""
    power = 0.0
    for discordant in range(tasks + 1):
        discordant_mass = _binomial_probability(
            discordant, tasks, discordance_probability)
        conditional_rejection = sum(
            _binomial_probability(improved, discordant, improvement_probability)
            for improved in range(discordant + 1)
            if exact_two_sided_binomial_pvalue(improved, discordant) <= alpha
        )
        power += discordant_mass * conditional_rejection
    return power


def minimum_tasks_for_power(
    discordance_probability: float,
    improvement_probability: float,
    *,
    target_power: float = 0.80,
    alpha: float = 0.05,
    maximum_tasks: int = 1000,
) -> int:
    for tasks in range(1, maximum_tasks + 1):
        if unconditional_mcnemar_power(
            tasks,
            discordance_probability,
            improvement_probability,
            alpha=alpha,
        ) >= target_power:
            return tasks
    raise ValueError("Target power not reached within maximum_tasks")
