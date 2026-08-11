"""The quick start form, as the README and the documentation site print it."""


def test_vector_database_import():
    from zeusdb import VectorDatabase

    assert VectorDatabase is not None
