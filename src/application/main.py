import argparse
from pathlib import Path
from datetime import datetime, date

from src.infrastructure.repositories import FileSystemRepository
from src.domain.policy_loader import PolicyLoader
from src.application.use_cases import ValidationOrchestrator
from src.domain.models import ProjectionContext

ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "data" / "processed"
OUTPUT = PROCESSED / "real_scale_cycle"
POLICY_PATH = ROOT / "schemas" / "compliance_policy.example.json"

def parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()

def main():
    parser = argparse.ArgumentParser(description="Run Compliance Validation with Real Architecture")
    parser.add_argument("--period-start", default="2026-02-08")
    parser.add_argument("--period-end", default="2026-03-31")
    parser.add_argument("--anchor-scale-id", type=int, default=1)
    parser.add_argument("--sector-id", default="CAIXA", help="Target sector ID")
    args = parser.parse_args()

    print(f"Starting Validation for Sector: {args.sector_id}")
    print(f"Period: {args.period_start} to {args.period_end}")

    # Setup
    repo = FileSystemRepository(data_path=PROCESSED)
    policy_loader = PolicyLoader(schemas_path=ROOT / "schemas")
    
    orchestrator = ValidationOrchestrator(
        repo=repo,
        policy_loader=policy_loader,
        output_path=OUTPUT
    )

    context = ProjectionContext(
        period_start=parse_date(args.period_start),
        period_end=parse_date(args.period_end),
        anchor_scale_id=args.anchor_scale_id,
        sector_id=args.sector_id,
    )

    # Run
    try:
        result = orchestrator.run(context, POLICY_PATH)
        print("Validation Completed Successfully.")
        print(result)
        print(f"\nOutputs generated in: {OUTPUT}")
    except Exception as e:
        print(f"Validation Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
