# esg-report-parser

> **ESG/sustainability report PDF → structured metrics JSON.** Scope 1/2/3 emissions, energy, water, waste, diversity, governance — normalized across GRI, SASB, TCFD, CDP frameworks.

[![PyPI](https://img.shields.io/pypi/v/esg-report-parser?style=flat)](https://pypi.org/project/esg-report-parser/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Quickstart

```bash
pip install esg-report-parser
python -m esg_report_parser sustainability_report.pdf
python -m esg_report_parser esg_report.txt --json
```

## Extracted metrics

**Emissions** — Scope 1, 2 (market + location-based), 3, intensity, YoY change, net-zero target

**Energy** — total consumption MWh, renewable %, energy intensity

**Water** — withdrawal m³, recycled %, water-stress area exposure

**Waste** — total tonnes, landfill diversion %, hazardous waste

**Diversity** — women in workforce/leadership/board %, pay equity ratio

**Safety** — TRIR, LTIR, fatalities, lost days

**Governance** — board independence %, CEO pay ratio, ethics violations

**Ratings** — MSCI, Sustainalytics, ISS, CDP, DJSI scores

## License
MIT © [Alper Nabil Gabra Zakher](https://github.com/AlperNab)
