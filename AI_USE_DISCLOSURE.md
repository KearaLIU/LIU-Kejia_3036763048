# AI Use Disclosure

**Course:** ECON6067 — Individual Project
**Project:** Replication of Jegadeesh & Titman (1993) "Returns to Buying Winners and
Selling Losers" on CRSP data, 2000–2025
**Student:** LIU Kejia (3036763048)
**Date:** 2026-10-10

## Tool used

Claude Code (Anthropic), run as a coding and writing assistant in the VS Code extension,
was used throughout the project.

## How the AI was used

- **Conceptual learning.** At the start of the project I was not yet familiar with several
  technical terms and ideas — what "momentum" (relative-strength) investing actually is,
  winner-minus-loser (P10 − P1) portfolios, decile sorting, overlapping portfolio
  formation with 1/*K* rebalancing, Newey–West standard errors, the one-month skip, and
  bid–ask bounce. I used the AI's explanations and worked examples to learn these
  concepts, and only moved on once I could restate each idea in my own words and connect
  it back to Jegadeesh & Titman (1993).

- **Analysis code.** Drafting and debugging the pipeline (`code/00`–`06`): the momentum
  engine (past-*J*-month compound returns, decile formation, overlapping *K*-month
  returns, Newey–West standard errors), the skip-month variant, and the two
  size-conditioned extensions.

- **Diagnosis.** Interpreting an unexpected result — the −78% winner-minus-loser return
  in January 2001 — which was traced to the momentum-crash mechanism of Daniel &
  Moskowitz (2016) rather than to a data error, and annotating the relevant figure.

- **Writing.** Drafting the README. For the README in particular, the AI drafted the
  structure and text — what the project does, the method in brief, the results at a
  glance, the repository layout, the data and licensing notes, the environment, the
  "how to reproduce" instructions, the per-script descriptions, and the reusable-skill
  pointer — which I then reviewed, corrected, and finalised.

## Overview

I used AI tools to assist with data cleaning, code writing, results analysis, and report
drafting. All data choices, methodological decisions, verification checks, interpretation
of results, and conclusions, however, are my own responsibility. The sections below
describe how I checked the AI-generated code, analysis, and writing, and the important AI
errors or suggestions that I corrected or rejected.

## 1. How I checked the AI-generated code

I did not take the AI-generated code on trust; I verified it item by item in the following
ways:

- **Recomputing key results.** I selected a sample of stocks and months and manually
  computed monthly returns, trailing-6-month cumulative returns, decile assignment, and
  holding-period returns from the raw data, then compared them with `monthly_panel.parquet`
  and `momentum_deciles.parquet`. For example, I randomly picked three stocks, manually
  compounded their daily returns into monthly returns, computed their trailing-6-month
  cumulative returns, and confirmed that the AI's compounding logic and decile assignment
  matched my manual calculation.

- **Logic review and questioning.** I read every function the AI generated carefully and
  raised questions about the key logic. For example, I checked how `past_return` handles
  missing values and confirmed that months missing within the formation window are indeed
  excluded from ranking; I also checked that `overlapping_decile_returns` correctly
  averages the overlapping portfolios with 1/*K* weights. Where I did not understand a
  part, I asked the AI to explain its implementation and cross-checked it against the
  method described in Jegadeesh & Titman (1993).

- **Boundary-condition checks.** I checked how stocks with a −100% return and how suspended
  and delisted stocks are handled. The AI floors formation-period returns below −100%
  (`np.clip(R, -0.999, None)`); I confirmed that this is only to prevent negative gross
  returns in the compounding step and that it affects the ranking signal alone, leaving
  holding-period returns unchanged.

- **Cross-validation.** I compared the sample size with the raw CRSP file and confirmed
  that the final panel contains 1,566,495 stock-month observations, 15,665 stocks, and 312
  months, consistent with the screening criteria.

## 2. How I checked the AI-generated analysis

- **Statistical significance.** The AI initially described the 6/6 strategy's
  winner-minus-loser return (0.52%/month, *t* = 1.10) as "marginally significant." By
  standard statistical judgment, *t* = 1.10 is far below the 10% significance threshold
  (|*t*| > 1.65), so I corrected it to "not statistically significant at conventional
  levels" and revised the wording in the summary and conclusion accordingly.

- **Economic logic and comparison with the literature.** I compared the AI's extension
  results with the classic literature. The AI initially proposed defining firm size with
  equal-count groups, which yielded the weakest momentum among small caps (0.37%),
  contradicting the classic finding that small-cap momentum is stronger. Reasoning it
  through, I realized that CRSP is dominated by micro-cap stocks, so an equal-count "Small"
  group would consist almost entirely of micro-caps and would be contaminated by bid–ask
  bounce. I therefore rejected that approach and re-grouped by NYSE market-capitalization
  30%/70% breakpoints, obtaining more reasonable results (small 0.48%, mid 0.65%, large
  0.50%).

- **Questioning and challenging.** For every conclusion the AI produced, I asked whether
  the result was reasonable, whether its direction matched the original paper, and whether
  there were alternative explanations. For example, when the AI attributed the stronger
  momentum to the removal of bid–ask bounce, I inspected the skip-month implementation
  further and confirmed that it indeed leaves one month idle between formation and holding
  before accepting that interpretation.

## 3. How I checked the AI-generated writing

- **Fact-checking.** I checked every number in the report against the CSV files in
  `outputs/tables/`, ensuring that the values in Tables 1–5 match exactly.

- **Citation checking.** I verified the references, confirming that the journal, volume,
  and page numbers for Daniel & Moskowitz (2016), Fama & French (1993), and Jegadeesh &
  Titman (1993) are correct.

- **Format and typo correction.** I found that an early AI draft of the report wrote the
  course code as "ENCO6067" and corrected it to "ECON6067." I also fixed the messy table
  formatting and the inconsistency in the figure filenames (e.g. the space in
  `fig3_cumulative_wml.png`).

## 4. Important AI errors I corrected or rejected

- **Misleading significance wording.** The AI described a return difference with *t* = 1.10
  as "marginally significant." I corrected it to "not statistically significant" to avoid
  overstating the result.

- **Inappropriate size-grouping method.** The AI initially used equal-count terciles,
  producing the misleading conclusion that small-cap momentum is weakest. I rejected this
  approach and re-grouped by NYSE breakpoints, obtaining results more consistent with the
  literature.

- **Course-code typo.** An early AI draft wrote "ENCO6067"; I corrected it to "ECON6067."

- **Incomplete output-file naming.** In the appendix the AI wrote only `output/table.csv`
  and `output/fig1…fig5.png`; I listed every output filename individually to ensure
  reproducibility.

- **Missing delisting-bias disclosure.** The AI did not mention in the report that
  delisting returns are not handled. I added the following: because delisting returns
  (DLRET) are not merged, the large negative returns of delisted stocks (especially
  bankruptcies) are ignored, which may overstate the loser portfolio's return and compress
  the winner-minus-loser spread — a delisting bias that should be noted in the limitations.

## Statement

All AI-generated code and text were reviewed, understood, and verified by me before
inclusion. I am responsible for the final submission.
