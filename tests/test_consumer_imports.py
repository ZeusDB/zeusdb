"""
The import forms the shipped integration packages use, reproduced exactly.

Two published packages depend on `zeusdb` and reach into it only through the
forms below. Neither contains the string `zeusdb_vector_database` anywhere, so
this package is their entire runtime surface.

    langchain-zeusdb                    langchain_zeusdb/vectorstores.py
    llama-index-vector-stores-zeusdb    llama_index/vector_stores/zeusdb/base.py

A change here that breaks one of those forms breaks a published package at
import. These tests exist so it fails here first.
"""

import logging

import pytest


def test_langchain_zeusdb_imports_vector_database():
    """langchain-zeusdb, vectorstores.py lines 1327, 1637 and 1877."""
    from zeusdb import VectorDatabase  # Use mega package

    assert isinstance(VectorDatabase, type)


def test_llama_index_zeusdb_imports_vector_database():
    """llama-index-vector-stores-zeusdb, base.py line 23.

    Module level, under the comment "ZeusDB runtime (umbrella package only)".
    The adapter does not import at all when this fails.
    """
    from zeusdb import VectorDatabase  # type: ignore

    assert isinstance(VectorDatabase, type)


def test_langchain_zeusdb_imports_logging_helpers():
    """langchain-zeusdb, vectorstores.py lines 61 and 62.

    Two separate `from zeusdb.logging_config import` statements inside one try,
    so either name missing sends the adapter to its fallback.
    """
    from zeusdb.logging_config import get_logger as _get_logger
    from zeusdb.logging_config import operation_context as _operation_context

    assert callable(_get_logger)
    assert callable(_operation_context)


def test_llama_index_zeusdb_imports_logging_helpers():
    """llama-index-vector-stores-zeusdb, base.py lines 32 to 37."""
    from zeusdb.logging_config import (
        get_logger as _get_logger,
    )
    from zeusdb.logging_config import (
        operation_context as _operation_context,
    )

    assert callable(_get_logger)
    assert callable(_operation_context)


def test_logger_accepts_the_structured_fields_both_adapters_pass():
    """Both adapters log with arbitrary keyword fields.

    For example `logger.warning("Empty embedding received", operation=where)`
    at langchain-zeusdb vectorstores.py line 453. A plain `logging.Logger`
    raises `TypeError: Logger._log() got an unexpected keyword argument
    'operation'` on that call, which is why `get_logger` here returns an
    adapter rather than forwarding the dependency's logger unchanged.
    """
    from zeusdb.logging_config import get_logger

    logger = get_logger("langchain_zeusdb")
    logger.warning("Empty embedding received", operation="add_texts")
    logger.debug("translated_filters", zeusdb_filter={"kind": "web"})
    logger.info("Index cleared", operation="clear_index")
    logger.error("failed", operation="query", error="boom", exc_info=False)


def test_structured_fields_reach_the_log_record(caplog):
    """The keyword fields arrive as record attributes rather than being lost."""
    from zeusdb.logging_config import get_logger

    logger = get_logger("langchain_zeusdb")
    with caplog.at_level(logging.WARNING, logger="zeusdb.vector.langchain_zeusdb"):
        logger.warning("Empty embedding received", operation="add_texts")

    assert len(caplog.records) == 1
    assert caplog.records[0].operation == "add_texts"


def test_operation_context_wraps_a_successful_block():
    """Both adapters use it as `with operation_context(name, **fields):`."""
    from zeusdb.logging_config import operation_context

    with operation_context("add_texts", text_count=3):
        pass


def test_operation_context_reraises_and_logs_a_failure(caplog):
    """A failing block logs an error carrying the duration, then re-raises."""
    from zeusdb.logging_config import operation_context

    with (
        caplog.at_level(logging.ERROR, logger="zeusdb.vector"),
        pytest.raises(ValueError, match="boom"),
        operation_context("query", has_embedding=True),
    ):
        raise ValueError("boom")

    assert len(caplog.records) == 1
    record = caplog.records[0]
    assert record.operation == "query"
    assert record.has_embedding is True
    assert isinstance(record.duration_ms, float)


@pytest.mark.parametrize(
    "operation_name, context",
    [
        # langchain-zeusdb call sites.
        ("add_texts", {"text_count": 3}),
        ("add_documents", {"doc_count": 2}),
        ("similarity_search_with_score", {"top_k": 4}),
        ("similarity_search_by_vector", {"top_k": 4}),
        ("mmr_search", {"top_k": 4, "fetch_k": 20}),
        ("mmr_search_by_vector", {"top_k": 4, "fetch_k": 20}),
        # llama-index-vector-stores-zeusdb call sites.
        ("create_index", {"space": "cosine"}),
        ("delete_nodes", {"node_ids_count": 2}),
        ("clear_index", {}),
        ("query", {"has_embedding": True}),
        ("persist_index", {"path": "index.zdb"}),
        ("load_index", {"path": "index.zdb"}),
    ],
)
def test_every_operation_context_call_site_in_both_adapters(operation_name, context):
    """The exact field names both adapters pass.

    A field named after a `logging.LogRecord` attribute raises `KeyError` when
    it reaches the record, so the names matter and not just the shape.
    """
    from zeusdb.logging_config import operation_context

    with operation_context(operation_name, **context):
        pass
