#!/usr/bin/env python3
"""
esg-report-parser — ESG/sustainability report PDF → structured metrics
Extracts: Scope 1/2/3 emissions, energy, water, waste, diversity,
governance, normalized across reporting frameworks (GRI, SASB, TCFD, CDP)
"""
import anthropic, base64, json, re, sys
from pathlib import Path

SYSTEM = """You are a sustainability analyst and ESG data specialist.
Extract all ESG metrics from this report into a standardized, comparable format.

Rules:
- Normalize emissions to tonnes CO2e
- Note base year and reporting year clearly
- Flag any methodology changes, restatements, or data gaps
- Map to frameworks where possible (GRI, SASB, TCFD, CDP)
- Include units for every metric
- Note third-party verification status

Return ONLY valid JSON — no markdown, no explanation.

{
  "company_name": "string",
  "reporting_year": "YYYY or YYYY-YYYY",
  "report_type": "annual_report|sustainability_report|esg_report|integrated_report",
  "frameworks_referenced": ["GRI","SASB","TCFD","CDP","UN SDGs","ISSB","..."],
  "third_party_verified": true_or_false,
  "verifier": "string or null",
  "environmental": {
    "emissions": {
      "scope_1_tonnes_co2e": number_or_null,
      "scope_2_market_based_tonnes_co2e": number_or_null,
      "scope_2_location_based_tonnes_co2e": number_or_null,
      "scope_3_tonnes_co2e": number_or_null,
      "scope_3_categories_included": ["list"],
      "total_ghg_tonnes_co2e": number_or_null,
      "emissions_intensity": "string or null",
      "yoy_change_pct": number_or_null,
      "base_year": "YYYY or null",
      "net_zero_target_year": number_or_null
    },
    "energy": {
      "total_consumption_mwh": number_or_null,
      "renewable_pct": number_or_null,
      "renewable_mwh": number_or_null,
      "energy_intensity": "string or null"
    },
    "water": {
      "total_withdrawal_m3": number_or_null,
      "water_recycled_pct": number_or_null,
      "water_stress_area_pct": number_or_null
    },
    "waste": {
      "total_waste_tonnes": number_or_null,
      "landfill_diversion_pct": number_or_null,
      "hazardous_waste_tonnes": number_or_null,
      "recycled_pct": number_or_null
    },
    "biodiversity_commitments": ["string"],
    "environmental_fines": number_or_null
  },
  "social": {
    "employees": {
      "total_headcount": number_or_null,
      "full_time": number_or_null,
      "part_time": number_or_null,
      "new_hires": number_or_null,
      "turnover_rate_pct": number_or_null
    },
    "diversity": {
      "women_in_workforce_pct": number_or_null,
      "women_in_leadership_pct": number_or_null,
      "women_on_board_pct": number_or_null,
      "underrepresented_groups_pct": number_or_null,
      "pay_equity_ratio": number_or_null
    },
    "health_safety": {
      "trir": number_or_null,
      "ltir": number_or_null,
      "fatalities": number_or_null,
      "lost_days": number_or_null
    },
    "training_hours_per_employee": number_or_null,
    "community_investment_usd": number_or_null,
    "supply_chain_audits": number_or_null
  },
  "governance": {
    "board_size": number_or_null,
    "independent_directors_pct": number_or_null,
    "women_on_board_pct": number_or_null,
    "board_diversity_pct": number_or_null,
    "ceo_pay_ratio": number_or_null,
    "ethics_violations": number_or_null,
    "data_breaches": number_or_null,
    "political_contributions_usd": number_or_null,
    "anti_corruption_training_pct": number_or_null
  },
  "ratings_and_indices": [
    {"provider":"MSCI|Sustainalytics|ISS|CDP|DJSI","rating":"string","score":"string or null"}
  ],
  "key_targets": [
    {"target":"description","deadline":"YYYY or null","progress":"string or null"}
  ],
  "notable_incidents": ["significant ESG incidents mentioned"],
  "data_gaps": ["metrics mentioned but not quantified"],
  "methodology_notes": ["important notes about how metrics were calculated"],
  "analyst_notes": "2-3 sentence ESG quality assessment",
  "confidence": 0.0
}"""

def parse(source: str) -> dict:
    client = anthropic.Anthropic()
    path = Path(source)
    if path.exists() and source.endswith(".pdf"):
        data = base64.standard_b64encode(path.read_bytes()).decode("ascii")
        content = [
            {"type":"document","source":{"type":"base64","media_type":"application/pdf","data":data}},
            {"type":"text","text":"Extract all ESG metrics from this report."}
        ]
    elif path.exists():
        text = path.read_text(encoding="utf-8",errors="replace")[:60000]
        content = [{"type":"text","text":f"Extract ESG metrics:\n\n{text}"}]
    else:
        content = [{"type":"text","text":f"Extract ESG metrics:\n\n{source[:60000]}"}]

    resp = client.messages.create(
        model="claude-sonnet-4-20250514", max_tokens=4096, system=SYSTEM,
        messages=[{"role":"user","content":content}]
    )
    raw = re.sub(r'^```(?:json)?\s*','',resp.content[0].text.strip(),flags=re.MULTILINE)
    raw = re.sub(r'\s*```$','',raw,flags=re.MULTILINE)
    return json.loads(raw)

