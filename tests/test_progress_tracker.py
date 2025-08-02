import os
import sys
import json
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import progress_tracker

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


def test_update_stud_updates_top_stats_and_history():
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
    with patch('progress_tracker.normalize_species_name', return_value='Rex'), \
         patch('progress_tracker.record_history') as rec:
        updated = progress_tracker.update_stud('egg', stats, config, progress, 'wipe1')
    assert updated is True
    assert progress['Rex']['stud']['melee'] == 6
    assert progress['Rex']['top_stats']['melee'] == 6
    rec.assert_called_once_with('Rex', 'top_stats', 'melee', 6, 'wipe1')


def test_update_stud_replaces_top_stats():
    progress = {
        'Rex': {
            'top_stats': {'melee': 5, 'health': 10},
            'stud': {'melee': 5, 'health': 10},
            'mutation_thresholds': {},
            'mutation_stud': {},
            'female_count': 0
        }
    }
    config = {'stat_merge_stats': ['melee']}
    stats = {'melee': {'base': 7}}
    with patch('progress_tracker.normalize_species_name', return_value='Rex'), \
         patch('progress_tracker.record_history'):
        updated = progress_tracker.update_stud('egg', stats, config, progress, 'wipe1')
    assert updated is True
    assert progress['Rex']['top_stats'] == {'melee': 7}


def test_apply_automated_modes_low_count():
    modes = progress_tracker.apply_automated_modes(10, {'automated'})
    assert modes == {'automated', 'mutations', 'stat_merge', 'all_females'}


def test_apply_automated_modes_mid_count():
    modes = progress_tracker.apply_automated_modes(50, {'all_females', 'automated'})
    assert modes == {'automated', 'mutations', 'stat_merge', 'top_stat_females'}


def test_apply_automated_modes_high_count():
    modes = progress_tracker.apply_automated_modes(120, {'all_females', 'top_stat_females', 'automated'})
    assert modes == {'mutations', 'stat_merge'}


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
