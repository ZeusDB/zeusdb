"""
Tests for ZeusDB module error handling.
"""
import pytest


def test_missing_attribute():
    """Test that accessing non-existent modules raises helpful AttributeError."""
    import zeusdb
    
    with pytest.raises(AttributeError) as exc_info:
        zeusdb.NonExistentModule
    
    error_msg = str(exc_info.value)
    assert "has no attribute" in error_msg
    assert "NonExistentModule" in error_msg


def test_missing_attribute_message_format():
    """Test the specific format of the error message.

    Asserts the opening rather than the whole string. The message also lists
    the available attributes, and pinning that list here made this test fail
    the moment the list changed.
    """
    import zeusdb

    with pytest.raises(AttributeError) as exc_info:
        zeusdb.SomeRandomDatabase

    expected_prefix = "module 'zeusdb' has no attribute 'SomeRandomDatabase'"
    assert str(exc_info.value).startswith(expected_prefix)
    assert "Available attributes:" in str(exc_info.value)


def test_case_sensitive_attribute_access():
    """Test that attribute access is case sensitive."""
    import zeusdb
    
    # Should work (assuming VectorDatabase is available)
    try:
        zeusdb.VectorDatabase  # This might fail if package not installed, but that's a different error
    except ImportError:
        pass  # Expected if zeusdb-vector-database not installed
    except AttributeError:
        pytest.fail("VectorDatabase should be a valid attribute name")
    
    # Should fail - wrong case
    with pytest.raises(AttributeError):
        zeusdb.vectordatabase
    
    with pytest.raises(AttributeError):
        zeusdb.VECTORDATABASE


def test_dir_includes_expected_attributes():
    """Test that __dir__ returns expected attributes."""
    import zeusdb
    
    available_attrs = dir(zeusdb)
    
    # Should always include version
    assert "__version__" in available_attrs
    
    # Should include known database types (even if not installed)
    assert "VectorDatabase" in available_attrs
    
    # Should not include random attributes
    assert "NonExistentModule" not in available_attrs


def test_all_attribute():
    """Test that __all__ is properly defined."""
    import zeusdb
    
    # Should have __all__ defined
    assert hasattr(zeusdb, "__all__")
    
    # Should include version
    assert "__version__" in zeusdb.__all__
    
    # Should include database types
    assert "VectorDatabase" in zeusdb.__all__
    