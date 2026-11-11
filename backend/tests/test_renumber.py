import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.services.rag import renumber  # noqa: E402


def test_markers_follow_order_of_first_use():
    assert renumber("Fee is Rs 30,000 [5]. Starts 17 Aug [1], [5].", 5) == ("Fee is Rs 30,000 [1]. Starts 17 Aug [2], [1].", [5, 1])


def test_out_of_range_markers_dropped():
    assert renumber("Yes [9] and [0] and [2].", 5) == ("Yes  and  and [1].", [2])


def test_no_markers():
    assert renumber("I only have Peshawar information.", 5) == ("I only have Peshawar information.", [])
