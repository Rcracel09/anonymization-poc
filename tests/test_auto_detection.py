"""
Tests for automatic PII detection and anonymization
"""
import pytest
from src.scripts.anonymizer import Anonymizer

@pytest.fixture
def anonymizer():
    return Anonymizer(locale='pt_PT')

# ========================================
# Name Detection Tests
# ========================================

def test_detect_name_column_by_keyword(anonymizer):
    """Should detect name column by keyword in column name"""
    samples = ["João Silva", "Maria Santos", "Pedro Costa"]
    
    assert anonymizer.is_name_column("customer_name", samples) == True
    assert anonymizer.is_name_column("full_name", samples) == True
    assert anonymizer.is_name_column("author", samples) == True
    assert anonymizer.is_name_column("reviewer_name", samples) == True

def test_detect_name_column_by_content(anonymizer):
    """Should detect name column by analyzing content"""
    name_samples = ["João Silva", "Maria Santos", "Pedro Costa"]
    
    # Even with unclear column name, should detect from content
    assert anonymizer.is_name_column("field1", name_samples) == True
    assert anonymizer.is_name_column("pessoa", name_samples) == True

def test_reject_non_name_columns(anonymizer):
    """Should NOT detect non-name columns"""
    number_samples = ["123", "456", "789"]
    text_samples = ["This is a description", "Another text field", "Some content"]
    
    assert anonymizer.is_name_column("amount", number_samples) == False
    assert anonymizer.is_name_column("description", text_samples) == False

# ========================================
# Email Detection Tests
# ========================================

def test_detect_email_column_by_keyword(anonymizer):
    """Should detect email column by keyword"""
    samples = ["test@example.com", "user@domain.pt", "admin@site.com"]
    
    assert anonymizer.is_email_column("email", samples) == True
    assert anonymizer.is_email_column("contact_email", samples) == True
    assert anonymizer.is_email_column("correio", samples) == True
    assert anonymizer.is_email_column("mail", samples) == True

def test_detect_email_column_by_content(anonymizer):
    """Should detect email by regex pattern in content"""
    email_samples = ["test@example.com", "user@domain.pt", "admin@site.com"]
    
    # Even with unclear column name
    assert anonymizer.is_email_column("field2", email_samples) == True
    assert anonymizer.is_email_column("contact", email_samples) == True

def test_reject_non_email_columns(anonymizer):
    """Should NOT detect non-email columns"""
    name_samples = ["João Silva", "Maria Santos"]
    text_samples = ["This is text", "Another string"]
    
    assert anonymizer.is_email_column("name", name_samples) == False
    assert anonymizer.is_email_column("description", text_samples) == False

# ========================================
# PII Detection Integration Tests
# ========================================

def test_detect_pii_columns_mixed(anonymizer):
    """Should correctly classify mixed columns"""
    column_samples = {
        "customer_name": ["João Silva", "Maria Santos", "Pedro Costa"],
        "email": ["joao@example.com", "maria@example.com", "pedro@example.com"],
        "phone": ["912345678", "923456789", "934567890"],
        "description": ["Some text", "Another description", "More content"],
        "age": ["25", "30", "35"]
    }
    
    pii_columns = anonymizer.detect_pii_columns(column_samples)
    
    assert "customer_name" in pii_columns
    assert pii_columns["customer_name"] == "name"
    
    assert "email" in pii_columns
    assert pii_columns["email"] == "email"
    
    # Should NOT detect these as PII
    assert "phone" not in pii_columns
    assert "description" not in pii_columns
    assert "age" not in pii_columns

# ========================================
# Anonymization Consistency Tests
# ========================================

def test_anonymize_name_consistency(anonymizer):
    """Same name should always generate same fake name"""
    name1 = anonymizer.anonymize_name("João Silva")
    name2 = anonymizer.anonymize_name("João Silva")
    
    assert name1 == name2
    assert name1 != "João Silva"

