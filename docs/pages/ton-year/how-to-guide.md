import Section from '../../components/section'

# How-to guides

We have prepared four Jupyter Notebooks demonstrating how to use the `tonyear` package.

1. [Ton-year](https://github.com/carbonplan/ton-year/blob/main/notebooks/ton-year.ipynb): Introduces `tonyear` package and walks through how it can be used to compare different ton-year accounting methods.
1. [Checking Moura Costa equivalency claims](https://github.com/carbonplan/ton-year/blob/main/notebooks/mc-equivalency-claim.ipynb): Shows how the Moura Costa ton-year "equivalency" claim fails to produce equivalent outcomes from the standpoint of the atmosphere.
1. [Replicating the NCX equivalency claim](https://github.com/carbonplan/ton-year/blob/main/notebooks/mc-equivalency-claim.ipynb): Attempt to replicate the ton-year calculations reported by NCX.
1. [Exploring additional tonyear approaches implemented by the Climate Action Reserve and the government of Quebec](https://github.com/carbonplan/ton-year/blob/main/notebooks/additional-methods.ipynb): Compares the ton-year methods used by the Climate Action Reserve and proposed by the government of Quebec to the Lashof method.

export default ({ children }) => (
  <Section name='How-to Guide'>{children}</Section>
)
