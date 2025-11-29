"""
Tests for phone number detection and anonymization
"""
import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.scripts.anonymizer import Anonymizer

@pytest.fixture
def anonymizer():
    return Anonymizer(locale='pt_PT')

# ========================================
# Phone Detection Tests
# ========================================

def test_detect_phone_column_by_keyword(anonymizer):
    """Should detect phone column by keyword in column name"""
    samples = ["+351912345678", "+351923456789", "+351934567890"]
    
    assert anonymizer.is_phone_column("phone", samples) == True
    assert anonymizer.is_phone_column("telephone", samples) == True
    assert anonymizer.is_phone_column("telefone", samples) == True
    assert anonymizer.is_phone_column("mobile", samples) == True
    assert anonymizer.is_phone_column("celular", samples) == True
    assert anonymizer.is_phone_column("whatsapp", samples) == True

def test_detect_phone_column_by_content(anonymizer):
    """Should detect phone column by analyzing content"""
    phone_samples = ["+351912345678", "912345678", "(21) 98765-4321"]
    
    # Even with unclear column name, should detect from content
    assert anonymizer.is_phone_column("field3", phone_samples) == True
    assert anonymizer.is_phone_column("contact_number", phone_samples) == True

def test_reject_non_phone_columns(anonymizer):
    """Should NOT detect non-phone columns"""
    email_samples = ["test@example.com", "user@example.com"]
    text_samples = ["This is text", "Another string"]
    
    assert anonymizer.is_phone_column("email", email_samples) == False
    assert anonymizer.is_phone_column("description", text_samples) == False

def test_phone_vs_email_detection(anonymizer):
    """Should correctly distinguish between phone and email in 'contact' fields"""
    phone_samples = ["+351912345678", "912345678", "(21) 98765-4321"]
    email_samples = ["test@example.com", "user@example.com"]
    
    # Contact field with phones should be detected as phone
    assert anonymizer.is_phone_column("contact", phone_samples) == True
    
    # Contact field with emails should be detected as email
    assert anonymizer.is_email_column("contact", email_samples) == True

# ========================================
# Phone Anonymization Tests
# ========================================

def test_anonymize_phone_consistency(anonymizer):
    """Same phone should always generate same fake phone"""
    phone1 = anonymizer.anonymize_phone("+351912345678")
    phone2 = anonymizer.anonymize_phone("+351912345678")
    
    assert phone1 == phone2
    assert phone1 != "+351912345678"

def test_anonymize_different_phones(anonymizer):
    """Different phones should generate different fake phones"""
    phone1 = anonymizer.anonymize_phone("+351912345678")
    phone2 = anonymizer.anonymize_phone("+351923456789")
    
    assert phone1 != phone2

def test_anonymize_phone_preserves_format_with_country_code(anonymizer):
    """Should preserve format with country code"""
    original = "+351912345678"
    anonymized = anonymizer.anonymize_phone(original)
    
    assert anonymized.startswith('+')
    assert anonymized != original

def test_anonymize_phone_preserves_format_with_parentheses(anonymizer):
    """Should preserve format with parentheses"""
    original = "(21) 98765-4321"
    anonymized = anonymizer.anonymize_phone(original)
    
    assert '(' in anonymized
    assert ')' in anonymized
    assert anonymized != original

def test_anonymize_phone_preserves_format_with_spaces(anonymizer):
    """Should preserve format with spaces"""
    original = "+351 912 345 678"
    anonymized = anonymizer.anonymize_phone(original)
    
    assert ' ' in anonymized
    assert anonymized != original

def test_anonymize_phone_preserves_format_simple(anonymizer):
    """Should handle simple format without special chars"""
    original = "912345678"
    anonymized = anonymizer.anonymize_phone(original)
    
    assert anonymized != original
    assert anonymized.replace('+', '').replace(' ', '').replace('-', '').replace('(', '').replace(')', '').isdigit()

# ========================================
# Text PII Extraction with Phones
# ========================================

def test_anonymize_text_with_phones(anonymizer):
    """Should detect and replace phones in free text"""
    original = "Contact us at +351912345678 or call 912345678 for more info"
    anonymized = anonymizer.anonymize_text(original)
    
    assert "+351912345678" not in anonymized
    assert "912345678" not in anonymized
    assert "Contact us at" in anonymized
    assert "for more info" in anonymized

def test_anonymize_text_with_phones_and_emails(anonymizer):
    """Should handle text with both phones and emails"""
    original = "Call João Silva at +351912345678 or email joao.silva@example.com"
    anonymized = anonymizer.anonymize_text(original)
    
    assert "+351912345678" not in anonymized
    assert "joao.silva@example.com" not in anonymized
    assert "Call" in anonymized
    assert "or email" in anonymized

