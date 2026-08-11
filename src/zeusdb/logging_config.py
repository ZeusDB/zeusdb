"""
Structured logging helpers for ZeusDB and its integration packages.

This module exists because two published packages import it by name.
`langchain-zeusdb` and `llama-index-vector-stores-zeusdb` both open with

    from zeusdb.logging_config import get_logger, operation_context

and fall back to a private copy when that import fails. `from a.b import c`
resolves `a.b` through the import system rather than through a module-level
`__getattr__`, so serving those consumers needs a real file here rather than a
registry entry in `__init__.py`.

Neither name can be forwarded unchanged from `zeusdb-vector-database`.

`get_logger` there returns a plain `logging.Logger`. Both consumers call their
logger with arbitrary keyword fields, as in

    logger.warning("Empty embedding received", operation="add_texts")

and a plain `Logger` raises `TypeError: Logger._log() got an unexpected keyword
argument 'operation'` on that call. So `get_logger` here wraps that logger in a
`LoggerAdapter` that moves those keywords into the `extra` mapping, which is
what the consumers' own fallback does and what the stdlib accepts. The
underlying logger still comes from `zeusdb-vector-database` when it is
installed, so the central logging configuration owns handlers and format.

`operation_context` has no counterpart in `zeusdb-vector-database`. It is
implemented here, matching the fallback both consumers carry: a debug record on
entry, an info record carrying `duration_ms` on success, an error record
carrying `duration_ms` and `error` on failure, and the exception re-raised.
Records carry a traceback on the error path, which `llama-index` already
requested of its own fallback and `langchain-zeusdb` did not.
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from time import perf_counter
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Iterator, MutableMapping

__all__ = ["get_logger", "operation_context"]

# Keywords the stdlib logging call signature already claims. Everything else a
# caller passes is treated as a structured field.
_RESERVED = frozenset({"exc_info", "stack_info", "stacklevel", "extra"})


class _StructuredAdapter(logging.LoggerAdapter):
    """Move arbitrary keyword fields into `extra` for the stdlib logger."""

    def process(
        self, msg: Any, kwargs: MutableMapping[str, Any]
    ) -> tuple[Any, MutableMapping[str, Any]]:
        extra = kwargs.get("extra") or {}
        if not isinstance(extra, dict):
            # Defensive: keep logging working rather than raising on a caller
            # that passed something other than a mapping.
            extra = {"_extra": repr(extra)}
        fields = {key: kwargs.pop(key) for key in list(kwargs) if key not in _RESERVED}
        if fields:
            extra.update(fields)
            kwargs["extra"] = extra
        return msg, kwargs


def _base_logger(name: str | None) -> logging.Logger:
    """Return the underlying logger, from the vector database when installed.

    Falls back to the same `zeusdb.vector` names when it is not, so this module
    imports and works on its own.
    """
    try:
        from zeusdb_vector_database.logging_config import (
            get_logger as _vector_database_get_logger,
        )
    except ImportError:
        return logging.getLogger(f"zeusdb.vector.{name}" if name else "zeusdb.vector")
    return _vector_database_get_logger(name)


def get_logger(name: str | None = None) -> logging.LoggerAdapter:
    """Return a logger that accepts arbitrary structured fields as keywords.

    Args:
        name: Optional suffix, such as `"langchain_zeusdb"`. The base
            `zeusdb.vector` logger is returned when omitted.

    Returns:
        A `LoggerAdapter` over the configured `zeusdb.vector` logger.
    """
    return _StructuredAdapter(_base_logger(name), {})


@contextmanager
def operation_context(operation_name: str, **context: Any) -> Iterator[None]:
    """Log the start, completion and failure of an operation with its duration.

    Args:
        operation_name: The operation being timed, recorded as `operation`.
        **context: Structured fields attached to every record.

    Yields:
        Nothing. The exception from a failing block is logged and re-raised.
    """
    logger = get_logger()
    logger.debug(f"{operation_name} started", operation=operation_name, **context)
    start = perf_counter()
    try:
        yield
    except Exception as e:
        logger.exception(
            f"{operation_name} failed",
            operation=operation_name,
            duration_ms=(perf_counter() - start) * 1000,
            error=str(e),
            **context,
        )
        raise
    else:
        logger.info(
            f"{operation_name} completed",
            operation=operation_name,
            duration_ms=(perf_counter() - start) * 1000,
            **context,
        )
