import pytest
from autonomous_research.utils.loop_detector import LoopDetector

def test_add_and_history():
    ld = LoopDetector(history_size=3)
    ld.add_item('a')
    ld.add_item('b')
    ld.add_item('c')
    assert ld.get_recent_history() == ['a', 'b', 'c']
    ld.add_item('d')
    assert ld.get_recent_history() == ['b', 'c', 'd']

def test_is_looping():
    ld = LoopDetector(history_size=5, repeat_threshold=2)
    ld.add_item('x')
    ld.add_item('y')
    ld.add_item('x')
    assert ld.is_looping('x') is True
    assert ld.is_looping('y') is False
    ld.add_item('y')
    ld.add_item('y')
    assert ld.is_looping('y') is True

def test_no_false_positive():
    ld = LoopDetector(history_size=4, repeat_threshold=3)
    ld.add_item('z')
    ld.add_item('z')
    assert ld.is_looping('z') is False
    ld.add_item('z')
    assert ld.is_looping('z') is True
