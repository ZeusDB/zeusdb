"""
ZeusDB - A modular database ecosystem
"""
from typing import Any

__version__ = "0.0.3"

__all__ = []

def __getattr__(name: str) -> Any:
    if name == "VectorDatabase":
        try:
            from zeusdb_vector_database import VectorDatabase
            __all__.append("VectorDatabase")
            return VectorDatabase
        except ImportError:
            raise ImportError(
                "VectorDatabase requires zeusdb-vector-database.\n"
                "Install with: uv pip install zeusdb-vector-database"
            )

    # Future modules — will be uncommented when available

    # elif name == "RelationalDatabase":
    #     try:
    #         from zeusdb_relational_database import RelationalDatabase
    #         __all__.append("RelationalDatabase")
    #         return RelationalDatabase
    #     except ImportError:
    #         raise ImportError(
    #             "RelationalDatabase requires zeusdb-relational-database.\n"
    #             "Install with: uv pip install zeusdb-relational-database"
    #         )

    # elif name == "GraphDatabase":
    #     try:
    #         from zeusdb_graph_database import GraphDatabase
    #         __all__.append("GraphDatabase")
    #         return GraphDatabase
    #     except ImportError:
    #         raise ImportError(
    #             "GraphDatabase requires zeusdb-graph-database.\n"
    #             "Install with: uv pip install zeusdb-graph-database"
    #         )

    # elif name == "DocumentDatabase":
    #     try:
    #         from zeusdb_document_database import DocumentDatabase
    #         __all__.append("DocumentDatabase")
    #         return DocumentDatabase
    #     except ImportError:
    #         raise ImportError(
    #             "DocumentDatabase requires zeusdb-document-database.\n"
    #             "Install with: uv pip install zeusdb-document-database"
    #         )

    raise AttributeError(f"module 'zeusdb' has no attribute '{name}'")

def __dir__():
    return sorted([
        "__version__",
        "VectorDatabase",
        # "RelationalDatabase",  # Future
        # "GraphDatabase",       # Future
        # "DocumentDatabase",    # Future
    ])