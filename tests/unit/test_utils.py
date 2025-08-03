import pytest
from autonomous_research.utils.loop_detector import LoopDetector

def test_loop_detector_basic():
    ld = LoopDetector(history_size=2, repeat_threshold=2)
    ld.add_item('a')
    ld.add_item('a')
    assert ld.is_looping('a')
    ld.add_item('b')
    assert not ld.is_looping('b')

def test_loop_detector_history_size():
    ld = LoopDetector(history_size=2)
    ld.add_item('x')
    ld.add_item('y')
    ld.add_item('z')
    assert ld.get_recent_history() == ['y', 'z']
