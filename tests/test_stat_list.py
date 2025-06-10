import stat_list


def test_generate_stat_list_full():
    progress = {
        "Dodo": {"stud": {"health": 10}, "mutation_thresholds": {"health": 1}}
    }
    settings = {"stat_list_mode": "full"}
    lines = stat_list.generate_stat_list(progress, {}, settings)
    assert lines == ["10+1H Dodo"]


def test_generate_stat_list_mutation():
    progress = {
        "Dodo": {
            "stud": {"health": 10, "melee": 5},
            "mutation_thresholds": {"health": 1, "melee": 2},
        }
    }
    rules = {"Dodo": {"mutation_stats": ["melee"]}}
    settings = {"stat_list_mode": "mutation"}
    lines = stat_list.generate_stat_list(progress, rules, settings)
    assert lines == ["5+2M Dodo"]


def test_generate_stat_list_mutation_fallback():
    progress = {
        "Dodo": {"stud": {"health": 10}, "mutation_thresholds": {"health": 1}}
    }
    settings = {"stat_list_mode": "mutation"}
    lines = stat_list.generate_stat_list(progress, {}, settings)
    assert lines == ["10+1H Dodo"]
