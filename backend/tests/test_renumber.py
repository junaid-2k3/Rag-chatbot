import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.services.rag import _pdf_title, _source, renumber  # noqa: E402

DISTINCT = ["a", "b", "c", "d", "e"]


def test_markers_follow_order_of_first_use():
    assert renumber("Fee is Rs 30,000 [5]. Starts 17 Aug [1], [5].", DISTINCT) == ("Fee is Rs 30,000 [1]. Starts 17 Aug [2], [1].", [5, 1])


def test_out_of_range_markers_dropped():
    assert renumber("Yes [9] and [0] and [2].", DISTINCT) == ("Yes  and  and [1].", [2])


def test_no_markers():
    assert renumber("I only have Peshawar information.", DISTINCT) == ("I only have Peshawar information.", [])


def test_chunks_of_one_page_share_one_source_number():
    keys = ["x", "x", "y"]  # hits 1 and 2 come from the same URL
    assert renumber("A [1] B [2] C [3], [2].", keys) == ("A [1] B [1] C [2], [1].", [1, 3])


def test_adjacent_duplicate_markers_collapse():
    assert renumber("Rules [1], [2], [3].", ["x", "x", "x"]) == ("Rules [1].", [1])


def test_pdf_title_from_filename_not_hash():
    assert _pdf_title("https://pwr.nu.edu.pk/downloads/hostel-rules-v5.1.pdf") == "hostel rules v5.1"
    assert _pdf_title("https://pwr.nu.edu.pk/downloads/S03_hostel_form_2026.pdf") == "S03 hostel form 2026"
    chunk = {"source_type": "pdf", "title": "9fb90f1cde198439", "heading_path": "Page 1", "url": "https://pwr.nu.edu.pk/downloads/hostel-rules-v5.1.pdf", "page": 1, "score": 0.7}
    assert _source(chunk)["title"] == "hostel rules v5.1"


def test_generic_web_title_falls_back_to_heading():
    chunk = {"source_type": "html", "title": "FAST - NUCES Peshawar", "heading_path": "Fee Structure > Admission Fee", "url": "u", "page": None, "score": 0.7}
    assert _source(chunk)["title"] == "Fee Structure"
