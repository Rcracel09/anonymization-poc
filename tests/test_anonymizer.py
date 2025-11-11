import pytest 
from src.scripts.anonymizer import Anonymizer

@pytest.fixture
def anonymizer():
    return Anonymizer(locale='pt_PT')

def test_anonymize_name_consistency(anonymizer):
    """Mesmo nome deve gerar sempre o mesmo resultado"""
    name1 = anonymizer.anonymize_name("João Silva")
    name2 = anonymizer.anonymize_name("João Silva")
    
    assert name1 == name2
    assert name1 != "João Silva"

def test_anonymize_different_names(anonymizer):
    """Nomes diferentes devem gerar resultados diferentes"""
    name1 = anonymizer.anonymize_name("João Silva")
    name2 = anonymizer.anonymize_name("Maria Santos")
    
    assert name1 != name2

def test_anonymize_text_with_person(anonymizer):
    """spaCy deve detetar nomes em texto livre"""
    original = "Plano revisto por João Silva"
    anonymized = anonymizer.anonymize_text(original)
    
    assert "João Silva" not in anonymized
    assert "Plano revisto por" in anonymized

def test_anonymize_email(anonymizer):
    """Emails devem ser anonimizados"""
    email1 = anonymizer.anonymize_email("joao@empresa.pt")
    
    assert email1 != "joao@empresa.pt"
    assert "@" in email1