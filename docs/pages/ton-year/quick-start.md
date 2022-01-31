import Section from '../../components/section'

# Quick start

## Dependencies

- Python 3.8 or later
- numpy
- scipy
- pandas

## Install

The `tonyear` package can be installed using `pip` package installer from [PyPI](https://pypi.org/project/tonyear/):

```
python -m pip install tonyear
```

or from source:

```
python -m pip install git+https://github.com/carbonplan/ton-year
```

## Usage

The `tonyear` package provides a number of functions for exploring various aspects of ton-year accounting. See the [API docs](/api) for a complete listing of functions and parameters or the [How-to Guides](/how-to-guide) for detailed example on how to use the `tonyear` package for specific tasks.

```python
baseline = tonyear.get_baseline_curve("ipcc_2007")
mm = tonyear.calculate_tonyears(
    method="mc",
    baseline=baseline,
    time_horizon=100,
    delay=46,
    discount_rate=0.0
)
```

export default ({ children }) => (
  <Section name='Quick Start'>{children}</Section>
)
