from utils.logger import get_logger

log = get_logger("logic")

def should_keep_egg(scan: dict, species: str, sex: str, config):
    """
    Decide whether to keep or destroy an egg based on modes, stats, and progress.
    Returns (keep: bool, reasons: dict).
    """
    rules = config.rules.get(species, {})
    prog  = config.progress.get(species, {})
    modes = rules.get("modes", [])
    reasons = {}

    # 1) MUTATIONS (male-only)
    if "mutations" in modes and sex == "male":
        muts = rules.get("mut_stats") or rules.get("mutation_stats", [])
        reasons.setdefault("_debug", {})["muts_used"] = muts
        for stat in muts:
            curr   = scan["stats"].get(stat, {}).get("mutation", 0)
            thresh = prog.get("mut_stats", {}).get(stat, 0)
            reasons["_debug"][f"mut_{stat}"] = (curr, thresh)
            if curr < thresh:
                reasons["mut_low"] = True
                break
        else:
            if muts:
                reasons["mutation_match"] = True

    # 2) ALL FEMALES
    if "all_females" in modes and sex == "female":
        reasons["auto_keep_female"] = True

    # 3) STAT MERGE (male-only)
    if "stat_merge" in modes and sex == "male":
        stats = rules.get("top_stats") or rules.get("stat_merge_stats", [])
        reasons.setdefault("_debug", {})["stat_merge_used"] = stats
        for stat in stats:
            base   = scan["stats"].get(stat, {}).get("base", 0)
            topval = prog.get("top_stats", {}).get(stat, 0)
            reasons["_debug"][f"stat_merge_{stat}"] = (base, topval)
        # if any base ≥ tracked top, keep
        if stats and any(
            scan["stats"].get(s, {}).get("base", 0) >= prog.get("top_stats", {}).get(s, 0)
            for s in stats
        ):
            reasons["new_stat_merge"] = True

    # 4) TOP STAT FEMALES
    if "top_stat_females" in modes and sex == "female":
        stats = rules.get("top_stats") or rules.get("top_stat_females_stats", [])
        reasons.setdefault("_debug", {})["top_females_used"] = stats
        for stat in stats:
            base   = scan["stats"].get(stat, {}).get("base", 0)
            topval = prog.get("top_stats", {}).get(stat, 0)
            reasons["_debug"][f"top_female_{stat}"] = (base, topval)
        # if all base == tracked top, keep
        if stats and all(
            scan["stats"].get(s, {}).get("base", 0) == prog.get("top_stats", {}).get(s, 0)
            for s in stats
        ):
            reasons["top_female"] = True

    # 5) WAR MODE (any sex)
    if "war" in modes:
        stats = rules.get("top_stats") or rules.get("war_stats", [])
        reasons.setdefault("_debug", {})["war_used"] = stats
        for stat in stats:
            base   = scan["stats"].get(stat, {}).get("base", 0)
            mut    = scan["stats"].get(stat, {}).get("mutation", 0)
            topval = prog.get("top_stats", {}).get(stat, 0)
            reasons["_debug"][f"war_{stat}"] = (base + mut, topval)
        # if base+mutation ≥ tracked top for all, keep
        if stats and all(
            scan["stats"].get(s, {}).get("base", 0) + scan["stats"].get(s, {}).get("mutation", 0)
            >= prog.get("top_stats", {}).get(s, 0)
            for s in stats
        ):
            reasons["war_keep"] = True

    # Final decision
    keep = any(flag for flag in reasons if flag != "_debug")
    log.debug(f"Decision for {species} ({sex}): keep={keep}, reasons={reasons}")
    return keep, reasons
