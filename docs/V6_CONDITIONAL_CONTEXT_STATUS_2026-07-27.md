# v6 Conditional Context Status

Run: v6_foundation_candidate_20260727_corrected

The conditional revenue-band table now contains:

- 17,785 revenue-band context rows
- 5,531 peer groups
- 9,488 rows below the preferred scoreable-peer threshold

Rows below the minimum threshold remain stored for audit and future data
improvement, but must not be displayed as standalone numeric comparisons.

Organizations without usable revenue are not assigned a revenue band. The
future profile should show the available conditional bands for the same NTEE,
geography, and archetype cohort, with peer counts, source years, confidence,
and limitations.

No API or frontend activation has occurred.
