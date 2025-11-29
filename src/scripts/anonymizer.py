"""
Enhanced anonymization logic with automatic detection of PII
Uses spaCy + Faker + Regex to detect and anonymize emails, names, and phone numbers
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
        self.phone_mapping: Dict[str, str] = {}
        
        # Padrões regex para detecção
        self.email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        
        # Padrão para telefones (suporta vários formatos internacionais)
        # Exemplos: +351912345678, 912345678, (21) 98765-4321, +55 11 98765-4321
        self.phone_pattern = re.compile(
            r'(?:\+\d{1,3}[\s-]?)?'  # Código país opcional: +351, +55
            r'(?:\(\d{2,3}\)[\s-]?)?'  # Código área com parênteses: (21), (11)
            r'(?:\d{2,3}[\s-]?)?'  # Código área sem parênteses: 21, 11
            # Número principal: 912345678 , 933 456 789
            r'\d{3}[\s-]?\d{3}[\s-]?\d{3}'
        )
        
        # Palavras-chave para identificar colunas de email
        self.email_keywords = ['email', 'e-mail', 'mail', 'correo', 'correio']
        
        # Palavras-chave para identificar colunas de telefone
        self.phone_keywords = [
            'phone', 'telephone', 'telefone', 'tel', 'fone',
            'mobile', 'cell', 'celular', 'movil', 'movel',
            'whatsapp', 'numero', 'number'
        ]
        
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
    
    def is_phone_column(self, column_name: str, sample_values: List[str]) -> bool:
        """
        Detecta se uma coluna contém números de telefone
        """
        # Verificar nome da coluna
        column_lower = column_name.lower()
        if any(keyword in column_lower for keyword in self.phone_keywords):
            # Verificar se não é email (algumas colunas podem ter "contact" no nome)
            if not any(email_kw in column_lower for email_kw in self.email_keywords):
                return True
        
        # Verificar valores de amostra
        if sample_values:
            phone_count = 0
            for val in sample_values:
                if not val:
                    continue
                val_str = str(val).strip()
                # Verificar se parece um telefone e NÃO é email
                if self.phone_pattern.search(val_str) and '@' not in val_str:
                    phone_count += 1
            
            # Se >50% dos valores são telefones, é uma coluna de telefone
            return phone_count / len(sample_values) > 0.5
        
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
                            'price', 'preco', 'value', 'valor', 'id', 'identifier', 'identificador',
                            'observacoes', 'phone', 'telephone', 'telefone', 'email']
        
        
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
        Retorna: {column_name: 'email' ou 'name' ou 'phone'}
        """
        pii_columns = {}
        
        print("\n🔍 Detectando colunas com PII...")
        
        for column_name, sample_values in column_samples.items():
            # Filtrar valores None/NULL
            sample_values = [v for v in sample_values if v is not None]
            
            if not sample_values:
                continue
            
            # Testar se é email (primeiro, pois tem prioridade sobre phone em campos "contact")
            if self.is_email_column(column_name, sample_values):
                pii_columns[column_name] = 'email'
                print(f"   ✓ {column_name} → EMAIL")
                continue
            
            # Testar se é telefone
            if self.is_phone_column(column_name, sample_values):
                pii_columns[column_name] = 'phone'
                print(f"   ✓ {column_name} → PHONE")
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
    
    def anonymize_phone(self, original_phone: str) -> str:
        """
        Anonimiza um número de telefone, mantendo o formato similar ao original
        """
        if not original_phone:
            return original_phone
        
        phone_str = str(original_phone).strip()
        
        if phone_str not in self.phone_mapping:
            # Detectar formato do telefone original
            has_country_code = phone_str.startswith('+')
            has_parentheses = '(' in phone_str and ')' in phone_str
            has_spaces = ' ' in phone_str
            has_dashes = '-' in phone_str
            
            # Gerar número fake baseado no locale
            fake_phone = self.fake.phone_number()
            
            # Limpar caracteres especiais do fake phone
            clean_fake = re.sub(r'[^\d+]', '', fake_phone)
            
            # Se o original não tem código de país, remover do fake
            if not has_country_code and clean_fake.startswith('+'):
                clean_fake = clean_fake[1:]
                # Garantir que tem pelo menos 9 dígitos
                while len(clean_fake) < 9:
                    clean_fake += str(self.fake.random_digit())
            
            # Aplicar formatação similar ao original
            if has_parentheses:
                # Formato: (XX) XXXXX-XXXX ou +XX (XX) XXXXX-XXXX
                if has_country_code:
                    if len(clean_fake) >= 12:
                        formatted = f"+{clean_fake[:2]} ({clean_fake[2:4]}) {clean_fake[4:9]}-{clean_fake[9:13]}"
                    else:
                        formatted = f"+{clean_fake[:2]} ({clean_fake[2:4]}) {clean_fake[4:]}"
                else:
                    if len(clean_fake) >= 11:
                        formatted = f"({clean_fake[:2]}) {clean_fake[2:7]}-{clean_fake[7:11]}"
                    else:
                        formatted = f"({clean_fake[:2]}) {clean_fake[2:]}"
            elif has_spaces:
                # Formato com espaços: +351 912 345 678
                if has_country_code:
                    if len(clean_fake) >= 12:
                        formatted = f"+{clean_fake[:2]} {clean_fake[2:5]} {clean_fake[5:8]} {clean_fake[8:11]}"
                    else:
                        formatted = f"+{clean_fake[:2]} {clean_fake[2:]}"
                else:
                    if len(clean_fake) >= 9:
                        formatted = f"{clean_fake[:3]} {clean_fake[3:6]} {clean_fake[6:9]}"
                    else:
                        formatted = clean_fake
            elif has_dashes:
                # Formato com hífens: 912-345-678
                if len(clean_fake) >= 9:
                    formatted = f"{clean_fake[:3]}-{clean_fake[3:6]}-{clean_fake[6:9]}"
                else:
                    formatted = clean_fake
            else:
                # Sem formatação especial
                formatted = clean_fake
            
            self.phone_mapping[phone_str] = formatted
        
        return self.phone_mapping[phone_str]
    
    def anonymize_text(self, text: str) -> str:
        """
        Detecta e anonimiza nomes, emails e telefones em texto livre usando regex
        Preserva o contexto e estrutura do texto
        """
        if not text or str(text).strip() == "":
            return text
        
        text_str = str(text)
        anonymized_text = text_str
        
        # 1. Processar telefones PRIMEIRO (para evitar confusão com outros padrões)
        phone_matches = []
        for phone_match in self.phone_pattern.finditer(anonymized_text):
            phone_matches.append((phone_match.start(), phone_match.end(), phone_match.group()))
        
        # Processar de trás para frente para não quebrar offsets
        for start, end, original_phone in reversed(phone_matches):
            anonymized_phone = self.anonymize_phone(original_phone)
            anonymized_text = (
                anonymized_text[:start] +
                anonymized_phone +
                anonymized_text[end:]
            )
        
        # 2. Processar nomes conhecidos dos campos estruturados
        known_names_in_text = []
        for original_name in self.name_mapping.keys():
            if original_name in anonymized_text:
                pattern = re.escape(original_name)
                for match in re.finditer(pattern, anonymized_text):
                    known_names_in_text.append((match.start(), match.end(), original_name))
        
        # Processar de trás para frente
        for start, end, original_name in reversed(sorted(known_names_in_text)):
            anonymized_name = self.name_mapping[original_name]
            anonymized_text = (
                anonymized_text[:start] + 
                anonymized_name + 
                anonymized_text[end:]
            )
        
        # 3. Detectar nomes novos com regex
        name_pattern = re.compile(r'\b[A-ZÁÀÂÃÉÊÍÓÔÕÚÇ][a-záàâãéêíóôõúç]+(?:\s+[A-ZÁÀÂÃÉÊÍÓÔÕÚÇ][a-záàâãéêíóôõúç]+){1,3}\b')
        
        potential_names = []
        for match in name_pattern.finditer(anonymized_text):
            potential_name = match.group()
            
            if self._looks_like_name(potential_name) and not self._is_common_word(potential_name):
                potential_names.append((match.start(), match.end(), potential_name))
        
        # Processar de trás para frente
        for start, end, potential_name in reversed(potential_names):
            anonymized_name = self.anonymize_name(potential_name)
            anonymized_text = (
                anonymized_text[:start] + 
                anonymized_name + 
                anonymized_text[end:]
            )
        
        # 4. Processar emails por último
        email_matches = []
        for email_match in self.email_pattern.finditer(anonymized_text):
            email_matches.append((email_match.start(), email_match.end(), email_match.group()))
        
        # Processar de trás para frente
        for start, end, original_email in reversed(email_matches):
            anonymized_email = self.anonymize_email(original_email)
            anonymized_text = (
                anonymized_text[:start] +
                anonymized_email +
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
            'Assigned', 'Support', 'Agent', 'Reported', 'Issues', 'Regarding', 'Contacted','Contact',
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
        
        # Verificar se TODAS as palavras do texto formam uma palavra comum
        if text in common_words:
            return True
        
        # Se é nome composto, verificar se primeira palavra é comum (ex: "User Luís")
        words = text.split()
        if len(words) > 1 and words[0] in common_words:
            return True
        
        return False
    
    def get_statistics(self) -> Dict:
        """
        Retorna estatísticas da anonimização
        """
        return {
            'total_names_anonymized': len(self.name_mapping),
            'total_emails_anonymized': len(self.email_mapping),
            'total_phones_anonymized': len(self.phone_mapping),
            'sample_mappings': {
                'names': dict(list(self.name_mapping.items())[:5]),
                'emails': dict(list(self.email_mapping.items())[:3]),
                'phones': dict(list(self.phone_mapping.items())[:3])
            }
        }