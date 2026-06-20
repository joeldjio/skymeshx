"""
Security tests for Pi server (SEC-01, SEC-02, SEC-03, SEC-04).

Tests authentication, CORS, XSS prevention, and request size limits.
"""
import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch
import sys

# Import Pi server module
pi_server_path = Path(__file__).parent.parent.parent / "pi"
sys.path.insert(0, str(pi_server_path))

try:
    import server as pi_server
except ImportError:
    pytest.skip("Pi server module not available", allow_module_level=True)


class TestPiServerAuthentication:
    """Test SEC-01: Authentication and localhost binding."""
    
    def test_default_host_is_localhost(self):
        """Verify default binding is localhost, not 0.0.0.0."""
        with patch('sys.argv', ['server.py']):
            with patch('pi_server.HTTPServer') as mock_server:
                with patch('pi_server.connect'):
                    try:
                        pi_server.main()
                    except SystemExit:
                        pass
                
                # Check that HTTPServer was called with localhost
                if mock_server.called:
                    call_args = mock_server.call_args[0]
                    host, port = call_args[0]
                    assert host == "127.0.0.1", f"Expected localhost binding, got {host}"
    
    def test_api_token_required_for_commands(self):
        """Verify API token is required for /api/command endpoint."""
        # Set a test token
        pi_server._api_token = "test-token-12345"
        
        handler = pi_server._Handler(Mock(), ('127.0.0.1', 8080), Mock())
        handler.headers = {}
        
        # Test without Authorization header
        assert not handler._check_auth(), "Should reject request without auth header"
        
        # Test with wrong token
        handler.headers = {"Authorization": "Bearer wrong-token"}
        assert not handler._check_auth(), "Should reject request with wrong token"
        
        # Test with correct token
        handler.headers = {"Authorization": "Bearer test-token-12345"}
        assert handler._check_auth(), "Should accept request with correct token"
    
    def test_no_token_allows_all_requests(self):
        """Verify that when no token is set, all requests are allowed (backward compat)."""
        pi_server._api_token = ""
        
        handler = pi_server._Handler(Mock(), ('127.0.0.1', 8080), Mock())
        handler.headers = {}
        
        assert handler._check_auth(), "Should allow requests when no token configured"
    
    def test_constant_time_token_comparison(self):
        """Verify token comparison uses constant-time comparison."""
        import hmac
        
        pi_server._api_token = "secret-token"
        handler = pi_server._Handler(Mock(), ('127.0.0.1', 8080), Mock())
        
        # This test verifies that hmac.compare_digest is used
        # by checking the implementation uses it
        import inspect
        source = inspect.getsource(handler._check_auth)
        assert "hmac.compare_digest" in source, "Should use constant-time comparison"


class TestPiServerCORS:
    """Test SEC-02: CORS configuration."""
    
    def test_cors_disabled_by_default(self):
        """Verify CORS is disabled by default."""
        pi_server._cors_origin = ""
        
        handler = pi_server._Handler(Mock(), ('127.0.0.1', 8080), Mock())
        handler.send_response = Mock()
        handler.send_header = Mock()
        handler.end_headers = Mock()
        handler.wfile = Mock()
        handler.wfile.write = Mock()
        
        handler._send(200, "text/plain", b"test")
        
        # Check that CORS header was not added
        cors_calls = [call for call in handler.send_header.call_args_list 
                      if "Access-Control-Allow-Origin" in str(call)]
        assert len(cors_calls) == 0, "Should not add CORS header by default"
    
    def test_cors_enabled_when_configured(self):
        """Verify CORS header is added when explicitly configured."""
        pi_server._cors_origin = "https://example.com"
        
        handler = pi_server._Handler(Mock(), ('127.0.0.1', 8080), Mock())
        handler.send_response = Mock()
        handler.send_header = Mock()
        handler.end_headers = Mock()
        handler.wfile = Mock()
        handler.wfile.write = Mock()
        
        handler._send(200, "text/plain", b"test")
        
        # Check that CORS header was added with correct origin
        handler.send_header.assert_any_call("Access-Control-Allow-Origin", "https://example.com")


