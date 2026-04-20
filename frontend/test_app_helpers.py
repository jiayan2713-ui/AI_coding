from app import escape_html, format_confidence, format_document_summary, get_scope_label


def test_format_document_summary_uses_filename_and_chunk_count():
    assert (
        format_document_summary({"filename": "handbook.pdf", "chunks_count": 12})
        == "handbook.pdf · 12 个片段"
    )


def test_get_scope_label_shows_hit_state():
    assert get_scope_label(True) == "已命中文档范围"
    assert get_scope_label(False) == "未命中文档范围"


def test_format_confidence_as_percentage():
    assert format_confidence(0.8732) == "87.32%"


def test_escape_html_handles_document_content():
    assert escape_html('<script>alert("x")</script>') == "&lt;script&gt;alert(&quot;x&quot;)&lt;/script&gt;"
