"""Project paths. External development dependencies can be configured after relocation."""
from pathlib import Path
import os, sys
PROJECT = Path(__file__).resolve().parents[1]
SUPPORT = Path(os.environ.get('DARKTIDE_DEV_SUPPORT', PROJECT.parent.parent / 'dev-support')).resolve()
GAME = Path(os.environ.get('DARKTIDE_SOURCE', SUPPORT / 'game-source')).resolve()
FIXTURES = SUPPORT / 'fixtures'
CHECKS = PROJECT / 'build/checks'
CHECKS.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(Path(os.environ.get('DARKTIDE_TEST_RUNTIME', SUPPORT / 'test-runtime'))))
SOURCES = PROJECT / 'src'
