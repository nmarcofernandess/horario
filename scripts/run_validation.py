#!/usr/bin/env python3
"""Script para rodar validação via linha de comando."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from datetime import date
from src.infrastructure.database.setup import SessionLocal, init_db
from src.infrastructure.repositories_db import SqlAlchemyRepository
from src.domain.policy_loader import PolicyLoader
from src.domain.models import ProjectionContext
from src.application.use_cases import ValidationOrchestrator

def main():
    init_db()
    session = SessionLocal()
    repo = SqlAlchemyRepository(session)
    policy_loader = PolicyLoader(schemas_path=ROOT / "schemas")
    orchestrator = ValidationOrchestrator(
        repo=repo,
        policy_loader=policy_loader,
        output_path=ROOT / "data" / "processed" / "real_scale_cycle",
        data_dir=ROOT / "data" / "processed"
    )
    context = ProjectionContext(
        period_start=date(2026, 2, 8),
        period_end=date(2026, 3, 31),
        sector_id="CAIXA",
        anchor_scale_id=1
    )
    result = orchestrator.run(context, ROOT / "schemas" / "compliance_policy.example.json")
    print("OK:", result)
    session.close()

if __name__ == "__main__":
    main()
