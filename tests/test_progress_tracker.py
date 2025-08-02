import os
import sys
import json
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import progress_tracker


def test_update_top_stats_records_new_value():
    progress = {}
    with patch('progress_tracker.normalize_species_name', return_value='Rex'), \
         patch('progress_tracker.record_history') as rec:
        updated = progress_tracker.update_top_stats('egg', {'melee': {'base': 5}}, progress, 'wipe1')
    assert updated is True
    assert progress['Rex']['top_stats']['melee'] == 5
    rec.assert_called_once_with('Rex', 'top_stats', 'melee', 5, 'wipe1')


def test_update_top_stats_no_change():
    progress = {'Rex': {'top_stats': {'melee': 5}, 'mutation_thresholds': {}, 'stud': {}, 'female_count': 0}}
    with patch('progress_tracker.normalize_species_name', return_value='Rex'), \
         patch('progress_tracker.record_history') as rec:
        updated = progress_tracker.update_top_stats('egg', {'melee': {'base': 4}}, progress, 'wipe1')
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
    assert set(rules['Rex']['modes']) == set()


def test_adjust_rules_for_females_high_count_war():
    progress = {'Rex': {'female_count': 150}}
    rules = {'Rex': {'modes': ['automated', 'war']}}
    with patch('progress_tracker.log'):
        changed = progress_tracker.adjust_rules_for_females('Rex', progress, rules)
    assert changed is True
    assert set(rules['Rex']['modes']) == {'war'}


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


def test_update_stud_equal_match_better_base():
    progress = {
        'Rex': {
            'top_stats': {'melee': 5},
            'stud': {'melee': 5},
            'mutation_thresholds': {},
            'mutation_stud': {},
            'female_count': 0
        }
    }
    config = {'stat_merge_stats': ['melee']}
    stats = {'melee': {'base': 6}}
    with patch('progress_tracker.normalize_species_name', return_value='Rex'), patch('progress_tracker.log'):
        updated = progress_tracker.update_stud('egg', stats, config, progress)
    assert updated is True
    assert progress['Rex']['stud']['melee'] == 6


def test_apply_automated_modes_low_count():
    modes = progress_tracker.apply_automated_modes(4, {'automated'})
    assert modes == {'automated', 'mutations', 'stat_merge', 'all_females'}


def test_apply_automated_modes_mid_count():
    modes = progress_tracker.apply_automated_modes(50, {'all_females', 'automated'})
    assert modes == {'automated', 'mutations', 'stat_merge', 'top_stat_females'}


def test_apply_automated_modes_high_count():
    modes = progress_tracker.apply_automated_modes(120, {'all_females', 'top_stat_females', 'automated'})
    assert modes == set()


def test_apply_automated_modes_high_count_war():
    modes = progress_tracker.apply_automated_modes(120, {'automated', 'war'})
    assert modes == {'war'}


def test_record_history_custom_wipe(tmp_path):
    wipe = 'custom'
    wipes_dir = tmp_path / 'wipes'
    with patch('progress_tracker.WIPE_DIR', str(wipes_dir)):
        progress_tracker.record_history('Rex', 'top_stats', 'melee', 5, wipe)
        hist_file = wipes_dir / wipe / 'progress_history.json'
        assert hist_file.exists()
        with open(hist_file, encoding='utf-8') as f:
            data = json.load(f)
        assert data['Rex']['top_stats']['melee'][0]['value'] == 5
