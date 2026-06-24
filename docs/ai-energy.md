# DC Map Energy Demand Data Pipeline PRD

## 1. Objective

Build a reliable data extraction and normalization pipeline for the DC Map project.

The project has pivoted from mapping individual data center facilities to visualizing global and regional electricity demand from data centers and AI infrastructure.

The goal is to use credible research PDFs and reports to create structured JSON data that can power a public web visualization.

The pipeline must avoid processing entire 300-500 page PDFs with an LLM. Instead, it should index documents, find relevant pages, extract only useful text/tables, and normalize the results into clean data files.

---

## 2. Product Goal

Create a public visualization showing:

- Global electricity demand over time
- Data center electricity demand over time
- AI-related data center electricity demand where available
- Data center electricity demand as a percentage of total electricity demand
- Regional/country-level demand where credible data exists
- Historical values and projections up to 2030
- Low/base/high scenario ranges when available
- Source-backed confidence labels and notes

The output should be good enough for a portfolio project and public educational tool, but it does not need to claim exact real-time accuracy.

All claims must be source-backed.

---

## 3. What We Are Not Building

Do not build a facility-level scraper.

Do not try to collect every individual data center in the world.

Do not scrape random low-quality websites.

Do not estimate individual facility megawatts unless a credible source explicitly states it.

Do not process full PDFs through an LLM.

Do not create unsupported claims.

Do not remove uncertainty. If sources disagree, preserve ranges or scenarios.

---

## 4. Source Folder

Assume PDFs are already placed in a local folder.

Recommended structure:

```txt
/sources/pdfs/
  iea-energy-and-ai.pdf
  iea-global-energy-review.pdf
  epri-data-center-load-growth.pdf
  mckinsey-data-center-demand.pdf
  goldman-sachs-data-center-power-demand.pdf
  uptime-institute-report.pdf
```

The script should work with whatever PDF filenames exist in `/sources/pdfs`.

---

## 5. Core Metrics To Extract

Only extract data relevant to the visualization.

Priority metrics:

```txt
total_electricity_demand_twh
data_center_electricity_demand_twh
ai_data_center_electricity_demand_twh
data_center_share_percent
electricity_generation_twh
electricity_demand_growth_percent
data_center_power_demand_gw
peak_load_gw
projection_low
projection_base
projection_high
```

Important years:

```txt
2020
2021
2022
2023
2024
2025
2030
```

Primary projection target:

```txt
2030
```

---

## 6. Units

Use TWh/year as the main unit for electricity consumption.

Use GW only when the source discusses power capacity or peak demand.

Never mix TWh and GW without labeling clearly.

Normalize these units:

```txt
TWh
GWh
MWh
GW
MW
percent
```

Conversion rules:

```txt
1 TWh = 1,000 GWh
1 GWh = 1,000 MWh
1 GW = 1,000 MW
```

Do not convert GW to TWh unless the source provides load factor, utilization, or annual consumption assumptions.

---

## 7. Required Output Files

Generate these files:

```txt
/data/extracted/pdf_index.json
/data/extracted/relevant_pages.json
/data/extracted/raw_extractions.csv
/data/extracted/source_quotes.json
/public/data/energy-demand.json
/public/data/sources.json
/public/data/meta.json
```

---

## 8. PDF Indexing Step

For each PDF, create an index containing:

```ts
{
  "source_id": "string",
  "filename": "string",
  "title": "string | null",
  "page_count": number,
  "table_of_contents": [],
  "headings": [],
  "figures": [],
  "tables": [],
  "keyword_hits": []
}
```

Extract:

- document title
- page count
- table of contents if available
- headings
- figure captions
- table captions
- pages containing relevant keywords

Do not send full PDF text to an LLM.

---

## 9. Keyword Search

Search each PDF for these terms:

```txt
data center
data centre
AI
artificial intelligence
electricity demand
electricity consumption
power demand
energy demand
TWh
GWh
GW
MW
2030
projection
forecast
scenario
hyperscale
cloud
server
load growth
grid
```

For each hit, store:

```ts
{
  "source_id": "string",
  "page": number,
  "keyword": "string",
  "snippet": "string"
}
```

---

## 10. Relevant Page Selection

Select only pages likely to contain useful data.

A page is relevant if it contains:

- data center electricity demand
- AI electricity demand
- 2030 projections
- TWh/GW values
- regional or country-level electricity demand
- charts/tables about data center load growth
- scenario ranges
- data center share of electricity demand

Include neighboring pages around highly relevant hits.

Example:

If page 42 contains a chart caption about data center electricity demand, also extract pages 41 and 43.

---

## 11. Extraction Step

For relevant pages only, extract:

- plain text
- tables
- chart captions
- nearby numeric values
- footnotes
- source notes

Preferred Python libraries:

```txt
pymupdf
pdfplumber
camelot
tabula
pandas
```

Use OCR only as a fallback.

---

## 12. Raw Extraction Format

Write extracted rows to:

```txt
/data/extracted/raw_extractions.csv
```

Columns:

