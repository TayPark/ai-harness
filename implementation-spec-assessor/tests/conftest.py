import copy,json,sys
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
@pytest.fixture
def report(): return json.loads((ROOT/'tests/fixtures/reports/excellent.json').read_text())
@pytest.fixture
def source(): return (ROOT/'tests/fixtures/excellent-prompt.md').read_text()