def test_anonymize_text_mixed_pii_with_phones(anonymizer):
    """Should handle text with names, emails, and phones"""
    original = "Contact Maria Santos (maria.santos@blog.com, +351923456789) for support"
    anonymized = anonymizer.anonymize_text(original)
    
    assert "Maria Santos" not in anonymized
    assert "maria.santos@blog.com" not in anonymized
    assert "+351923456789" not in anonymized
    assert "Contact" in anonymized
    assert "for support" in anonymized

def test_anonymize_text_multiple_phone_formats(anonymizer):
    """Should detect different phone formats in text"""
    original = """
    Contact options:
    - Mobile: +351912345678
    - Office: (21) 98765-4321
    - WhatsApp: 912 345 678
    """
    anonymized = anonymizer.anonymize_text(original)
    
    assert "+351912345678" not in anonymized
    assert "(21) 98765-4321" not in anonymized
    assert "912 345 678" not in anonymized
    assert "Contact options:" in anonymized
    assert "Mobile:" in anonymized

# ========================================
# Edge Cases
# ========================================

def test_handle_empty_phone(anonymizer):
    """Should handle None and empty strings"""
    assert anonymizer.anonymize_phone(None) == None
    assert anonymizer.anonymize_phone("") == ""

def test_handle_invalid_phone(anonymizer):
    """Should handle invalid phone numbers gracefully"""
    # Too short
    result = anonymizer.anonymize_phone("123")
    assert result == "123"  # Should return as-is if not valid
    
    # Valid phone should be anonymized
    result = anonymizer.anonymize_phone("+351912345678")
    assert result != "+351912345678"

# ========================================
# Statistics Tests
# ========================================

def test_phone_statistics_tracking(anonymizer):
    """Should track phone anonymization in statistics"""
    anonymizer.anonymize_phone("+351912345678")
    anonymizer.anonymize_phone("+351923456789")
    anonymizer.anonymize_phone("912345678")
    
    stats = anonymizer.get_statistics()
    
    assert stats['total_phones_anonymized'] == 3
    assert 'phones' in stats['sample_mappings']
    assert len(stats['sample_mappings']['phones']) <= 3

def test_combined_statistics(anonymizer):
    """Should track all types of PII in statistics"""
    anonymizer.anonymize_name("João Silva")
    anonymizer.anonymize_email("joao@example.com")
    anonymizer.anonymize_phone("+351912345678")
    
    stats = anonymizer.get_statistics()
    
    assert stats['total_names_anonymized'] == 1
    assert stats['total_emails_anonymized'] == 1
    assert stats['total_phones_anonymized'] == 1

# ========================================
# Portuguese Phone Format Tests
# ========================================

def test_portuguese_phone_formats(anonymizer):
    """Should handle various Portuguese phone formats"""
    formats = [
        "+351912345678",          # International format
        "912345678",              # National mobile
        "+351 912 345 678",       # With spaces
        "912 345 678",            # National with spaces
        "+351-912-345-678",       # With dashes
    ]
    
    for phone in formats:
        result = anonymizer.anonymize_phone(phone)
        assert result != phone
        assert result is not None

def test_brazilian_phone_formats(anonymizer):
    """Should handle Brazilian phone formats"""
    formats = [
        "+55 11 98765-4321",      # São Paulo mobile
        "(21) 98765-4321",        # Rio de Janeiro mobile
        "+5511987654321",         # Without formatting
        "(11) 3456-7890",         # Landline
    ]
    
    for phone in formats:
        result = anonymizer.anonymize_phone(phone)
        assert result != phone
        assert result is not None

# ========================================
# Integration Tests
# ========================================

def test_detect_pii_columns_with_phones(anonymizer):
    """Should correctly classify columns including phones"""
    column_samples = {
        "customer_name": ["João Silva", "Maria Santos"],
        "email": ["joao@example.com", "maria@example.com"],
        "phone": ["+351912345678", "+351923456789"],
        "telefone": ["912345678", "923456789"],
        "description": ["Some text", "Another description"],
    }
    
    pii_columns = anonymizer.detect_pii_columns(column_samples)
    
    assert "customer_name" in pii_columns
    assert pii_columns["customer_name"] == "name"
    
    assert "email" in pii_columns
    assert pii_columns["email"] == "email"
    
    assert "phone" in pii_columns
    assert pii_columns["phone"] == "phone"
    
    assert "telefone" in pii_columns
    assert pii_columns["telefone"] == "phone"
    
    # Should NOT detect description
    assert "description" not in pii_columns

def test_anonymize_text_consistency_with_phones(anonymizer):
    """Should maintain consistency across multiple text anonymizations"""
    text1 = "Call João Silva at +351912345678"
    text2 = "João Silva's number is +351912345678"
    
    anon1 = anonymizer.anonymize_text(text1)
    anon2 = anonymizer.anonymize_text(text2)
    
    # Extract the fake name from first anonymization
    # Both texts should use the same fake name and fake phone
    # This is complex to test directly, but we can verify consistency
    # by checking that the same inputs produce the same outputs
    assert anonymizer.anonymize_text(text1) == anon1
    assert anonymizer.anonymize_text(text2) == anon2
