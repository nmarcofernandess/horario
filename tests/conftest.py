"""Pytest configuration and shared fixtures."""
import sys
from pathlib import Path

# Add project root to path for imports
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
