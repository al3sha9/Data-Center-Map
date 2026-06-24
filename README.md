# Data Centre Map

![Status](https://img.shields.io/badge/status-in_progress-orange?style=flat-square)
![Pipeline](https://img.shields.io/badge/pipeline-data_extraction-blue?style=flat-square)
![Records](https://img.shields.io/badge/reviewed_records-5-brightgreen?style=flat-square)
![Python](https://img.shields.io/badge/python-3.10%2B-3776ab?style=flat-square&logo=python&logoColor=white)

Data Centre Map is a data visualization project about the growing electricity demand of data centers and AI infrastructure.

The original idea was to build a world map of individual data centers. After collecting data from public sources, it became clear that facility-level data is too inconsistent. A lot of public datasets include very small server rooms, university servers, or facilities with no disclosed power capacity. That makes it hard to make a useful claim about global infrastructure.

So the project has shifted toward a better question:

> How much electricity are data centers using today, and how much could they need by 2030?

The goal is to show this using TWh/year, sourced from credible public reports instead of random scraped data.

## What this project is trying to show

The visualization will focus on:

- global data center electricity demand
- AI-related data center demand where available
- 2024 baseline values
- 2030 projections
- low, base, and high scenarios
- regional differences where reliable data exists
- source-backed notes for every number

The project is not trying to be a real-time monitoring tool. It is based on public research, estimates, and projections.

## Current dataset

The current cleaned dataset includes these global data center electricity demand records:

| Year | Scenario | Value |
|---|---:|---:|
| 2024 | estimate | 415 TWh |
| 2030 | headwinds | 670 TWh |
| 2030 | high efficiency | 800 TWh |
| 2030 | base | 945 TWh |
| 2030 | lift-off | 1260 TWh |

These records are extracted from public research PDFs and manually reviewed before being added to the final dataset.

## Planned visualization

The frontend will include:

- scenario chart for 2024 to 2030 demand
- map view for regional/country-level data when available
- timeline slider
- source panel for every displayed number
- simple methodology/disclaimer page

The main unit is **TWh/year** because the project is about electricity consumption over time. GW may be used only when a source is talking about power capacity or peak demand.

## Tech stack

Planned frontend:

- React
- Vite
- TypeScript
- Tailwind CSS
- shadcn/ui
- MapLibre/mapcn

Data pipeline:

- Python
- pandas
- PyMuPDF / pdfplumber
- CSV and JSON outputs

## Project structure

```txt
dc-map/
  sources/
    pdfs/                  # downloaded research reports

  scripts/
    index_pdfs.py
    find_relevant_pages.py
    extract_relevant_pages.py
    create_priority_review.py
    normalize_extractions.py
    validate_dataset.py

  data/
    extracted/             # intermediate extraction and review files
    manual/                # manually approved/rejected data if needed

  public/
    data/
      energy-demand.json   # final dataset used by the website
      sources.json
      meta.json

  docs/
    methodology.md
    data-sources.md
    review-process.md
```

## Data pipeline

The Python scripts are only there to help prepare the data.

They do this:

1. index the PDFs
2. find pages that mention data centers, AI, electricity demand, TWh, 2030, and related terms
3. extract possible numbers from those pages
4. create a smaller review file with likely useful claims
5. manually approve only the claims that are clearly supported by the source
6. normalize approved claims into JSON
7. validate the final dataset

The pipeline does not automatically trust every number it finds. Anything important has to be reviewed before it goes into the public dataset.

## Data quality rules

Every final number should have:

- a source
- a page number
- a year
- a metric
- a unit
- a scenario
- a short note or quote
- a confidence label

If a number is unclear, unrelated, or only appears as a chart axis label, it should not be used.

## Disclaimer

This project uses public reports and research estimates. The numbers should be treated as educational, scenario-based data, not exact real-time measurements.

The goal is to make the scale of data center electricity demand easier to understand, not to provide a commercial or authoritative energy database.

## Status

Work in progress.

The first cleaned global scenario dataset is ready. Next steps are organizing the project, building the first chart, then adding regional data once enough reliable records are reviewed.# Data-Center-Map
