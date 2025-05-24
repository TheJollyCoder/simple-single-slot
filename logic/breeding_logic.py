from utils.logger import get_logger

log = get_logger("logic")

def should_keep_egg(scan: dict, species: str, sex: str, config) -> tuple[bool,dict]:
    rules = config.rules.get(species, {})
    prog  = config.progress.get(species, {})
    modes = rules.get("modes", [])
    reasons = {}

    if "mutations" in modes and sex=="male":
        for stat in rules.get("mut_stats", []):
            if scan["stats"][stat]["mutation"] < prog.get("mut_stats",{}).get(stat,0):
                reasons["mut_low"] = True
                break
        else:
            reasons["mutation_match"] = True

    if "all_females" in modes and sex=="female":
        reasons["auto_keep_female"] = True

    if "stat_merge" in modes and sex=="male":
        studs = prog.get("stud", {}).get("stats", {})
        better = sum(1 for s,v in scan["stats"].items() if v["base"] >= studs.get(s,0))
        if better > prog.get("stud", {}).get("score", -1):
            reasons["new_stud"] = True

    if "top_stat_females" in modes and sex=="female":
        top = prog.get("top_stats", {})
        if all(scan["stats"][s]["base"] == top.get(s,0) for s in top):
            reasons["top_female"] = True

    if "war" in modes:
        top = prog.get("top_stats", {})
        if all((scan["stats"][s]["base"] + scan["stats"][s]["mutation"]) >= v 
               for s,v in top.items()):
            reasons["war_keep"] = True

    return bool(reasons), reasons
