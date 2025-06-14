from logger import get_logger
log = get_logger("breeding_logic")
kept_log = get_logger("kept_eggs")
destroyed_log = get_logger("destroyed_eggs")

from progress_tracker import normalize_species_name, apply_automated_modes

def should_keep_egg(scan, rules, progress):
    egg = scan["egg"]
    stats = scan["stats"]
    sex = scan["sex"]
    species = normalize_species_name(egg)

    log.debug(f"Evaluating egg: {egg} ({sex})")

    # ─── CATCH GARBAGE SPECIES NAMES ──────────────────────────────
    # require "CS" and either "male" or "female" in the raw OCR
    sl = egg.lower()
    if "cs" not in sl or not ("male" in sl or "female" in sl):
        result = {
            "mutations": False,
            "all_females": False,
            "stat_merge": False,
            "top_stat_females": False,
            "war": False,
            "_debug": {
                "invalid_species": "name did not contain CS and male/female",
                "final": "rescan"
            }
        }
        log.error(f"Invalid OCR for egg species: {egg!r}. Triggering rescan.")
        return "rescan", result

    # determine effective modes, accounting for automated logic
    enabled = set(rules.get("modes", []))
    # mutations and stat_merge are always active
    enabled.update({"mutations", "stat_merge"})
    count = progress.get(species, {}).get("female_count", 0)
    enabled = apply_automated_modes(count, enabled)

    # ─── AUTO-DESTROY FEMALES WHEN NO FEMALE-MODES ENABLED ────────
    female_modes = {"all_females", "top_stat_females", "war"}
    if sex == "female" and not (female_modes & enabled):
        result = {
            "mutations": False,
            "all_females": False,
            "stat_merge": False,
            "top_stat_females": False,
            "war": False,
            "_debug": {
                "auto_destroy": "no female modes enabled",
                "final": "destroy"
            }
        }
        destroyed_log.info(f"Egg {egg} DESTROYED | reason: no female modes enabled")
        return "destroy", result

    result = {
        "mutations": False,
        "all_females": False,
        "stat_merge": False,
        "top_stat_females": False,
        "war": False,
        "_debug": {}
    }

    # ─── Mutations ─────────────────────────────────────────
    if "mutations" in enabled and sex == "male":
        log.debug("Evaluating mutations rule")

        tracked = rules.get("mutation_stats", [])
        old_thresh = progress.get(species, {}).get("mutation_thresholds", {})
        # default any missing stats to 0
        thresholds = {st: old_thresh.get(st, 0) for st in tracked}

        all_ok = True
        any_strict = False
        better_base = False
        reasons = []

        for st in tracked:
            egg_mut = stats.get(st, {}).get("mutation", 0)
            th = thresholds[st]

            # require at least your old threshold even if no new mutation
            if egg_mut < th:
                all_ok = False
                reasons.append(f"{st}={egg_mut}<{th}")
            elif egg_mut > th:
                any_strict = True
                reasons.append(f"{st}={egg_mut}>{th}")
            else:
                stud_base = progress.get(species, {}).get("mutation_stud", {}).get(st, 0)
                egg_base = stats.get(st, {}).get("base", 0)
                if egg_base > stud_base:
                    better_base = True
                reasons.append(f"{st}={egg_mut}={th}")

        if all_ok and (any_strict or better_base):
            result["mutations"] = True
            result["_debug"]["mutations"] = " | ".join(reasons)
        else:
            result["_debug"]["mutations"] = f"❌ not qualified: {' | '.join(reasons)}"

    # ─── All Females ──────────────────────────────────────────────
    if "all_females" in enabled and sex == "female":
        log.debug("Evaluating all_females rule")
        result["all_females"] = True
        result["_debug"]["all_females"] = "female"

    # ─── Stat Merge ──────────────────────────────────────────────
    if "stat_merge" in enabled and sex == "male":
        log.debug("Evaluating stat_merge rule")
        if scan.get("updated_stud"):
            result["stat_merge"] = True
            result["_debug"]["stat_merge"] = "updated_stud = True"
        else:
            merge_stats = rules.get("stat_merge_stats", [])
            top = progress.get(species, {}).get("top_stats", {})
            stud = progress.get(species, {}).get("stud", {})
            match_count = sum(
                1 for stat in merge_stats
                if stats.get(stat, {}).get("base", 0) >= top.get(stat, 0)
            )
            stud_count = sum(
                1 for stat in merge_stats
                if stud.get(stat, 0) >= top.get(stat, 0)
            )
            if match_count > 0 and not stud:
                result["stat_merge"] = True
                result["_debug"]["stat_merge"] = "first valid stud"
            elif match_count > stud_count:
                result["stat_merge"] = True
                result["_debug"]["stat_merge"] = f"{match_count}>{stud_count}"
            elif match_count == stud_count and match_count > 0:
                for stat in merge_stats:
                    base = stats.get(stat, {}).get("base", 0)
                    if base > stud.get(stat, 0):
                        result["stat_merge"] = True
                        result["_debug"]["stat_merge"] = f"{stat} base {base}>{stud.get(stat, 0)}"
                        break

    # ─── Top Stat Females ────────────────────────────────────────
    if "top_stat_females" in enabled and sex == "female":
        log.debug(f"RAW STATS passed into logic: {stats}")
        log.debug("Evaluating top_stat_females rule")
        top = progress.get(species, {}).get("top_stats", {})
        required = rules.get("top_stat_females_stats", [])
        mismatched = []
        match = True
        for stat in required:
            top_val = top.get(stat, -999)
            base_val = stats.get(stat, {}).get("base", 0)
            if base_val != top_val:
                match = False
                mismatched.append(f"{stat}={base_val}≠{top_val}")
        if match:
            result["top_stat_females"] = True
            result["_debug"]["top_stat_females"] = "all matched"
        else:
            result["_debug"]["top_stat_females"] = f"mismatched: {', '.join(mismatched)}"

    # ─── War Tames ───────────────────────────────────────────────
    if "war" in enabled:
        log.debug("Evaluating war rule")
        top = progress.get(species, {}).get("top_stats", {})
        tracked = rules.get("war_stats", [])
        mismatch = []
        match = True
        for stat in tracked:
            base = stats.get(stat, {}).get("base", 0)
            mut = stats.get(stat, {}).get("mutation", 0)
            val = base + mut
            top_val = top.get(stat, 0)
            if val < top_val:
                mismatch.append(f"{stat}={val}<{top_val}")
                match = False
        if match:
            result["war"] = True
            result["_debug"]["war"] = "all stats≥top"
        else:
            result["_debug"]["war"] = f"below top: {', '.join(mismatch)}"

    # ─── Final decision & separate logs ──────────────────────────
    decision = "keep" if any(result[k] for k in result if k != "_debug") else "destroy"
    result["_debug"]["final"] = decision

    if decision == "keep":
        details = []
        for rule, passed in result.items():
            if rule == "_debug" or not passed:
                continue
            reason = result["_debug"].get(rule, "")
            details.append(f"{rule}: {reason}")
        kept_log.info(f"Egg {egg} KEPT | {'; '.join(details)}")
    else:
        details = [f"{k}:{v}" for k, v in result["_debug"].items() if k != "final"]
        destroyed_log.info(f"Egg {egg} DESTROYED | details: {'; '.join(details)}")

    return decision, result
