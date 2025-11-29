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
            'client', 'cliente', 'customer', 'assigned'
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
        
        # Excluir colunas que claramente NÃO são nomes de pessoas
        excluded_keywords = ['title', 'titulo', 'subject', 'assunto', 'product', 'produto', 
                            'item', 'project', 'projeto', 'description', 'descricao',
                            'content', 'conteudo', 'text', 'texto', 'note', 'nota',
                            'observation', 'observacao', 'date', 'data', 'amount', 'quantia',
                            'price', 'preco', 'value', 'valor', 'id', 'identifier', 'identificador']
        
        
        if any(keyword in column_lower for keyword in excluded_keywords):
            return False 
        
        # Verificar se contém keywords de nome
        if any(keyword in column_lower for keyword in self.name_keywords):
            return True
        
        # Usar spaCy para analisar valores de amostra
        if sample_values:
            person_count = 0
            for val in sample_values[:10]:  # Limitar análise a 10 valores
                if not val or not isinstance(val, str):
                    continue
                
                # Se valor é muito longo (>150 chars), provavelmente não é só um nome
                if len(val) > 150:
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
        
        # Se é muito longo, provavelmente não é apenas um nome
        if len(text) > 150:
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
        Anonimiza um email, garantindo formato válido (sem espaços)
        """
        if not original_email or '@' not in str(original_email):
            return original_email
        
        email_str = str(original_email).strip()
        
        if email_str not in self.email_mapping:
            # Gerar email válido
            fake_email = self.fake.email()
            
            # Garantir que não há espaços, acentos ou caracteres especiais no email
            # Remover espaços
            fake_email = fake_email.replace(' ', '')
            
            # Remover acentos e caracteres especiais antes do @
            if '@' in fake_email:
                local_part, domain = fake_email.split('@', 1)
                
                # Substituir acentos e caracteres especiais
                replacements = {
                    'á': 'a', 'à': 'a', 'â': 'a', 'ã': 'a', 'ä': 'a',
                    'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
                    'í': 'i', 'ì': 'i', 'î': 'i', 'ï': 'i',
                    'ó': 'o', 'ò': 'o', 'ô': 'o', 'õ': 'o', 'ö': 'o',
                    'ú': 'u', 'ù': 'u', 'û': 'u', 'ü': 'u',
                    'ç': 'c', 'ñ': 'n',
                    'Á': 'A', 'À': 'A', 'Â': 'A', 'Ã': 'A', 'Ä': 'A',
                    'É': 'E', 'È': 'E', 'Ê': 'E', 'Ë': 'E',
                    'Í': 'I', 'Ì': 'I', 'Î': 'I', 'Ï': 'I',
                    'Ó': 'O', 'Ò': 'O', 'Ô': 'O', 'Õ': 'O', 'Ö': 'O',
                    'Ú': 'U', 'Ù': 'U', 'Û': 'U', 'Ü': 'U',
                    'Ç': 'C', 'Ñ': 'N'
                }
                
                for old_char, new_char in replacements.items():
                    local_part = local_part.replace(old_char, new_char)
                
                # Remover hífens e tornar minúsculo
                local_part = local_part.replace('-', '').lower()
                
                fake_email = f"{local_part}@{domain}"
            
            self.email_mapping[email_str] = fake_email
        
        return self.email_mapping[email_str]
    
    def anonymize_text(self, text: str) -> str:
        """
        Usa spaCy para detectar e anonimizar nomes e emails em texto livre
        Preserva o contexto e estrutura do texto
        """
        if not text or str(text).strip() == "":
            return text
        
        text_str = str(text)
        
        # Primeiro, anonimizar emails com regex
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
                # IMPORTANTE: Ignorar entidades que contêm @ (email)
                # spaCy às vezes detecta "Nome at email@domain.com" como uma única entidade
                if '@' in ent.text:
                    # Tentar extrair apenas o nome (antes de "at" ou "em")
                    if ' at ' in ent.text:
                        name_part = ent.text.split(' at ')[0].strip()
                    elif ' em ' in ent.text:  # Português
                        name_part = ent.text.split(' em ')[0].strip()
                    else:
                        # Fallback: pegar tudo antes do primeiro @
                        name_part = ent.text.split('@')[0].strip()
                        # Remover possível "at" ou "em" do final
                        name_part = name_part.rstrip('at ').rstrip('em ').strip()
                    
                    if name_part and len(name_part) > 2:
                        detected_names.add(name_part)
                        anonymized_name = self.anonymize_name(name_part)
                        
                        # Calcular offsets corretos
                        name_start = ent.start_char
                        name_end = ent.start_char + len(name_part)
                        
                        anonymized_text = (
                            anonymized_text[:name_start] +
                            anonymized_name +
                            anonymized_text[name_end:]
                        )
                    continue
                
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
        name_pattern = re.compile(r'\b[A-ZÁÀÂÃÉÊÍÓÔÕÚÇ][a-záàâãéêíóôõúç]+(?:\s+[A-ZÁÀÂÃÉÊÍÓÔÕÚÇ][a-záàâãéêíóôõúç]+){1,3}\b')
        
        # Encontrar todos os potenciais nomes
        potential_names = []
        for match in name_pattern.finditer(anonymized_text):
            potential_name = match.group()
            
            # Só processar se spaCy não detectou, parece nome e não é palavra comum
            if (potential_name not in detected_names and 
                self._looks_like_name(potential_name) and
                not self._is_common_word(potential_name)):
                potential_names.append((match.start(), match.end(), potential_name))
        
        # Processar de trás para frente
        for start, end, potential_name in reversed(potential_names):
            anonymized_name = self.anonymize_name(potential_name)
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
            # Artigos e preposições
            'Article', 'The', 'And', 'Or', 'But', 'In', 'On', 'At', 'To', 'For', 'By', 'With',
            # Contexto
            'Contact', 'Email', 'Phone', 'Address', 'Dear', 'Hello', 'Regards', 'From',
            'Mr', 'Mrs', 'Ms', 'Dr', 'Prof', 'Sir', 'Madam', 'User', 'Customer', 'Client',
            # Dias e meses
            'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday',
            'January', 'February', 'March', 'April', 'May', 'June', 'July', 
            'August', 'September', 'October', 'November', 'December',
            # Locais
            'Portugal', 'Lisboa', 'Porto', 'Coimbra', 'Brazil', 'Brasília',
            'Spain', 'Madrid', 'France', 'Paris', 'England', 'London',
            # Línguas e outros
            'English', 'Portuguese', 'Spanish', 'French',
            'Company', 'Corporation', 'Limited', 'Inc', 'Ltd', 'Group'
        }
        
        # Verificar se QUALQUER palavra é comum
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