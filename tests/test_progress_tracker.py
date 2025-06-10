import os
import sys
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import progress_tracker


def test_update_top_stats_records_new_value():
    progress = {}
    with patch('progress_tracker.normalize_species_name', return_value='Rex'), \
         patch('progress_tracker.record_history') as rec:
        updated = progress_tracker.update_top_stats('egg', {'melee': {'base': 5}}, progress)
    assert updated is True
    assert progress['Rex']['top_stats']['melee'] == 5
    rec.assert_called_once_with('Rex', 'top_stats', 'melee', 5)


def test_update_top_stats_no_change():
    progress = {'Rex': {'top_stats': {'melee': 5}, 'mutation_thresholds': {}, 'stud': {}, 'female_count': 0}}
    with patch('progress_tracker.normalize_species_name', return_value='Rex'), \
         patch('progress_tracker.record_history') as rec:
        updated = progress_tracker.update_top_stats('egg', {'melee': {'base': 4}}, progress)
    assert updated is False
    assert progress['Rex']['top_stats']['melee'] == 5
    rec.assert_not_called()


def test_increment_female_count_when_female():
    progress = {}
    with patch('progress_tracker.normalize_species_name', return_value='Rex'):
        count = progress_tracker.increment_female_count('egg', progress, 'female')
    assert count == 1
    assert progress['Rex']['female_count'] == 1


def test_increment_female_count_when_not_female():
    progress = {}
    with patch('progress_tracker.normalize_species_name', return_value='Rex'):
        count = progress_tracker.increment_female_count('egg', progress, 'male')
    assert count == 0
    assert progress == {}


def test_adjust_rules_for_females_new_species_with_template():
    progress = {}
    rules = {}
    template = {"modes": []}
    with patch('progress_tracker.log'):
        changed = progress_tracker.adjust_rules_for_females('Rex', progress, rules, template)
    assert changed is True
    assert set(rules['Rex']['modes']) == {'mutations', 'stat_merge', 'all_females', 'automated'}


def test_adjust_rules_for_females_medium_count():
    progress = {'Rex': {'female_count': 50}}
    rules = {'Rex': {'modes': ['all_females', 'automated']}}
    with patch('progress_tracker.log'):
        changed = progress_tracker.adjust_rules_for_females('Rex', progress, rules)
    assert changed is True
    assert set(rules['Rex']['modes']) == {'mutations', 'stat_merge', 'top_stat_females', 'automated'}


def test_adjust_rules_for_females_high_count():
    progress = {'Rex': {'female_count': 150}}
    rules = {'Rex': {'modes': ['all_females', 'top_stat_females', 'automated']}}
    with patch('progress_tracker.log'):
        changed = progress_tracker.adjust_rules_for_females('Rex', progress, rules)
    assert changed is True
    assert set(rules['Rex']['modes']) == {'mutations', 'stat_merge'}


def test_update_mutation_stud_updates_value():
    progress = {
        'Rex': {
            'mutation_thresholds': {'melee': 2},
            'mutation_stud': {'melee': 5}
        }
    }
    config = {'mutation_stats': ['melee']}
    stats = {'melee': {'mutation': 2, 'base': 6}}
    with patch('progress_tracker.normalize_species_name', return_value='Rex'):
        updated = progress_tracker.update_mutation_stud('egg', stats, config, progress)
    assert updated is True
    assert progress['Rex']['mutation_stud']['melee'] == 6


def test_apply_automated_modes_low_count():
    result = progress_tracker.apply_automated_modes(10, {'automated'})
    assert result == {'automated', 'mutations', 'stat_merge', 'all_females'}


def test_apply_automated_modes_mid_count():
    result = progress_tracker.apply_automated_modes(50, {'automated', 'all_females'})
    assert result == {'automated', 'mutations', 'stat_merge', 'top_stat_females'}


def test_apply_automated_modes_high_count():
    result = progress_tracker.apply_automated_modes(150, {'automated', 'all_females', 'top_stat_females'})
    assert result == {'mutations', 'stat_merge'}