def fmt(v, unit=""):
    if v is None: return "N/A"
    if isinstance(v, float): return f"{v:,.1f}{unit}"
    return f"{v:,}{unit}"

def print_report(r: dict):
    env = r.get("environmental",{})
    em = env.get("emissions",{})
    soc = r.get("social",{})
    gov = r.get("governance",{})

    print(f"\n{'═'*60}")
    print(f"  ESG REPORT — {r.get('company_name','?')} ({r.get('reporting_year','?')})")
    print(f"  Verified: {'✅' if r.get('third_party_verified') else '❌'} {r.get('verifier','') or ''}")
    print(f"  Frameworks: {', '.join(r.get('frameworks_referenced',[]))}")
    print(f"{'═'*60}")

    print(f"\n  ENVIRONMENT")
    if em.get("scope_1_tonnes_co2e"): print(f"  Scope 1:     {fmt(em['scope_1_tonnes_co2e'],' tCO2e')}")
    if em.get("scope_2_market_based_tonnes_co2e"): print(f"  Scope 2 (mb):{fmt(em['scope_2_market_based_tonnes_co2e'],' tCO2e')}")
    if em.get("scope_3_tonnes_co2e"): print(f"  Scope 3:     {fmt(em['scope_3_tonnes_co2e'],' tCO2e')}")
    if em.get("net_zero_target_year"): print(f"  Net zero by: {em['net_zero_target_year']}")
    energy = env.get("energy",{})
    if energy.get("total_consumption_mwh"): print(f"  Energy:      {fmt(energy['total_consumption_mwh'],' MWh')} ({fmt(energy.get('renewable_pct'),'%')} renewable)")
    water = env.get("water",{})
    if water.get("total_withdrawal_m3"): print(f"  Water:       {fmt(water['total_withdrawal_m3'],' m³')}")
    waste = env.get("waste",{})
    if waste.get("total_waste_tonnes"): print(f"  Waste:       {fmt(waste['total_waste_tonnes'],' tonnes')} ({fmt(waste.get('landfill_diversion_pct'),'%')} diverted)")

    div = soc.get("diversity",{})
    print(f"\n  SOCIAL & DIVERSITY")
    emp = soc.get("employees",{})
    if emp.get("total_headcount"): print(f"  Headcount:   {fmt(emp['total_headcount'])}")
    if div.get("women_in_workforce_pct"): print(f"  Women in workforce: {fmt(div['women_in_workforce_pct'],'%')}")
    if div.get("women_in_leadership_pct"): print(f"  Women in leadership:{fmt(div['women_in_leadership_pct'],'%')}")
    if div.get("women_on_board_pct"): print(f"  Women on board:     {fmt(div['women_on_board_pct'],'%')}")
    hs = soc.get("health_safety",{})
    if hs.get("trir"): print(f"  TRIR: {fmt(hs['trir'])} | Fatalities: {fmt(hs.get('fatalities'))}")

    print(f"\n  GOVERNANCE")
    if gov.get("board_size"): print(f"  Board: {fmt(gov['board_size'])} ({fmt(gov.get('independent_directors_pct'),'%')} independent)")
    if gov.get("ceo_pay_ratio"): print(f"  CEO pay ratio: {fmt(gov['ceo_pay_ratio'],'x')}")

    targets = r.get("key_targets",[])
    if targets:
        print(f"\n  KEY TARGETS ({len(targets)})")
        for t in targets[:4]:
            print(f"  🎯 {t.get('target','')[:70]} — {t.get('deadline','?')}")

    ratings = r.get("ratings_and_indices",[])
    if ratings:
        print(f"\n  ESG RATINGS: {' | '.join(f\"{r2.get('provider','?')}: {r2.get('rating','?')}\" for r2 in ratings)}")

    gaps = r.get("data_gaps",[])
    if gaps: print(f"\n  Data gaps: {', '.join(gaps[:4])}")
    if r.get("analyst_notes"): print(f"\n  Assessment: {r['analyst_notes']}")
    print(f"\n  Confidence: {int(r.get('confidence',0)*100)}%")
    print(f"{'═'*60}\n")

if __name__ == "__main__":
    if len(sys.argv)<2: print("Usage: python -m esg_report_parser <report.pdf|.txt> [--json]"); sys.exit(0)
    r = parse(sys.argv[1])
    if "--json" in sys.argv: print(json.dumps(r,indent=2,ensure_ascii=False))
    else: print_report(r)
