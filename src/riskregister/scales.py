"""Risk scoring scales, severity bands and risk-appetite comparison.

The model is a classic 5x5 likelihood x impact matrix (ISO 31000 / NIST RMF
style). Every score in this package is derived from that matrix so that the
register, the dashboard and the executive report can never disagree.

All numbers are *relative* (1-25). For monetary quantification see the
FAIR/Monte-Carlo extension described in ``docs/roadmap.md``.
"""

from __future__ import annotations

SCALE_MIN = 1
SCALE_MAX = 5
MAX_SCORE = SCALE_MAX * SCALE_MAX

LIKELIHOOD: dict[int, str] = {
    1: "Raro / Rare (< 10% in 12 months)",
    2: "Improvavel / Improbable (10-30%)",
    3: "Possivel / Possible (30-60%)",
    4: "Provavel / Likely (60-85%)",
    5: "Quase certo / Almost certain (> 85%)",
}

IMPACT: dict[int, str] = {
    1: "Muito baixo / Very low (< R$ 10k; no customer impact)",
    2: "Baixo / Low (R$ 10k-100k; isolated customer impact)",
    3: "Moderado / Moderate (R$ 100k-1M; limited customer impact)",
    4: "Alto / High (R$ 1M-10M; wide customer impact)",
    5: "Severo / Severe (> R$ 10M; regulatory or licence at risk)",
}

# (upper bound of score, severity band name)
LEVEL_BANDS: tuple[tuple[int, str], ...] = (
    (4, "Baixo"),
    (9, "Moderado"),
    (14, "Alto"),
    (25, "Critico"),
)

LEVEL_ORDER: dict[str, int] = {
    "Baixo": 1,
    "Moderado": 2,
    "Alto": 3,
    "Critico": 4,
}

LEVEL_EN: dict[str, str] = {
    "Baixo": "Low",
    "Moderado": "Moderate",
    "Alto": "High",
    "Critico": "Critical",
}

APPETITE_EN: dict[str, str] = {
    "Baixo": "Low",
    "Moderado": "Moderate",
    "Alto": "High",
}

KRI_STATUS_ORDER: dict[str, int] = {"Verde": 1, "Amarelo": 2, "Vermelho": 3, "Sem dados": 0}


def validate_scale_value(value: int, name: str) -> None:
    """Raise ``ValueError`` when *value* is outside the 1-5 scale."""

    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{name} must be an integer between {SCALE_MIN} and {SCALE_MAX}")
    if not SCALE_MIN <= value <= SCALE_MAX:
        raise ValueError(
            f"{name} must be between {SCALE_MIN} and {SCALE_MAX} (got {value})"
        )


def score(likelihood: int, impact: int) -> int:
    """Return the 1-25 risk score for a likelihood/impact pair."""

    validate_scale_value(likelihood, "likelihood")
    validate_scale_value(impact, "impact")
    return likelihood * impact


def level(score_value: int) -> str:
    """Map a 1-25 score to its severity band (``Baixo`` ... ``Critico``)."""

    if not 1 <= score_value <= MAX_SCORE:
        raise ValueError(f"score must be between 1 and {MAX_SCORE} (got {score_value})")
    for upper, name in LEVEL_BANDS:
        if score_value <= upper:
            return name
    return LEVEL_BANDS[-1][1]


def level_rank(level_name: str) -> int:
    """Return the ordinal rank of a severity band (1 = lowest)."""

    try:
        return LEVEL_ORDER[level_name]
    except KeyError as exc:  # pragma: no cover - defensive
        raise ValueError(f"unknown severity band: {level_name!r}") from exc


def exceeds_appetite(residual_level: str, appetite_level: str) -> bool:
    """``True`` when the residual severity is above the approved appetite."""

    return level_rank(residual_level) > level_rank(appetite_level)


def reduction_pct(inherent_score: int, residual_score: int) -> float:
    """Percentage of inherent risk removed by the current control set."""

    if inherent_score <= 0:
        return 0.0
    return round((inherent_score - residual_score) / inherent_score * 100, 1)


def heatmap_cell(likelihood: int, impact: int) -> str:
    """Severity band of a heat-map cell (same rule as :func:`level`)."""

    return level(score(likelihood, impact))
