"""
Enhanced anonymization logic with automatic detection of PII
Uses spaCy + Faker + Regex to detect and anonymize emails and names
"""

import spacy
import re
from faker import Faker
from typing import Dict, Optional, List, Tuple

class Anonymizer:
    def __init__(self, locale: str = 'pt_PT'):
        """
        Inicializa o anonimizador com modelo spaCy português
        """
        print("📦 Carregando modelo spaCy português...")
        self.nlp = spacy.load("pt_core_news_lg")
        self.fake = Faker(locale)
        
        # Dicionário para consistência
        self.name_mapping: Dict[str, str] = {}
        self.email_mapping: Dict[str, str] = {}
        
        # Padrões regex para detecção
        self.email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        
        # Palavras-chave para identificar colunas de email
        self.email_keywords = ['email', 'e-mail', 'mail', 'correo', 'correio']
        
        # Palavras-chave para identificar colunas de nome
        self.name_keywords = [
            'name', 'nome', 'namen', 'nombre',
            'first_name', 'last_name', 'full_name',
            'firstname', 'lastname', 'fullname',
            'author', 'autor', 'creator', 'criador',
            'owner', 'proprietario', 'user', 'usuario',
            'reviewer', 'revisor', 'approver', 'aprovador',
            'contact', 'contato', 'person', 'pessoa',
            'client', 'cliente', 'customer'
        ]
    
    def is_email_column(self, column_name: str, sample_values: List[str]) -> bool:
        """
        Detecta se uma coluna contém emails
        """
        # Verificar nome da coluna
        column_lower = column_name.lower()
        if any(keyword in column_lower for keyword in self.email_keywords):
            return True
        
        # Verificar valores de amostra
        if sample_values:
            email_count = sum(1 for val in sample_values if val and self.email_pattern.match(str(val)))
            # Se >50% dos valores são emails, é uma coluna de email
            return email_count / len(sample_values) > 0.5
        
        return False
    
    def is_name_column(self, column_name: str, sample_values: List[str]) -> bool:
        """
        Detecta se uma coluna contém nomes de pessoas
        """
        # Verificar nome da coluna
        column_lower = column_name.lower()
        if any(keyword in column_lower for keyword in self.name_keywords):
            return True
        
        # Usar spaCy para analisar valores de amostra
        if sample_values:
            person_count = 0
            for val in sample_values[:10]:  # Limitar análise a 10 valores
                if not val or not isinstance(val, str):
                    continue
                
                doc = self.nlp(val.strip())
                
                # Verificar se o valor inteiro é uma entidade PERSON
                if len(doc.ents) > 0:
                    for ent in doc.ents:
                        if ent.label_ == "PER":
                            person_count += 1
                            break
                # Ou se contém palavras capitalizadas típicas de nomes
                elif self._looks_like_name(val):
                    person_count += 1
            
            # Se >40% parecem nomes, é uma coluna de nome
            return person_count / min(len(sample_values), 10) > 0.4
        
        return False
    
    def _looks_like_name(self, text: str) -> bool:
        """
        Verifica se um texto parece um nome (heurística simples)
        """
        if not text or len(text) < 3:
            return False
        
        # Nome típico: 2-4 palavras capitalizadas
        words = text.split()
        
        # Deve ter pelo menos 2 palavras para ser considerado um nome
        if len(words) < 2:
            return False
            
        if len(words) > 5:
            return False
        
        capitalized_words = sum(1 for w in words if w and w[0].isupper())
        
        # Pelo menos 50% das palavras capitalizadas
        return capitalized_words / len(words) >= 0.5
    
    def detect_pii_columns(self, column_samples: Dict[str, List[str]]) -> Dict[str, str]:
        """
        Detecta automaticamente colunas com PII
        Retorna: {column_name: 'email' ou 'name'}
        """
        pii_columns = {}
        
        print("\n🔍 Detectando colunas com PII...")
        
        for column_name, sample_values in column_samples.items():
            # Filtrar valores None/NULL
            sample_values = [v for v in sample_values if v is not None]
            
            if not sample_values:
                continue
            
            # Testar se é email
            if self.is_email_column(column_name, sample_values):
                pii_columns[column_name] = 'email'
                print(f"   ✓ {column_name} → EMAIL")
                continue
            
            # Testar se é nome
            if self.is_name_column(column_name, sample_values):
                pii_columns[column_name] = 'name'
                print(f"   ✓ {column_name} → NAME")
                continue
        
        return pii_columns
    
    def anonymize_name(self, original_name: str) -> str:
        """
        Anonimiza um nome, mantendo consistência
        """
        if not original_name or str(original_name).strip() == "":
            return original_name
        
        name_str = str(original_name)
        
        if name_str not in self.name_mapping:
            self.name_mapping[name_str] = self.fake.name()
        
        return self.name_mapping[name_str]
    
    def anonymize_email(self, original_email: str) -> str:
        """
        Anonimiza um email
        """
        if not original_email or '@' not in str(original_email):
            return original_email
        
        email_str = str(original_email)
        
        if email_str not in self.email_mapping:
            self.email_mapping[email_str] = self.fake.email()
        
        return self.email_mapping[email_str]
    
    def anonymize_text(self, text: str) -> str:
        """
        Usa spaCy para detectar e anonimizar nomes e emails em texto livre
        """
        if not text or str(text).strip() == "":
            return text
        
        text_str = str(text)
        
        # Primeiro, anonimizar emails com regex
        # Coletar todos os emails para processar de trás para frente
        email_matches = []
        for email_match in self.email_pattern.finditer(text_str):
            email_matches.append((email_match.start(), email_match.end(), email_match.group()))
        
        # Processar emails de trás para frente para não quebrar offsets
        anonymized_text = text_str
        for start, end, original_email in reversed(email_matches):
            anonymized_email = self.anonymize_email(original_email)
            anonymized_text = (
                anonymized_text[:start] +
                anonymized_email +
                anonymized_text[end:]
            )
        
        # Depois, usar spaCy para nomes
        doc = self.nlp(anonymized_text)
        
        # Coletar nomes já detectados pelo spaCy
        detected_names = set()
        
        # Processar entidades de trás para frente para não quebrar offsets
        for ent in reversed(doc.ents):
            if ent.label_ == "PER":  # Nome de pessoa
                detected_names.add(ent.text)
                original = ent.text
                anonymized = self.anonymize_name(original)
                
                # Substituir no texto
                start = ent.start_char
                end = ent.end_char
                anonymized_text = (
                    anonymized_text[:start] + 
                    anonymized + 
                    anonymized_text[end:]
                )
        
        # Fallback: usar regex para encontrar nomes que o spaCy perdeu
        # Padrão: 2-4 palavras capitalizadas (nomes portugueses e ingleses)
        name_pattern = re.compile(r'\b[A-ZÁÀÂÃÉÊÍÓÔÕÚÇ][a-záàâãéêíóôõúç]+(?:\s+[A-ZÁÀÂÃÉÊÍÓÔÕÚÇ][a-záàâãéêíóôõúç]+){1,3}\b')
        
        # Encontrar todos os potenciais nomes
        potential_names = []
        for match in name_pattern.finditer(anonymized_text):
            potential_name = match.group()
            # Só processar se:
            # 1. spaCy não detectou
            # 2. Parece um nome (heurística)
            # 3. Não é uma palavra comum
            if (potential_name not in detected_names and 
                self._looks_like_name(potential_name) and
                not self._is_common_word(potential_name)):
                potential_names.append((match.start(), match.end(), potential_name))
        
        # Processar de trás para frente para não quebrar offsets
        for start, end, potential_name in reversed(potential_names):
            anonymized_name = self.anonymize_name(potential_name)
            # Usar offsets em vez de replace() para evitar substituições indesejadas
            anonymized_text = (
                anonymized_text[:start] + 
                anonymized_name + 
                anonymized_text[end:]
            )
        
        return anonymized_text
    
    def _is_common_word(self, text: str) -> bool:
        """
        Verifica se é uma palavra comum (não é nome)
        """
        # Lista de palavras comuns que podem estar capitalizadas
        common_words = {
            # Artigos e preposições comuns
            'Article', 'The', 'And', 'Or', 'But', 'In', 'On', 'At', 'To', 'For', 'By', 'With',
            # Palavras que aparecem antes de nomes (contexto)
            'Contact', 'Email', 'Phone', 'Address', 'Dear', 'Hello', 'Regards', 'From',
            'Mr', 'Mrs', 'Ms', 'Dr', 'Prof', 'Sir', 'Madam',
            # Dias da semana
            'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday',
            # Meses
            'January', 'February', 'March', 'April', 'May', 'June', 'July', 
            'August', 'September', 'October', 'November', 'December',
            # Locais conhecidos (não pessoas)
            'Portugal', 'Lisboa', 'Porto', 'Coimbra', 'Brazil', 'Brasília',
            'Spain', 'Madrid', 'France', 'Paris', 'England', 'London',
            # Línguas
            'English', 'Portuguese', 'Spanish', 'French',
            # Outras palavras comuns
            'Company', 'Corporation', 'Limited', 'Inc', 'Ltd', 'Group'
        }
        
        # Verificar se QUALQUER palavra é comum (não precisa ser todas)
        # Isso previne "Contact João" de ser considerado um nome
        words = text.split()
        for word in words:
            if word in common_words:
                return True
        
        return False
    
    def get_statistics(self) -> Dict:
        """
        Retorna estatísticas da anonimização
        """
        return {
            'total_names_anonymized': len(self.name_mapping),
            'total_emails_anonymized': len(self.email_mapping),
            'sample_mappings': {
                'names': dict(list(self.name_mapping.items())[:5]),
                'emails': dict(list(self.email_mapping.items())[:3])
            }
        }