```csv
source_id,source_name,filename,page,year,region,country,metric,value,unit,scenario,quote,note,confidence
```

Definitions:

- `source_id`: stable slug for source
- `source_name`: human-readable source name
- `filename`: PDF filename
- `page`: page number in PDF
- `year`: year the value applies to
- `region`: global, north_america, europe, asia_pacific, middle_east, africa, latam, or null
- `country`: country name if applicable
- `metric`: normalized metric key
- `value`: numeric value
- `unit`: TWh, GW, percent, etc.
- `scenario`: historical, estimate, low, base, high
- `quote`: short supporting quote or caption
- `note`: caveats
- `confidence`: high, medium, low

---

## 13. Normalized Web Data Schema

Generate:

```txt
/public/data/energy-demand.json
```

Shape:

```ts
[
  {
    "id": "global_datacenter_demand_2024_iea",
    "year": 2024,
    "region": "global",
    "country": null,
    "metric": "data_center_electricity_demand_twh",
    "value": 415,
    "unit": "TWh",
    "scenario": "estimate",
    "source_id": "iea_energy_ai_2025",
    "source_label": "IEA Energy and AI",
    "source_page": 12,
    "confidence": "high",
    "note": "Estimated global data center electricity demand."
  }
]
```

---

## 14. Sources Schema

Generate:

```txt
/public/data/sources.json
```

Shape:

```ts
[
  {
    "id": "iea_energy_ai_2025",
    "name": "IEA Energy and AI",
    "publisher": "International Energy Agency",
    "type": "report",
    "year": 2025,
    "url": "source URL if known",
    "filename": "iea-energy-and-ai.pdf",
    "credibility": "high",
    "notes": "Primary source for global data center electricity demand."
  }
]
```

---

## 15. Meta Schema

Generate:

```txt
/public/data/meta.json
```

Shape:

```ts
{
  "version": "1.0",
  "last_updated": "YYYY-MM-DD",
  "total_records": 0,
  "source_count": 0,
  "metrics": [],
  "coverage": {
    "years": [],
    "regions": [],
    "countries": []
  },
  "disclaimer": "This dataset is compiled from public research reports and should be treated as scenario-based educational data, not real-time operational measurement."
}
```

---

## 16. Confidence Rules

Use `high` when:

- source is IEA, EPRI, Ember, government, official company report, or major research firm
- value is directly stated in a table/chart/text
- unit and year are clear

Use `medium` when:

- source is credible but value is derived from a chart or secondary reporting
- scenario assumptions are clear but not exact

Use `low` when:

- value is approximate
- chart reading is imprecise
- context is incomplete

Do not include low-confidence values in final visualization unless clearly labeled.

---

## 17. Handling Conflicting Sources

If sources disagree, do not choose one silently.

Preserve multiple records with different `source_id` and `scenario`.

Example:

```txt
IEA 2030 global data center demand: base scenario
Uptime 2030 global data center demand: low/high range
Goldman 2030 power demand growth: investment scenario
```

The frontend can show these as scenarios or uncertainty bands.

---

## 18. Derived Calculations

Allowed derived fields:

```txt
data_center_share_percent = data_center_electricity_demand_twh / total_electricity_demand_twh * 100
growth_percent = (future_value - base_value) / base_value * 100
```

When a value is calculated, mark it:

```ts
"derived": true
```

and include:

```ts
"derived_from": ["record_id_1", "record_id_2"]
```

Do not calculate unsupported values.

---

## 19. Recommended Script Structure

```txt
/scripts/
  index_pdfs.py
  find_relevant_pages.py
  extract_relevant_pages.py
  normalize_extractions.py
  validate_dataset.py
```

Execution order:

```bash
python scripts/index_pdfs.py
python scripts/find_relevant_pages.py
python scripts/extract_relevant_pages.py
python scripts/normalize_extractions.py
python scripts/validate_dataset.py
```

---

## 20. Validation Rules

Before writing final JSON:

- every record must have `source_id`
- every record must have `year`
- every record must have `metric`
- every record must have numeric `value`
- every record must have `unit`
- every record must have `confidence`
- every non-derived record must have `source_page`
- no unsupported unit mixing
- no duplicate IDs
- no full PDF text stored in output JSON
- no random unsourced claims

---

## 21. Website Visualization Target

The final dataset should support these frontend views:

### Global Timeline

Line chart:

- total electricity demand TWh
- data center electricity demand TWh
- AI data center demand TWh if available

### Share View

Area or line chart:

- data center share of global electricity demand

### Regional Map

World map colored by:

- data center electricity demand TWh
- data center share percent
- projected 2030 growth

### Scenario Toggle

Toggle between:

- historical
- estimate
- low
- base
- high

### Source Panel

For each number shown, display:

- source name
- source page
- confidence
- short note
- link if available

---

## 22. Final Deliverable

The final output should be a clean, source-backed dataset that can power the DC Map website.

The pipeline should prioritize accuracy, traceability, and small targeted extraction over aggressive scraping.

The most important principle:

Every number on the website must be traceable to a credible source, page number, and note.