def test_anonymize_different_names(anonymizer):
    """Different names should generate different fake names"""
    name1 = anonymizer.anonymize_name("João Silva")
    name2 = anonymizer.anonymize_name("Maria Santos")
    
    assert name1 != name2

def test_anonymize_email_consistency(anonymizer):
    """Same email should always generate same fake email"""
    email1 = anonymizer.anonymize_email("joao@empresa.pt")
    email2 = anonymizer.anonymize_email("joao@empresa.pt")
    
    assert email1 == email2
    assert email1 != "joao@empresa.pt"
    assert "@" in email1

# ========================================
# Text PII Extraction Tests
# ========================================

def test_anonymize_text_with_names(anonymizer):
    """Should detect and replace names in free text"""
    original = "Plano revisto por João Silva e aprovado por Maria Santos"
    anonymized = anonymizer.anonymize_text(original)
    
    assert "João Silva" not in anonymized
    assert "Maria Santos" not in anonymized
    assert "Plano revisto por" in anonymized
    assert "aprovado por" in anonymized

def test_anonymize_text_with_emails(anonymizer):
    """Should detect and replace emails in free text"""
    original = "Contact João Silva at joao.silva@example.com for more info"
    anonymized = anonymizer.anonymize_text(original)
    
    assert "joao.silva@example.com" not in anonymized
    assert "@" in anonymized  # Should have a fake email
    assert "Contact" in anonymized

def test_anonymize_text_mixed_pii(anonymizer):
    """Should handle text with both names and emails"""
    original = "Article by Maria Santos (maria.santos@blog.com) and reviewed by João Silva"
    anonymized = anonymizer.anonymize_text(original)
    
    assert "Maria Santos" not in anonymized
    assert "João Silva" not in anonymized
    assert "maria.santos@blog.com" not in anonymized
    assert "Article by" in anonymized
    assert "reviewed by" in anonymized

# ========================================
# Edge Cases
# ========================================

def test_handle_empty_values(anonymizer):
    """Should handle None and empty strings"""
    assert anonymizer.anonymize_name(None) == None
    assert anonymizer.anonymize_name("") == ""
    assert anonymizer.anonymize_email(None) == None
    assert anonymizer.anonymize_email("") == ""

def test_handle_malformed_emails(anonymizer):
    """Should handle malformed emails gracefully"""
    # Missing @
    assert anonymizer.anonymize_email("notanemail") == "notanemail"
    
    # Valid email should be anonymized
    result = anonymizer.anonymize_email("valid@email.com")
    assert result != "valid@email.com"
    assert "@" in result

def test_statistics_tracking(anonymizer):
    """Should track anonymization statistics"""
    anonymizer.anonymize_name("João Silva")
    anonymizer.anonymize_name("Maria Santos")
    anonymizer.anonymize_email("joao@example.com")
    
    stats = anonymizer.get_statistics()
    
    assert stats['total_names_anonymized'] == 2
    assert stats['total_emails_anonymized'] == 1
    assert 'sample_mappings' in stats

# ========================================
# Portuguese-specific Tests
# ========================================

def test_portuguese_name_detection(anonymizer):
    """Should detect Portuguese names with accents"""
    samples = [
        "João António Silva",
        "Maria José Santos",
        "José Luís Ferreira"
    ]
    
    assert anonymizer.is_name_column("nome", samples) == True

def test_portuguese_field_names(anonymizer):
    """Should recognize Portuguese field naming"""
    samples = ["João Silva", "Maria Santos"]
    
    assert anonymizer.is_name_column("pessoa", samples) == True
    assert anonymizer.is_name_column("autor", samples) == True
    assert anonymizer.is_name_column("criador", samples) == True
    
    email_samples = ["test@example.com", "user@example.com"]
    assert anonymizer.is_email_column("correio", email_samples) == True
    assert anonymizer.is_email_column("mail", email_samples) == True