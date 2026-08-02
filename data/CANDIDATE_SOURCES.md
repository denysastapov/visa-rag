# Candidate sources — verified pool

Every URL below was fetched and confirmed to resolve and to be the document it
claims to be (checked 2026-11-24). This is the **pool to draw from**, not a
download list — pick from it in tiers.

**Workflow:** download a document → save it as PDF into `data/raw/` →
move its row into [`SOURCES.md`](SOURCES.md) with the local filename.

Most of these are HTML pages. Save them as PDF via the browser: **Cmd+P → Save as PDF**.

> `uscis.gov`, `travel.state.gov` and `dol.gov` return **HTTP 403** to non-browser
> user agents. Download through a browser, or set a browser `User-Agent` if scripting.

---

## Tier 1 — core (start here, ~12 docs)

Orientation plus the categories people ask about most. Together with what is
already in `data/raw/`, this is enough for a working assistant.

### Orientation — the concepts everything else hangs off

| Document | URL |
|---|---|
| What is a U.S. Visa? *(immigrant vs nonimmigrant — the key distinction)* | https://travel.state.gov/content/travel/en/us-visas/visa-information-resources/frequently-asked-questions/what-is-us-visa.html |
| Directory of Visa Categories *(master list of every visa letter code)* | https://travel.state.gov/content/travel/en/us-visas/visa-information-resources/all-visa-categories.html |
| Green Card Eligibility Categories *(every path to a green card)* | https://www.uscis.gov/green-card/green-card-eligibility-categories |
| Working in the United States *(work authorization overview)* | https://www.uscis.gov/working-in-the-united-states |
| Temporary (Nonimmigrant) Workers | https://www.uscis.gov/working-in-the-united-states/temporary-nonimmigrant-workers |

### The two routes — adjustment of status vs consular processing

| Document | URL |
|---|---|
| Green Card Processes and Procedures *(defines the fork)* | https://www.uscis.gov/green-card/green-card-processes-and-procedures |
| Adjustment of Status *(in-country, Form I-485)* | https://www.uscis.gov/green-card/green-card-processes-and-procedures/adjustment-of-status |
| Consular Processing *(from abroad)* | https://www.uscis.gov/green-card/green-card-processes-and-procedures/consular-processing |

### Most-asked categories

| Document | URL |
|---|---|
| H-1B Specialty Occupations | https://www.uscis.gov/working-in-the-united-states/h-1b-specialty-occupations |
| O-1 Extraordinary Ability or Achievement | https://www.uscis.gov/working-in-the-united-states/temporary-workers/o-1-visa-individuals-with-extraordinary-ability-or-achievement |
| Employment-Based Immigration: First Preference EB-1 | https://www.uscis.gov/working-in-the-united-states/permanent-workers/employment-based-immigration-first-preference-eb-1 |
| Employment-Based Immigration: Second Preference EB-2 *(incl. NIW)* | https://www.uscis.gov/working-in-the-united-states/permanent-workers/employment-based-immigration-second-preference-eb-2 |

---

## Tier 2 — breadth (add once the pipeline works)

### Remaining employment-based immigrant categories

| Document | URL |
|---|---|
| Employment-Based Immigration: Fourth Preference EB-4 | https://www.uscis.gov/working-in-the-united-states/permanent-workers/employment-based-immigration-fourth-preference-eb-4 |
| EB-5 Immigrant Investor Program | https://www.uscis.gov/working-in-the-united-states/permanent-workers/eb-5-immigrant-investor-program |

### Remaining temporary work visas

| Document | URL |
|---|---|
| L-1A Intracompany Transferee Executive or Manager | https://www.uscis.gov/working-in-the-united-states/temporary-workers/l-1a-intracompany-transferee-executive-or-manager |
| L-1B Intracompany Transferee Specialized Knowledge | https://www.uscis.gov/working-in-the-united-states/temporary-workers/l-1b-intracompany-transferee-specialized-knowledge |
| TN USMCA Professionals | https://www.uscis.gov/working-in-the-united-states/temporary-workers/tn-usmca-professionals |
| E-2 Treaty Investors | https://www.uscis.gov/working-in-the-united-states/temporary-workers/e-2-treaty-investors |
| E-1 Treaty Traders | https://www.uscis.gov/working-in-the-united-states/temporary-workers/e-1-treaty-traders |

### Study, exchange, visit

