"""Unit tests for the risk scoring engine."""

from riskregister.scales import (
    exceeds_appetite,
    level,
    reduction_pct,
    score,
)
from riskregister.models import KRI, Risk


def test_score_is_product():
    assert score(3, 4) == 12
    assert score(1, 1) == 1
    assert score(5, 5) == 25


def test_level_bands():
    assert level(1) == "Baixo"
    assert level(4) == "Baixo"
    assert level(5) == "Moderado"
    assert level(9) == "Moderado"
    assert level(10) == "Alto"
    assert level(14) == "Alto"
    assert level(15) == "Critico"
    assert level(25) == "Critico"


def test_reduction_pct():
    assert reduction_pct(20, 10) == 50.0
    assert reduction_pct(25, 25) == 0.0
    assert reduction_pct(0, 0) == 0.0


def test_exceeds_appetite():
    assert exceeds_appetite("Alto", "Moderado") is True
    assert exceeds_appetite("Moderado", "Alto") is False
    assert exceeds_appetite("Baixo", "Baixo") is False


def test_risk_properties():
    row = {
        "id": "R-999",
        "title": "t",
        "category": "c",
        "asset": "a",
        "scenario": "s",
        "cause": "ca",
        "inherent_likelihood": "5",
        "inherent_impact": "4",
        "residual_likelihood": "3",
        "residual_impact": "2",
        "owner": "o",
        "treatment": "tr",
        "target_date": "2026-12-31",
        "status": "Em andamento",
        "appetite_ref": "c",
        "last_review": "2026-09-30",
        "control_ids": "C-01;C-02",
    }
    risk = Risk.from_row(row)
    assert risk.inherent_score == 20
    assert risk.residual_score == 6
    assert risk.inherent_level == "Critico"
    assert risk.reduction_pct == 70.0
    assert risk.control_ids == ("C-01", "C-02")


def _kri(direction, green, amber, red, current, previous=None):
    return KRI(
        id="KRI-X", name="n", category="c", description="d", unit="%",
        data_source="ds", owner="o", frequency="Mensal", direction=direction,
        green=green, amber=amber, red=red, current=current, previous=previous,
        linked_risks=(),
    )


def test_kri_status_higher_is_better():
    assert _kri("higher_is_better", 95, 85, 0, 97).status == "Verde"
    assert _kri("higher_is_better", 95, 85, 0, 88).status == "Amarelo"
    assert _kri("higher_is_better", 95, 85, 0, 70).status == "Vermelho"


def test_kri_status_lower_is_better():
    assert _kri("lower_is_better", 2, 8, 999, 1).status == "Verde"
    assert _kri("lower_is_better", 2, 8, 999, 5).status == "Amarelo"
    assert _kri("lower_is_better", 2, 8, 999, 20).status == "Vermelho"


def test_kri_trend_worsening():
    worsen = _kri("lower_is_better", 2, 8, 999, 10, previous=4)
    improve = _kri("lower_is_better", 2, 8, 999, 3, previous=4)
    assert worsen.trend == "up" and worsen.trend_is_worsening
    assert improve.trend == "down" and not improve.trend_is_worsening


def test_kri_no_data():
    kri = KRI(
        id="KRI-Y", name="n", category="c", description="d", unit="%",
        data_source="ds", owner="o", frequency="Mensal", direction="lower_is_better",
        green=1, amber=2, red=3, current=None, previous=1, linked_risks=(),
    )
    assert kri.status == "Sem dados"
    assert kri.trend == "n/a"
