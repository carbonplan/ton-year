# flake8: noqa

from pkg_resources import DistributionNotFound, get_distribution

from .core import calculate_tonyears, get_baseline_curve, print_benefit_report
from .ghgforcing import joos_2013, joos_2013_monte_carlo

try:
    version = get_distribution(__name__).version
except DistributionNotFound:  # pragma: no cover
    version = '0.0.0'  # pragma: no cover
__version__ = version
