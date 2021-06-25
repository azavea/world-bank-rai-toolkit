# flake8: noqa

from rai.preprocess.preprocessor import *
from rai.preprocess.guatemala import *
from rai.preprocess.paraguay import *

country_to_preprocessor = {
    'guatemala': GuatemalaPreprocessor,
    'gt': GuatemalaPreprocessor,
    'paraguay': ParaguayPreprocessor,
    'py': ParaguayPreprocessor
}


def get_country_preprocesor(country: str) -> Preprocessor:
    country = country.strip().lower()
    preprocessor = country_to_preprocessor[country]
    return preprocessor