class TestPiServerXSSPrevention:
    """Test SEC-03: XSS prevention in log rendering."""
    
    def test_dashboard_html_uses_safe_log_rendering(self):
        """Verify dashboard JavaScript uses textContent instead of innerHTML for logs."""
        dashboard_html = pi_server._DASHBOARD_HTML
        
        # Check that pollLog function uses safe DOM methods
        assert "textContent" in dashboard_html, "Should use textContent for log messages"
        assert "document.createElement" in dashboard_html, "Should create elements safely"
        
        # Verify innerHTML is not used for log content
        # (it's used once to clear, which is safe)
        innerHTML_count = dashboard_html.count("el.innerHTML")
        assert innerHTML_count <= 1, "Should minimize innerHTML usage"
    
    def test_log_level_whitelist(self):
        """Verify log levels are whitelisted before use in CSS classes."""
        dashboard_html = pi_server._DASHBOARD_HTML
        
        # Check that log levels are validated
        assert "['D','I','W','E','C','FC','INFO','WARN','ERROR']" in dashboard_html or \
               "includes(l.l)" in dashboard_html, \
               "Should whitelist log levels"


class TestPiServerRequestLimits:
    """Test SEC-04: Request body size limits."""
    
    def test_max_body_size_constant_defined(self):
        """Verify MAX_BODY_SIZE constant is defined."""
        assert hasattr(pi_server, '_max_body_size'), "Should define _max_body_size"
        assert pi_server._max_body_size > 0, "Max body size should be positive"
        assert pi_server._max_body_size <= 10240, "Max body size should be reasonable (<=10KB)"
    
    def test_oversized_request_rejected(self):
        """Verify requests exceeding max body size are rejected."""
        pi_server._api_token = ""  # Disable auth for this test
        pi_server._max_body_size = 100  # Set small limit for testing
        
        handler = pi_server._Handler(Mock(), ('127.0.0.1', 8080), Mock())
        handler.path = "/api/command"
        handler.headers = {"Content-Length": "1000"}  # Exceeds limit
        handler.send_response = Mock()
        handler.send_header = Mock()
        handler.end_headers = Mock()
        handler.wfile = Mock()
        handler.wfile.write = Mock()
        
        handler.do_POST()
        
        # Should return 413 Payload Too Large
        handler.send_response.assert_called_with(413)


class TestPiServerSecurityConfiguration:
    """Test overall security configuration."""
    
    def test_security_warnings_logged(self):
        """Verify security warnings are logged for risky configurations."""
        with patch('sys.argv', ['server.py', '--host', '0.0.0.0']):
            with patch('pi_server.log') as mock_log:
                with patch('pi_server.HTTPServer'):
                    with patch('pi_server.connect'):
                        try:
                            pi_server.main()
                        except (SystemExit, KeyboardInterrupt):
                            pass
                
                # Check that warning was logged for 0.0.0.0 binding
                warning_calls = [call for call in mock_log.call_args_list 
                                if "0.0.0.0" in str(call) and "WARN" in str(call)]
                assert len(warning_calls) > 0, "Should warn when binding to all interfaces"
    
    def test_token_generation_when_not_provided(self):
        """Verify random token is generated when none provided."""
        with patch('sys.argv', ['server.py']):
            with patch('pi_server.secrets.token_urlsafe', return_value='random-token-xyz'):
                with patch('pi_server.log') as mock_log:
                    with patch('pi_server.HTTPServer'):
                        with patch('pi_server.connect'):
                            try:
                                pi_server.main()
                            except (SystemExit, KeyboardInterrupt):
                                pass
                
                # Check that token generation was logged
                token_calls = [call for call in mock_log.call_args_list 
                              if "Generated token" in str(call)]
                assert len(token_calls) > 0, "Should log generated token"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
