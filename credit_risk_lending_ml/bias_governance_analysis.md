# Bias / Governance Analysis — Credit Risk Model

Even with no explicit gender or location field in `credit_applicants.csv`,
several remaining features can act as correlated proxies for protected
attributes in a real deployment:

- **`employment_type`** (salaried / self_employed / gig): gig and informal
  self-employment in India skews toward specific socioeconomic groups and
  toward women re-entering the workforce after a career break. Treating
  `gig`/`self_employed` as inherently riskier than `salaried` risks
  indirectly penalizing these groups even though the model never sees
  gender or employment-formality status directly as a protected label.
- **`monthly_income_inr`**: income correlates with geography, caste, and
  gender due to structural labor-market disparities in India, so a model
  that penalizes low income can disproportionately reject applicants from
  historically disadvantaged groups.
- **`credit_bureau_score`**: bureau scores themselves reflect *access* to
  formal credit history, which is unevenly distributed (urban vs. rural,
  gender gaps in account ownership) — a low or missing score often
  reflects exclusion from the formal system rather than true
  creditworthiness, which is exactly why `is_thin_file` applicants (20%
  of this dataset) need separate handling rather than an unfavorable
  imputed default treatment.

None of this is *direct* discrimination (no protected attribute is used),
but it can still produce **disparate impact** — systematically worse
approval odds or pricing for groups correlated with low income, informal
employment, or thin credit files.

**Governance recommendation:** mandatory human (maker-checker) review for
any `is_thin_file=1` applicant before a decline or a high-risk-tier
pricing decision is finalized, since their bureau score is imputed
(training-median) rather than observed, not model-predicted from real
signal. This keeps the model as a decision *aid* rather than a sole
decision-maker for the population most exposed to proxy-driven error, and
should be paired with periodic monitoring of approval/pricing outcomes by
employment type and income band (as observable proxies) even though those
are not protected attributes themselves.
