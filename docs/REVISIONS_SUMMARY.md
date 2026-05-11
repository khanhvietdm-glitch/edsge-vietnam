# SCIE-Q1 Revision Summary

This document summarises the additions made to the original manuscript to
bring it to a SCIE-Q1 publication standard.

## New material (all integrated into `E-DSGE_Vietnam_REVISED.docx`)

### New sections

| Section | Title | Rationale |
| --- | --- | --- |
| 7.8 | Sectoral Heterogeneity in Climate Damages | Exploits the previously underused 9-sector x 6-region calibration block. SCIE-Q1 reviewers consistently request sectoral disaggregation. |
| 7.9 | Cross-Country SCC Benchmark | Positions Vietnam's $38.7-$61.2/tCO2 range against China, India, Indonesia, Brazil, South Africa, Mexico, the US and the EU. |
| 8.4 | Transition Pathway to NDC 2030 and Net-Zero 2050 | Explicitly maps the model output onto Vietnam's stated climate commitments. |
| 10 | Replication Package and Computational Reproducibility | Open-science / FAIR statement with GitHub URL, code architecture, reproduction procedure. |
| Appendix D | Python Implementation Details | Implementation notes that complement the Dynare description in Appendix C. |

### New tables

| Table | Title |
| --- | --- |
| 13 | Cross-country social cost of carbon benchmark |
| 14 | Sectoral abatement potential at $50/tCO2 |
| 15 | Pathway snapshots at 2025 / 2030 / 2040 / 2050 |

### New figures

| Figure | Title |
| --- | --- |
| 5 | Sectoral heterogeneity in climate damages (heatmap + GVA bars) |
| 6 | Vietnam transition pathway 2025-2050 (price, emissions, temperature) |
| 7 | SCC sensitivity heatmap over ECS x d2 grid |

### Front-matter additions

* Replication notice at the very top with hyperlinked GitHub URL.
* Author Contributions block (CRediT-style).
* Funding statement.
* Data Availability Statement.
* Conflict of Interest statement.
* Acknowledgments paragraph.

## Why these changes lift the paper to SCIE-Q1

1. **Open-science compliance**: top economics journals (Energy Economics,
   Journal of Environmental Economics and Management, Resource and Energy
   Economics, Climate Policy) now require executable replication packages
   under permissive licenses. The GitHub repo addresses this directly.

2. **Sectoral disaggregation**: a frequent reviewer concern for aggregate
   E-DSGE papers is the absence of sectoral channels. Section 7.8 and
   Table 14 ground the carbon-pricing policy in sector-specific data
   without complicating the structural estimation.

3. **External validity**: cross-country benchmarking (Table 13) directly
   addresses the question "how does this SCC compare to other economies?"
   that reviewers always raise for country-specific SCC papers.

4. **Policy relevance**: connecting the Ramsey-optimal path to the NDC
   2030 and Net-Zero 2050 targets (Section 8.4 and Figure 6) makes the
   paper directly useful for Vietnamese policymakers (MOIT, MONRE, SBV)
   and shifts it from pure academic exercise toward applied policy.

5. **Reproducibility**: the 18-test pytest suite and the FAIR-aligned
   replication package guard against the "results-cannot-be-reproduced"
   criticism that has affected several recent climate-DSGE papers.

## Files added to the repository

```
docs/E-DSGE_Vietnam_REVISED.docx     - Revised manuscript (1.4 MB)
docs/REVISIONS_SUMMARY.md            - This file
scripts/build_revised_paper.py       - Generates the revised docx
scripts/generate_new_figures.py      - Generates Figures 5-7
scripts/generate_new_tables.py       - Generates Tables 13-15
results/figures/fig5_sectoral_damages.png
results/figures/fig6_transition_pathway.png
results/figures/fig7_scc_heatmap.png
results/tables/table_13_cross_country_scc.csv
results/tables/table_14_sectoral_abatement.csv
results/tables/table_15_transition_milestones.csv
```

## Suggested journals

The revised paper is well-aligned with the scope of:

| Journal | IF (2024) | SJR Q | Notes |
| --- | --- | --- | --- |
| Energy Economics | 12.8 | Q1 | Climate-macro is a core topic. |
| Resource and Energy Economics | 4.4 | Q1 | Closer to the model's structural emphasis. |
| Journal of Environmental Economics and Management | 6.4 | Q1 | SCC + welfare-based policy ranking fits perfectly. |
| Climate Policy | 7.2 | Q1 | Section 8.4 (NDC/Net-Zero pathway) particularly suits this audience. |
| Ecological Economics | 5.5 | Q1 | Sectoral / regional damage analysis. |
| Climatic Change | 5.5 | Q1 | Integrated DSGE-DICE methodology aligns. |

## Next steps recommended to authors

1. Run the replication package end-to-end on a fresh machine to verify
   bit-identical output.
2. Update bibliographic references in Section 7.9 / Table 13 with the
   final published citations for each cross-country benchmark.
3. Consider extracting Section 8.4 + Figure 6 into a separate policy brief
   for distribution to MOIT / MONRE / SBV.
4. Submit the manuscript with the GitHub URL listed under "Code and Data
   Availability" in the journal submission portal.
