"""
Security tests for license secret validation (UI-13).

Tests that development license secret is detected and rejected in builds.
"""
import pytest
import sys
import os
from pathlib import Path
from unittest.mock import patch, Mock
import subprocess


class TestLicenseSecretValidation:
    """Test UI-13: License secret validation in build process."""
    
    def test_development_secret_detected(self):
        """Verify development secret is detected in _version.py."""
        from tools.ui._version import LICENSE_SECRET
        
        # In development, the secret should start with the dev prefix
        # or be set via environment variable
        if not os.getenv("SKYMESHX_LICENSE_SECRET"):
            assert LICENSE_SECRET.startswith("skymeshx-dev-secret"), \
                "Development builds should have dev secret prefix"
    
    def test_setup_validation_function_exists(self):
        """Verify setup.py has validation function."""
        setup_path = Path(__file__).parent.parent.parent / "setup.py"
        setup_content = setup_path.read_text()
        
        assert "validate_license_secret" in setup_content, \
            "setup.py should have validate_license_secret function"
        assert "RELEASE BLOCKER" in setup_content, \
            "setup.py should have release blocker message"
    
    def test_setup_checks_dev_secret(self):
        """Verify setup.py checks for development secret."""
        setup_path = Path(__file__).parent.parent.parent / "setup.py"
        setup_content = setup_path.read_text()
        
        assert "skymeshx-dev-secret" in setup_content, \
            "setup.py should check for dev secret prefix"
        assert "sys.exit(1)" in setup_content, \
            "setup.py should exit on validation failure"
    
    def test_setup_checks_minimum_length(self):
        """Verify setup.py checks minimum secret length."""
        setup_path = Path(__file__).parent.parent.parent / "setup.py"
        setup_content = setup_path.read_text()
        
        assert "len(LICENSE_SECRET)" in setup_content, \
            "setup.py should check secret length"
        assert "32" in setup_content, \
            "setup.py should enforce minimum 32 character length"
    
    def test_skip_check_environment_variable(self):
        """Verify SKIP_LICENSE_CHECK environment variable works."""
        setup_path = Path(__file__).parent.parent.parent / "setup.py"
        setup_content = setup_path.read_text()
        
        assert "SKIP_LICENSE_CHECK" in setup_content, \
            "setup.py should support SKIP_LICENSE_CHECK env var"
    
    def test_environment_variable_override(self):
        """Verify LICENSE_SECRET can be set via environment variable."""
        with patch.dict(os.environ, {"SKYMESHX_LICENSE_SECRET": "production-secret-32-chars-long-xyz"}):
            # Reload the module to pick up environment variable
            import importlib
            from tools.ui import _version
            importlib.reload(_version)
            
            assert _version.LICENSE_SECRET == "production-secret-32-chars-long-xyz", \
                "Should use environment variable when set"
    
    @pytest.mark.skipif(
        os.getenv("SKIP_LICENSE_CHECK") == "1",
        reason="License check is skipped in this environment"
    )
    def test_setup_fails_with_dev_secret(self):
        """Verify setup.py fails when development secret is present."""
        # This test simulates running setup.py with dev secret
        setup_path = Path(__file__).parent.parent.parent / "setup.py"
        
        # Run setup.py in a subprocess to test validation
        env = os.environ.copy()
        env.pop("SKYMESHX_LICENSE_SECRET", None)  # Remove any override
        env.pop("SKIP_LICENSE_CHECK", None)  # Don't skip check
        
        result = subprocess.run(
            [sys.executable, str(setup_path), "--version"],
            capture_output=True,
            text=True,
            env=env
        )
        
        # Should fail if dev secret is present
        if "skymeshx-dev-secret" in open(Path(__file__).parent.parent.parent / "tools/ui/_version.py").read():
            assert result.returncode != 0, \
                "setup.py should fail with development secret"
            assert "RELEASE BLOCKER" in result.stderr, \
                "Should show release blocker message"
    
    def test_setup_succeeds_with_skip_check(self):
        """Verify setup.py succeeds when SKIP_LICENSE_CHECK=1."""
        setup_path = Path(__file__).parent.parent.parent / "setup.py"
        
        env = os.environ.copy()
        env["SKIP_LICENSE_CHECK"] = "1"
        
        result = subprocess.run(
            [sys.executable, str(setup_path), "--version"],
            capture_output=True,
            text=True,
            env=env,
            timeout=10
        )
        
        # Should succeed with skip check
        assert result.returncode == 0, \
            "setup.py should succeed with SKIP_LICENSE_CHECK=1"


class TestLicenseSecretStrength:
    """Test license secret strength requirements."""
    
    def test_secret_minimum_length(self):
        """Verify secret meets minimum length requirement."""
        from tools.ui._version import LICENSE_SECRET
        
        # If not using environment variable, dev secret is expected
        if not os.getenv("SKYMESHX_LICENSE_SECRET"):
            # Dev secret should still meet minimum length for testing
            assert len(LICENSE_SECRET) >= 32, \
                "License secret should be at least 32 characters"
    
    def test_secret_not_empty(self):
        """Verify secret is not empty."""
        from tools.ui._version import LICENSE_SECRET
        
        assert LICENSE_SECRET, "License secret should not be empty"
        assert LICENSE_SECRET.strip(), "License secret should not be whitespace"
    
    def test_secret_documentation_exists(self):
        """Verify license secret is documented."""
        version_path = Path(__file__).parent.parent.parent / "tools/ui/_version.py"
        version_content = version_path.read_text()
        
        assert "HMAC-SHA256" in version_content, \
            "Should document secret algorithm"
        assert "ROTATE" in version_content, \
            "Should document rotation requirement"
        assert "SKYMESHX_LICENSE_SECRET" in version_content, \
            "Should document environment variable"


class TestBuildProcessSecurity:
    """Test overall build process security."""
    
    def test_setup_imports_version_module(self):
        """Verify setup.py imports and validates _version module."""
        setup_path = Path(__file__).parent.parent.parent / "setup.py"
        setup_content = setup_path.read_text()
        
        assert "from tools.ui._version import LICENSE_SECRET" in setup_content, \
            "setup.py should import LICENSE_SECRET"
    
    def test_validation_runs_before_setup(self):
        """Verify validation runs before setup() call."""
        setup_path = Path(__file__).parent.parent.parent / "setup.py"
        setup_content = setup_path.read_text()
        
        # Find positions of validation and setup calls
        validation_pos = setup_content.find("validate_license_secret()")
        setup_pos = setup_content.find("setup(")
        
        assert validation_pos > 0, "Should call validate_license_secret()"
        assert setup_pos > 0, "Should call setup()"
        assert validation_pos < setup_pos, \
            "Validation should run before setup()"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
