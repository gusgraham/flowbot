"""
Legacy module imports - isolated to prevent formatter reordering issues.
"""

import sys
from pathlib import Path

# Add legacy folder to sys.path
_legacy_path = Path(__file__).parent.parent.parent.parent / 'legacy'
if str(_legacy_path) not in sys.path:
    sys.path.insert(0, str(_legacy_path))

# Import legacy modules
import Storage_Modeller as Plato_SM
import Storage_Modeller_Catchment as PLATO_SM_Catchment
import Storage_Modeller_WWTW as PLATO_SM_WWTW

__all__ = ['Plato_SM', 'PLATO_SM_Catchment', 'PLATO_SM_WWTW']
