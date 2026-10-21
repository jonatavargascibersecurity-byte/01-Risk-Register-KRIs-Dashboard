"""Loading, validating and saving the project data sets.

The CSV files in ``data/`` are the single source of truth. This module reads
them into typed objects, checks their internal consistency and writes them
back in a stable column order.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from .models import (
    CONTROL_EFFECTIVENESS,
    CONTROL_TYPES,
    DIRECTIONS,
    Appetite,
    Control,
    KRI,
    Risk,
)
from .scales import LEVEL_ORDER, exceeds_appetite

RISK_FIELDS = [
    "id",
    "title",
    "category",
    "asset",
    "scenario",
    "cause",
    "inherent_likelihood",
    "inherent_impact",
    "control_ids",
    "residual_likelihood",
    "residual_impact",
    "owner",
    "treatment",
    "target_date",
    "status",
    "appetite_ref",
    "last_review",
]

CONTROL_FIELDS = [
    "id",
    "name",
    "type",
    "description",
    "framework_ref",
    "owner",
    "effectiveness",
    "last_tested",
    "next_review",
]

KRI_FIELDS = [
    "id",
    "name",
    "category",
    "description",
    "unit",
    "data_source",
    "owner",
    "frequency",
    "direction",
    "green",
    "amber",
    "red",
    "current",
    "previous",
    "linked_risks",
]

APPETITE_FIELDS = [
    "category",
    "appetite_level",
    "tolerance",
    "description",
    "owner",
    "approved_by",
    "approved_on",
]


class DataError(RuntimeError):
    """Raised when the data files cannot be parsed."""


def _read_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise DataError(f"data file not found: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise DataError(f"empty data file: {path}")
        return [dict(row) for row in reader]


def _write_rows(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


@dataclass(frozen=True)
class Registry:
    """The whole GRC data set loaded from disk."""

    risks: list[Risk]
    controls: list[Control]
    kris: list[KRI]
    appetites: list[Appetite]
    source_dir: Path

    @property
    def control_by_id(self) -> dict[str, Control]:
        return {control.id: control for control in self.controls}

    @property
    def appetite_by_category(self) -> dict[str, Appetite]:
        return {appetite.category: appetite for appetite in self.appetites}

    def risks_above_appetite(self) -> list[Risk]:
        appetites = self.appetite_by_category
        breaches = []
        for risk in self.risks:
            appetite = appetites.get(risk.appetite_ref)
            if appetite is None:
                continue
            if exceeds_appetite(risk.residual_level, appetite.appetite_level):
                breaches.append(risk)
        return sorted(breaches, key=lambda r: r.priority_score, reverse=True)

    def validate(self) -> list[str]:
        """Return a list of data-quality findings (empty list = clean data).

        This mirrors what a real register hygiene check looks like: broken
        references, invalid scale values, orphaned controls, KRIs pointing at
        risks that no longer exist and thresholds in the wrong order.
        """

        issues: list[str] = []
        control_ids = {control.id for control in self.controls}
        risk_ids = {risk.id for risk in self.risks}
        appetites = self.appetite_by_category

        seen_risk_ids: set[str] = set()
        for risk in self.risks:
            if risk.id in seen_risk_ids:
                issues.append(f"{risk.id}: duplicated risk id")
            seen_risk_ids.add(risk.id)

            for control_id in risk.control_ids:
                if control_id not in control_ids:
                    issues.append(
                        f"{risk.id}: references unknown control '{control_id}'"
                    )

            if risk.appetite_ref not in appetites:
                issues.append(
                    f"{risk.id}: appetite category '{risk.appetite_ref}' not defined"
                )

            if risk.residual_score > risk.inherent_score:
                issues.append(
                    f"{risk.id}: residual score is higher than inherent score"
                )

            if not risk.treatment.strip():
                issues.append(f"{risk.id}: treatment plan is empty")

        seen_control_ids: set[str] = set()
        for control in self.controls:
            if control.id in seen_control_ids:
                issues.append(f"{control.id}: duplicated control id")
            seen_control_ids.add(control.id)
            if control.type not in CONTROL_TYPES:
                issues.append(
                    f"{control.id}: unknown control type '{control.type}' "
                    f"(expected one of {', '.join(CONTROL_TYPES)})"
                )
            if control.effectiveness not in CONTROL_EFFECTIVENESS:
                issues.append(
                    f"{control.id}: unknown effectiveness '{control.effectiveness}'"
                )

        orphan_controls = control_ids - {
            cid for risk in self.risks for cid in risk.control_ids
        }
        for control_id in sorted(orphan_controls):
            issues.append(f"{control_id}: control is not linked to any risk")

        for kri in self.kris:
            if kri.direction not in DIRECTIONS:
                issues.append(f"{kri.id}: unknown direction '{kri.direction}'")
            if kri.direction == "higher_is_better" and not kri.green > kri.amber > kri.red:
                issues.append(
                    f"{kri.id}: thresholds must satisfy green > amber > red "
                    "for a higher_is_better indicator"
                )
            if kri.direction == "lower_is_better" and not kri.green < kri.amber < kri.red:
                issues.append(
                    f"{kri.id}: thresholds must satisfy green < amber < red "
                    "for a lower_is_better indicator"
                )
            for linked in kri.linked_risks:
                if linked not in risk_ids:
                    issues.append(f"{kri.id}: links to unknown risk '{linked}'")

        for appetite in self.appetites:
            if appetite.appetite_level not in LEVEL_ORDER:
                issues.append(
                    f"{appetite.category}: unknown appetite level "
                    f"'{appetite.appetite_level}'"
                )

        return issues


def load_registry(data_dir: str | Path) -> Registry:
    """Load every data file from *data_dir* into a :class:`Registry`."""

    base = Path(data_dir)
    try:
        risks = [Risk.from_row(row) for row in _read_rows(base / "risks.csv")]
        controls = [Control.from_row(row) for row in _read_rows(base / "controls.csv")]
        kris = [KRI.from_row(row) for row in _read_rows(base / "kris.csv")]
        appetites = [Appetite.from_row(row) for row in _read_rows(base / "risk_appetite.csv")]
    except KeyError as exc:
        raise DataError(f"missing column in data file: {exc}") from exc
    return Registry(
        risks=risks,
        controls=controls,
        kris=kris,
        appetites=appetites,
        source_dir=base,
    )


def save_registry(registry: Registry, data_dir: str | Path) -> None:
    """Write the registry back to CSV files (stable column order)."""

    base = Path(data_dir)
    _write_rows(base / "risks.csv", [r.to_row() for r in registry.risks], RISK_FIELDS)
    _write_rows(
        base / "controls.csv", [c.to_row() for c in registry.controls], CONTROL_FIELDS
    )
    _write_rows(base / "kris.csv", [k.to_row() for k in registry.kris], KRI_FIELDS)
    _write_rows(
        base / "risk_appetite.csv",
        [a.to_row() for a in registry.appetites],
        APPETITE_FIELDS,
    )
