"""
Security tests for UI path traversal vulnerabilities (UI-02).

Tests path validation in experiment context script operations.
"""
import pytest
from pathlib import Path
from unittest.mock import Mock, patch

try:
    from tools.ui.context.experiment_context import ExperimentContext
    UI_AVAILABLE = True
except ImportError:
    UI_AVAILABLE = False
    pytest.skip("UI context not available", allow_module_level=True)


class TestExperimentContextPathSecurity:
    """Test UI-02: Path traversal prevention in experiment script operations."""
    
    @pytest.fixture
    def context(self):
        """Create ExperimentContext instance for testing."""
        if not UI_AVAILABLE:
            pytest.skip("UI not available")
        return ExperimentContext()
    
    def test_validate_script_path_rejects_parent_traversal(self, context):
        """Verify ../escape.py is rejected."""
        with pytest.raises(ValueError, match="Invalid script filename|Path traversal"):
            context._validate_script_path("../escape.py")
    
    def test_validate_script_path_rejects_absolute_paths(self, context):
        """Verify absolute paths are rejected."""
        with pytest.raises(ValueError, match="Absolute paths not allowed|Path traversal"):
            context._validate_script_path("/etc/passwd")
        
        with pytest.raises(ValueError, match="Absolute paths not allowed|Path traversal"):
            context._validate_script_path("C:\\Windows\\System32\\config")
    
    def test_validate_script_path_rejects_hidden_files(self, context):
        """Verify hidden files (starting with .) are rejected."""
        with pytest.raises(ValueError, match="Invalid script filename"):
            context._validate_script_path(".hidden.py")
    
    def test_validate_script_path_rejects_empty_filename(self, context):
        """Verify empty filename is rejected."""
        with pytest.raises(ValueError, match="Invalid script filename"):
            context._validate_script_path("")
    
    def test_validate_script_path_rejects_complex_traversal(self, context):
        """Verify complex traversal attempts are rejected."""
        with pytest.raises(ValueError, match="Invalid script filename|Path traversal"):
            context._validate_script_path("subdir/../../../etc/passwd")
    
    def test_validate_script_path_accepts_simple_filename(self, context):
        """Verify simple filenames are accepted."""
        result = context._validate_script_path("test_script.py")
        assert result.name == "test_script.py"
        assert result.is_relative_to(context._scripts_dir)
    
    def test_validate_script_path_extracts_basename(self, context):
        """Verify only basename is used from complex paths."""
        # Even if user provides a path, only the basename should be used
        result = context._validate_script_path("some/path/script.py")
        assert result.name == "script.py"
        assert result.parent == context._scripts_dir
    
    def test_save_and_run_script_validates_path(self, context):
        """Verify saveAndRunScript validates filename."""
        with patch.object(context, 'runPythonFile'):
            with patch.object(context, 'scriptLogMessage'):
                with patch.object(context, 'scriptFinished') as mock_finished:
                    # Try to save with traversal attempt
                    context.saveAndRunScript("../escape.py", "print('test')")
                    
                    # Should emit security error
                    mock_finished.emit.assert_called_once()
                    args = mock_finished.emit.call_args[0]
                    assert args[0] is False  # success=False
                    assert "traversal" in args[1].lower() or "invalid" in args[1].lower()
    
    def test_delete_script_validates_path(self, context):
        """Verify deleteScript validates filename."""
        with patch.object(context, 'scriptLogMessage') as mock_log:
            # Try to delete with traversal attempt
            context.deleteScript("../../../etc/passwd")
            
            # Should log security error
            security_calls = [call for call in mock_log.emit.call_args_list 
                            if "SECURITY" in str(call) or "traversal" in str(call).lower()]
            assert len(security_calls) > 0, "Should log security warning"
    
    def test_read_script_validates_path(self, context):
        """Verify readScript validates filename."""
        # Try to read with traversal attempt
        result = context.readScript("../../../etc/passwd")
        
        # Should return empty string or error (not actual file content)
        assert result == "", "Should not read files outside uploads directory"
    
    def test_scripts_dir_is_resolved(self, context):
        """Verify scripts directory is resolved to absolute path."""
        assert context._scripts_dir.is_absolute(), "Scripts dir should be absolute"
    
    def test_list_uploaded_scripts_safe(self, context):
        """Verify listUploadedScripts only returns files from uploads directory."""
        scripts = context.listUploadedScripts()
        
        # All returned scripts should be simple filenames (no paths)
        for script in scripts:
            assert "/" not in script, "Should return simple filenames only"
            assert "\\" not in script, "Should return simple filenames only"
            assert not script.startswith("."), "Should not return hidden files"


class TestPathValidationEdgeCases:
    """Test edge cases in path validation."""
    
    @pytest.fixture
    def context(self):
        """Create ExperimentContext instance for testing."""
        if not UI_AVAILABLE:
            pytest.skip("UI not available")
        return ExperimentContext()
    
    def test_unicode_filename_handling(self, context):
        """Verify Unicode filenames are handled safely."""
        # Should accept valid Unicode filenames
        result = context._validate_script_path("test_文件.py")
        assert result.name == "test_文件.py"
    
    def test_special_characters_in_filename(self, context):
        """Verify special characters are handled."""
        # These should work (common in filenames)
        for name in ["test-script.py", "test_script.py", "test.script.py"]:
            result = context._validate_script_path(name)
            assert result.name == name
    
    def test_null_byte_injection(self, context):
        """Verify null byte injection is prevented."""
        with pytest.raises(ValueError):
            context._validate_script_path("test\x00.py")
    
    def test_windows_path_separators(self, context):
        """Verify Windows path separators are handled."""
        # Should extract basename even with Windows separators
        result = context._validate_script_path("folder\\script.py")
        assert result.name == "script.py"
        assert result.parent == context._scripts_dir


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
