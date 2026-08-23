# Re-export all program models from this package root for backward compatibility.
from .models_programs import Program, Degree, Step, DegreeFile, DEGREE_FILE_TYPES
from .models_assets import (
    Asset, QCMQuestion, FormFieldDef, ASSET_TYPES,
    PriseDeContact, PriseDeContactAsset,
)

__all__ = [
    'Program', 'Degree', 'Step', 'DegreeFile', 'DEGREE_FILE_TYPES',
    'Asset', 'QCMQuestion', 'FormFieldDef', 'ASSET_TYPES',
    'PriseDeContact', 'PriseDeContactAsset',
]
