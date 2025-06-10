# Automated Mode Overview

This document outlines how the repository currently adjusts breeding rules when
`automated` mode is enabled and proposes consolidating that logic.

## Current Workflow

1. **Scanning** – `edit_settings.py` or the Script Control tab launch a loop that
   calls `scanner.scan_slot()` to OCR an egg. The result is passed to
   `breeding_logic.should_keep_egg` for a keep/destroy decision.
2. **Decision Logic** – `should_keep_egg` evaluates rules for the species. When
   `automated` is in the `modes` list, the function enables or disables other
   modes based on the female count recorded in breeding progress.
3. **Progress Updates** – If a female egg is kept, `increment_female_count`
   records it and `adjust_rules_for_females` may rewrite `rules.json` so the
   active modes evolve over time.
4. **Saving** – Updated progress and rules are saved to disk to persist the
   state between sessions.

The automation thresholds are duplicated in two places:

- In `breeding_logic.should_keep_egg` when computing `enabled` modes
  dynamically.
- In `progress_tracker.adjust_rules_for_females` when persisting changes to the
  configuration.

Relevant excerpt from `adjust_rules_for_females`:

```python
if "automated" in modes:
    if count < 30:
        modes.update({"mutations", "stat_merge", "all_females"})
        modes.discard("top_stat_females")
    elif count < 96:
        modes.update({"mutations", "stat_merge", "top_stat_females"})
        modes.discard("all_females")
    else:
        modes.update({"mutations", "stat_merge"})
        modes.discard("all_females")
        modes.discard("top_stat_females")
        modes.discard("automated")
```

The same ranges appear in the runtime logic inside
`breeding_logic.should_keep_egg`.

## Consolidating Policy

Issue 2 introduces a helper that computes the effective modes for a species
based on its female count. Using that helper everywhere avoids keeping two
implementations in sync. The proposal is:

1. **Single Policy Layer** – Move the threshold logic into a helper
   `compute_automated_modes(base_modes, female_count)` (from Issue 2).
2. **Runtime Adjustment** – `breeding_logic.should_keep_egg` calls the helper to
   obtain the adjusted mode set before evaluating any rules.
3. **Persistent Rules?** – Decide whether to continue rewriting `rules.json`
   through `adjust_rules_for_females` or rely solely on the runtime helper. A
   lighter approach is to leave the JSON unchanged and only compute modes at
   runtime, keeping progress data as the sole driver of automation.

## Migration Steps

1. **Add the helper** from Issue 2 into `progress_tracker.py` (or a new
   module).
2. **Refactor `should_keep_egg`** to call the helper instead of duplicating the
   threshold logic.
3. **Update `adjust_rules_for_females`** so it also delegates to the helper.
   If persistent updates are no longer desired, this function can simply return
   the computed modes without modifying `rules.json`.
4. **Search for direct references** to `rules[species]['modes']` in the codebase
   and replace manual adjustments with calls to the helper.
5. **Regenerate tests** ensuring the helper is exercised and that existing
   behaviour remains consistent.

Consolidating the policy improves maintainability and makes future changes to
automated thresholds trivial.
