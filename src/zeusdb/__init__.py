"""
ZeusDB - A modular database ecosystem
"""
__version__ = "0.0.3"

__all__ = []

try:
    from zeusdb_vector_database import VectorDatabase # noqa: F401
    __all__.append("VectorDatabase")
except ImportError:
    pass

# try:
#     from zeusdb_relational_database import RelationalDatabase
#     __all__.append("RelationalDatabase")
# except ImportError:
#     pass

# try:
#     from zeusdb_graph_database import GraphDatabase
#     __all__.append("GraphDatabase")
# except ImportError:
#     pass

# try:
#     from zeusdb_document_database import DocumentDatabase
#     __all__.append("DocumentDatabase")
# except ImportError:
#     pass
