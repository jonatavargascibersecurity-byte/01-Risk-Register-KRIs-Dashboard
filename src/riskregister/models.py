"""Domain models for the risk register, control catalog, KRI set and appetite.

Each model knows how to build itself from a CSV row (``from_row``) and how to
serialise itself back to a CSV row (``to_row``). Keeping the mapping in one
place makes the data files the single source of truth for the project.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .scales import (
    APPETITE_EN,
    LEVEL_EN,
    level,
    reduction_pct,
    score,
)

CONTROL_TYPES = ("Preventiva", "Detetiva", "Corretiva")
CONTROL_EFFECTIVENESS = ("Eficiente", "Parcialmente eficiente", "Insuficiente")
DIRECTIONS = ("higher_is_better", "lower_is_better")


def _split_list(raw: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in raw.split(";") if item.strip())


def _to_int(raw: str, field_name: str, row_id: str) -> int:
    try:
        return int(str(raw).strip())
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"{row_id}: field '{field_name}' must be an integer (got {raw!r})"
        ) from exc


def _to_float(raw: str, field_name: str, row_id: str) -> float:
    try:
        return float(str(raw).strip())
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"{row_id}: field '{field_name}' must be a number (got {raw!r})"
        ) from exc


@dataclass(frozen=True)
class Risk:
    """A single entry of the risk register."""

    id: str
    title: str
    category: str
    asset: str
    scenario: str
    cause: str
    inherent_likelihood: int
    inherent_impact: int
    residual_likelihood: int
    residual_impact: int
    owner: str
    treatment: str
    target_date: str
    status: str
    appetite_ref: str
    last_review: str
    control_ids: tuple[str, ...] = field(default_factory=tuple)

    @classmethod
    def from_row(cls, row: dict[str, str]) -> "Risk":
        return cls(
            id=row["id"].strip(),
            title=row["title"].strip(),
            category=row["category"].strip(),
            asset=row["asset"].strip(),
            scenario=row["scenario"].strip(),
            cause=row["cause"].strip(),
            inherent_likelihood=_to_int(
                row["inherent_likelihood"], "inherent_likelihood", row.get("id", "?")
            ),
            inherent_impact=_to_int(
                row["inherent_impact"], "inherent_impact", row.get("id", "?")
            ),
            residual_likelihood=_to_int(
                row["residual_likelihood"], "residual_likelihood", row.get("id", "?")
            ),
            residual_impact=_to_int(
                row["residual_impact"], "residual_impact", row.get("id", "?")
            ),
            owner=row["owner"].strip(),
            treatment=row["treatment"].strip(),
            target_date=row["target_date"].strip(),
            status=row["status"].strip(),
            appetite_ref=row["appetite_ref"].strip(),
            last_review=row["last_review"].strip(),
            control_ids=_split_list(row.get("control_ids", "")),
        )

    def to_row(self) -> dict[str, str]:
        return {
            "id": self.id,
            "title": self.title,
            "category": self.category,
            "asset": self.asset,
            "scenario": self.scenario,
            "cause": self.cause,
            "inherent_likelihood": str(self.inherent_likelihood),
            "inherent_impact": str(self.inherent_impact),
            "control_ids": ";".join(self.control_ids),
            "residual_likelihood": str(self.residual_likelihood),
            "residual_impact": str(self.residual_impact),
            "owner": self.owner,
            "treatment": self.treatment,
            "target_date": self.target_date,
            "status": self.status,
            "appetite_ref": self.appetite_ref,
            "last_review": self.last_review,
        }

    @property
    def inherent_score(self) -> int:
        return score(self.inherent_likelihood, self.inherent_impact)

    @property
    def residual_score(self) -> int:
        return score(self.residual_likelihood, self.residual_impact)

    @property
    def inherent_level(self) -> str:
        return level(self.inherent_score)

    @property
    def residual_level(self) -> str:
        return level(self.residual_score)

    @property
    def residual_level_en(self) -> str:
        return LEVEL_EN[self.residual_level]

    @property
    def reduction_pct(self) -> float:
        return reduction_pct(self.inherent_score, self.residual_score)

    @property
    def priority_score(self) -> float:
        """Ranking score used to sort the register.

        Residual severity dominates; residual score above appetite and an
        overdue treatment date push a risk up the list.
        """

        value = float(self.residual_score)
        if self.status not in ("Fechado", "Closed"):
            value += 2.0
        return value


@dataclass(frozen=True)
class Control:
    """A control referenced by the risk register."""

    id: str
    name: str
    type: str
    description: str
    framework_ref: str
    owner: str
    effectiveness: str
    last_tested: str
    next_review: str

    @classmethod
    def from_row(cls, row: dict[str, str]) -> "Control":
        return cls(
            id=row["id"].strip(),
            name=row["name"].strip(),
            type=row["type"].strip(),
            description=row["description"].strip(),
            framework_ref=row["framework_ref"].strip(),
            owner=row["owner"].strip(),
            effectiveness=row["effectiveness"].strip(),
            last_tested=row["last_tested"].strip(),
            next_review=row["next_review"].strip(),
        )

    def to_row(self) -> dict[str, str]:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "description": self.description,
            "framework_ref": self.framework_ref,
            "owner": self.owner,
            "effectiveness": self.effectiveness,
            "last_tested": self.last_tested,
            "next_review": self.next_review,
        }

    @property
    def is_effective(self) -> bool:
        return self.effectiveness == "Eficiente"


@dataclass(frozen=True)
class KRI:
    """A Key Risk Indicator measured against a green/amber/red threshold set."""

    id: str
    name: str
    category: str
    description: str
    unit: str
    data_source: str
    owner: str
    frequency: str
    direction: str
    green: float
    amber: float
    red: float
    current: float | None
    previous: float | None
    linked_risks: tuple[str, ...] = field(default_factory=tuple)

    @classmethod
    def from_row(cls, row: dict[str, str]) -> "KRI":
        row_id = row.get("id", "?")
        current_raw = row.get("current", "").strip()
        previous_raw = row.get("previous", "").strip()
        return cls(
            id=row_id.strip(),
            name=row["name"].strip(),
            category=row["category"].strip(),
            description=row["description"].strip(),
            unit=row["unit"].strip(),
            data_source=row["data_source"].strip(),
            owner=row["owner"].strip(),
            frequency=row["frequency"].strip(),
            direction=row["direction"].strip(),
            green=_to_float(row["green"], "green", row_id),
            amber=_to_float(row["amber"], "amber", row_id),
            red=_to_float(row["red"], "red", row_id),
            current=_to_float(current_raw, "current", row_id) if current_raw else None,
            previous=(
                _to_float(previous_raw, "previous", row_id) if previous_raw else None
            ),
            linked_risks=_split_list(row.get("linked_risks", "")),
        )

    def to_row(self) -> dict[str, str]:
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "unit": self.unit,
            "data_source": self.data_source,
            "owner": self.owner,
            "frequency": self.frequency,
            "direction": self.direction,
            "green": _fmt(self.green),
            "amber": _fmt(self.amber),
            "red": _fmt(self.red),
            "current": "" if self.current is None else _fmt(self.current),
            "previous": "" if self.previous is None else _fmt(self.previous),
            "linked_risks": ";".join(self.linked_risks),
        }

    @property
    def status(self) -> str:
        """``Verde`` / ``Amarelo`` / ``Vermelho`` / ``Sem dados``."""

        if self.current is None:
            return "Sem dados"
        if self.direction == "higher_is_better":
            if self.current >= self.green:
                return "Verde"
            if self.current >= self.amber:
                return "Amarelo"
            return "Vermelho"
        if self.direction == "lower_is_better":
            if self.current <= self.green:
                return "Verde"
            if self.current <= self.amber:
                return "Amarelo"
            return "Vermelho"
        raise ValueError(f"{self.id}: unknown direction {self.direction!r}")

    @property
    def trend(self) -> str:
        """``up`` / ``down`` / ``flat`` / ``n/a`` compared with the last period."""

        if self.current is None or self.previous is None:
            return "n/a"
        if self.current == self.previous:
            return "flat"
        return "up" if self.current > self.previous else "down"

    @property
    def trend_is_worsening(self) -> bool:
        if self.trend == "n/a":
            return False
        worse = self.trend == "up" if self.direction == "lower_is_better" else self.trend == "down"
        return worse


@dataclass(frozen=True)
class Appetite:
    """Approved risk appetite for a category of risks."""

    category: str
    appetite_level: str
    tolerance: str
    description: str
    owner: str
    approved_by: str
    approved_on: str

    @classmethod
    def from_row(cls, row: dict[str, str]) -> "Appetite":
        return cls(
            category=row["category"].strip(),
            appetite_level=row["appetite_level"].strip(),
            tolerance=row["tolerance"].strip(),
            description=row["description"].strip(),
            owner=row["owner"].strip(),
            approved_by=row["approved_by"].strip(),
            approved_on=row["approved_on"].strip(),
        )

    def to_row(self) -> dict[str, str]:
        return {
            "category": self.category,
            "appetite_level": self.appetite_level,
            "tolerance": self.tolerance,
            "description": self.description,
            "owner": self.owner,
            "approved_by": self.approved_by,
            "approved_on": self.approved_on,
        }

    @property
    def appetite_level_en(self) -> str:
        return APPETITE_EN.get(self.appetite_level, self.appetite_level)


def _fmt(value: float) -> str:
    if value == int(value):
        return str(int(value))
    return str(value)