| Document | URL |
|---|---|
| Student Visa (F and M) | https://travel.state.gov/content/travel/en/us-visas/study/student-visa.html |
| Optional Practical Training (OPT) for F-1 Students | https://www.uscis.gov/working-in-the-united-states/students-and-exchange-visitors/optional-practical-training-opt-for-f-1-students |
| STEM OPT Extension | https://www.uscis.gov/working-in-the-united-states/students-and-exchange-visitors/optional-practical-training-extension-for-stem-students-stem-opt |
| Students and Employment | https://www.uscis.gov/working-in-the-united-states/students-and-exchange-visitors/students-and-employment |
| Exchange Visitor Visa (J) | https://travel.state.gov/content/travel/en/us-visas/study/exchange.html |
| J-1 Two-Year Home-Country Requirement — 212(e) waiver | https://travel.state.gov/content/travel/en/us-visas/study/exchange/waiver-of-the-exchange-visitor.html |
| Visitor Visa (B-1 business / B-2 tourism) | https://travel.state.gov/content/travel/en/us-visas/tourism-visit/visitor.html |

### Family & lottery

| Document | URL |
|---|---|
| Green Card for Immediate Relatives of U.S. Citizen | https://www.uscis.gov/green-card/green-card-eligibility/green-card-for-immediate-relatives-of-us-citizen |
| Green Card for Family Preference Immigrants | https://www.uscis.gov/green-card/green-card-eligibility/green-card-for-family-preference-immigrants |
| Diversity Visa Instructions | https://travel.state.gov/content/travel/en/us-visas/immigrate/diversity-visa-program-entry/diversity-visa-instructions.html |
| DV-2026 Plain Language Instructions and FAQs *(already a PDF)* | https://travel.state.gov/content/dam/visas/Diversity-Visa/DV-Instructions-Translations/DV-2026-Instructions-Translations/DV%202026%20Plain%20Language%20Instructions%20and%20FAQs.pdf |

---

## Tier 3 — depth (only if a specific question needs it)

Dense legal/policy text. Good for precise grounding, heavy for a first corpus.

| Document | URL |
|---|---|
| Policy Manual 6-F-2 — Extraordinary Ability (EB-1A) | https://www.uscis.gov/policy-manual/volume-6-part-f-chapter-2 |
| Policy Manual 6-F-3 — Outstanding Professor or Researcher (EB-1B) | https://www.uscis.gov/policy-manual/volume-6-part-f-chapter-3 |
| Policy Manual 6-F-4 — Multinational Executive or Manager (EB-1C) | https://www.uscis.gov/policy-manual/volume-6-part-f-chapter-4 |
| Policy Manual 6-F-5 — Advanced Degree or Exceptional Ability (EB-2) | https://www.uscis.gov/policy-manual/volume-6-part-f-chapter-5 |
| Immigrant Visa Process — 12-step consular spine | https://travel.state.gov/content/travel/en/us-visas/immigrate/the-immigrant-visa-process/step-1-submit-a-petition.html |
| H-1B Cap Season | https://www.uscis.gov/working-in-the-united-states/temporary-workers/h-1b-specialty-occupations/h-1b-cap-season |
| H-1B Electronic Registration Process | https://www.uscis.gov/working-in-the-united-states/temporary-workers/h-1b-specialty-occupations/h-1b-electronic-registration-process |
| B-1 Business Visa Fact Sheet | https://travel.state.gov/content/travel/en/us-visas/business/b-1-fact-sheet.html |
| E-1/E-2 Treaty Countries list | https://travel.state.gov/content/travel/en/us-visas/visa-information-resources/fees/treaty.html |
| Temporary Worker Visas (DOS view) | https://travel.state.gov/content/travel/en/us-visas/employment/temporary-worker-visas.html |
| USMCA Professional Workers (DOS view) | https://travel.state.gov/content/travel/en/us-visas/employment/visas-canadian-mexican-usmca-professional-workers.html |
| Treaty Trader / Treaty Investor (DOS view) | https://travel.state.gov/content/travel/en/us-visas/employment/treaty-trader-investor-visa-e.html |
| U.S. Visas — DOS landing page | https://travel.state.gov/content/travel/en/us-visas.html |
| J-1 waiver eligibility detail | https://travel.state.gov/content/travel/en/us-visas/study/exchange/waiver-of-the-exchange-visitor/eligibility.html |
| Diversity Visa Program — Submit an Entry | https://travel.state.gov/content/travel/en/us-visas/immigrate/diversity-visa-program-entry/diversity-visa-submit-entry1.html |
