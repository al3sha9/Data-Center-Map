# Methodology

Data Center Map uses public research reports to estimate how electricity demand from data centers and AI infrastructure is changing over time.

The project does not use live grid data or private facility-level data. Most data center power and electricity figures are not publicly disclosed, so the dataset is based on credible published estimates and scenarios.

## Main Unit

The main unit is `TWh/year` because the project is about electricity consumption over time.

`GW` or `MW` may appear in source reports, but those usually describe power capacity or peak load. They are not converted into `TWh` unless the source provides enough information to support that conversion.

## Source Selection

Sources are prioritized in this order:

1. International energy organizations
2. Government or grid research bodies
3. Major research firms
4. Company reports
5. Academic papers
6. Credible industry publications

Random scraped datasets are not used for final claims unless the data can be verified from a stronger source.

## Extraction Process

The PDFs are not processed fully with an LLM.

The Python pipeline indexes reports, finds pages related to data centers, AI, electricity demand, `TWh`, and 2030 projections, then extracts possible numeric claims.

The extracted rows are reviewed before they are added to the final public dataset.

## Review Process

A number is promoted to the final dataset only if it clearly has:

- Source
- Page number
- Year
- Metric
- Value
- Unit
- Scenario
- Supporting quote or context

Numbers are rejected if they are:

- Chart axis labels
- Unrelated electricity figures
- Investment or cost numbers
- Regional growth increments mistaken as totals
- Values without a clear year or unit
- Values without enough context

## Scenarios

Some reports provide multiple projections for 2030. These are kept as separate records instead of forcing one prediction.

Current cleaned global data center electricity demand records:

| Year | Scenario | Value |
|---:|---|---:|
| 2024 | estimate | 415 TWh |
| 2030 | headwinds | 670 TWh |
| 2030 | high efficiency | 800 TWh |
| 2030 | base | 945 TWh |
| 2030 | lift-off | 1,260 TWh |

These are scenario-based estimates, not exact measurements.

## Confidence

Records can be marked as `high`, `medium`, or `low`.

The first public dataset uses manually reviewed records only.

## Disclaimer

This project is meant for public understanding and visualization. It should not be treated as a live energy database or authoritative commercial energy source.

The numbers are based on public research estimates and may change as new reports are published.
