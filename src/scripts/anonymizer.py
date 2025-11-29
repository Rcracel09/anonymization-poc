"""
Enhanced anonymization logic with improved PII detection
Melhorias:
1. Detecção mais precisa com scoring system
2. Melhor tratamento de edge cases
3. Performance otimizada
4. Validação de dados mais robusta
5. Suporte a mais padrões de PII
"""

import spacy
import re
from faker import Faker
from typing import Dict, Optional, List, Tuple, Set
from collections import defaultdict
import unicodedata

class Anonymizer:
    def __init__(self, locale: str = 'pt_PT', confidence_threshold: float = 0.6):
        """
        Inicializa o anonimizador com modelo spaCy português
        
        Args:
            locale: Locale para Faker
            confidence_threshold: Threshold de confiança para detecção (0.0 a 1.0)
        """
        print("📦 Carregando modelo spaCy português...")
        self.nlp = spacy.load("pt_core_news_lg")
        self.fake = Faker(locale)
        self.confidence_threshold = confidence_threshold
        
        # Dicionários para consistência
        self.name_mapping: Dict[str, str] = {}
        self.email_mapping: Dict[str, str] = {}
        
        # Estatísticas detalhadas
        self.stats = defaultdict(int)
        
        # Padrões regex otimizados
        self.email_pattern = re.compile(
            r'\b[A-Za-z0-9](?:[A-Za-z0-9._%+-]*[A-Za-z0-9])?@[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?\.[A-Z|a-z]{2,}\b',
            re.IGNORECASE
        )
        
        # Padrão para nomes (2-5 palavras capitalizadas)
        self.name_pattern = re.compile(
            r'\b[A-ZÁÀÂÃÄÉÈÊËÍÌÎÏÓÒÔÕÖÚÙÛÜÇ][a-záàâãäéèêëíìîïóòôõöúùûüç]{1,}(?:\s+(?:de|da|do|dos|das|e|van|von|del|della|di|O\'|Mc|Mac))?\s+[A-ZÁÀÂÃÄÉÈÊËÍÌÎÏÓÒÔÕÖÚÙÛÜÇ][a-záàâãäéèêëíìîïóòôõöúùûüç]{1,}(?:\s+[A-ZÁÀÂÃÄÉÈÊËÍÌÎÏÓÒÔÕÖÚÙÛÜÇ][a-záàâãäéèêëíìîïóòôõöúùûüç]{1,}){0,3}\b'
        )
        
        # Keywords expandidas e ponderadas
        self.email_keywords = {
            # Peso alto (1.0)
            'email': 1.0, 'e-mail': 1.0, 'mail': 0.9, 'correio': 1.0, 'correo': 0.9,
            # Peso médio (0.7)
            'contact_email': 1.0, 'work_email': 1.0, 'personal_email': 1.0,
            'electronic_mail': 0.8,
            # Peso baixo (0.5)
            'contact': 0.5, 'contato': 0.5
        }
        
        self.name_keywords = {
            # Peso alto (1.0)
            'name': 1.0, 'nome': 1.0, 'full_name': 1.0, 'fullname': 1.0,
            'first_name': 1.0, 'last_name': 1.0, 'firstname': 1.0, 'lastname': 1.0,
            # Peso médio-alto (0.8-0.9)
            'author': 0.9, 'autor': 0.9, 'creator': 0.8, 'criador': 0.8,
            'reviewer': 0.9, 'revisor': 0.9, 'approver': 0.8, 'aprovador': 0.8,
            'owner': 0.7, 'proprietario': 0.7, 'responsible': 0.7, 'responsavel': 0.7,
            # Peso médio (0.6-0.7)
            'person': 0.7, 'pessoa': 0.7, 'contact': 0.6, 'contato': 0.6,
            'client': 0.7, 'cliente': 0.7, 'customer': 0.7,
            # Peso baixo (0.5)
            'user': 0.5, 'usuario': 0.5, 'assigned': 0.5,
            'member': 0.5, 'membro': 0.5, 'participant': 0.5
        }
        
        # Keywords de exclusão (certamente NÃO são PII)
        self.exclusion_keywords = {
            'title', 'titulo', 'subject', 'assunto', 'product', 'produto',
            'item', 'project', 'projeto', 'description', 'descricao',
            'content', 'conteudo', 'text', 'texto', 'note', 'nota',
            'observation', 'observacao', 'review', 'comment', 'comentario',
            'message', 'mensagem', 'body', 'status', 'type', 'tipo',
            'category', 'categoria', 'tag', 'label', 'etiqueta'
        }
        
        # Palavras comuns (não são nomes)
        self.common_words = self._load_common_words()
        
        # Cache para otimização
        self._spacy_cache: Dict[str, bool] = {}
    
    def _load_common_words(self) -> Set[str]:
        """
        Carrega lista de palavras comuns que não são nomes
        """
        return {
            # Artigos e conjunções
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'by', 'with',
            'o', 'a', 'os', 'as', 'um', 'uma', 'e', 'ou', 'mas', 'em', 'de', 'para',
            # Tratamentos (podem aparecer mas não são nomes completos)
            'mr', 'mrs', 'ms', 'dr', 'prof', 'sr', 'sra', 'dra',
            # Contexto comum
            'contact', 'email', 'phone', 'address', 'dear', 'hello', 'regards',
            'contato', 'telefone', 'endereco', 'caro', 'ola', 'atenciosamente',
            # Dias e meses
            'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday',
            'segunda', 'terca', 'quarta', 'quinta', 'sexta', 'sabado', 'domingo',
            'january', 'february', 'march', 'april', 'may', 'june', 'july',
            'august', 'september', 'october', 'november', 'december',
            'janeiro', 'fevereiro', 'marco', 'abril', 'maio', 'junho', 'julho',
            'agosto', 'setembro', 'outubro', 'novembro', 'dezembro',
            # Empresas e lugares comuns
            'company', 'corporation', 'limited', 'inc', 'ltd', 'group',
            'empresa', 'sociedade', 'limitada', 'grupo',
            'portugal', 'lisboa', 'porto', 'coimbra', 'brazil', 'brasil',
            'user', 'customer', 'client', 'utilizador', 'cliente'
        }
    
    def _normalize_text(self, text: str) -> str:
        """
        Normaliza texto removendo acentos para comparação
        """
        return ''.join(
            c for c in unicodedata.normalize('NFD', text)
            if unicodedata.category(c) != 'Mn'
        ).lower()
    
    def _calculate_keyword_score(self, column_name: str, keywords: Dict[str, float]) -> float:
        """
        Calcula score baseado em keywords ponderadas
        """
        column_lower = self._normalize_text(column_name)
        max_score = 0.0
        
        for keyword, weight in keywords.items():
            if keyword in column_lower:
                # Score mais alto se keyword está isolada
                if column_lower == keyword:
                    max_score = max(max_score, weight * 1.2)
                # Score médio se keyword está no início ou fim
                elif column_lower.startswith(keyword) or column_lower.endswith(keyword):
                    max_score = max(max_score, weight * 1.1)
                # Score normal se keyword está contida
                else:
                    max_score = max(max_score, weight)
        
        return min(max_score, 1.0)  # Cap em 1.0
    
    def _is_excluded_column(self, column_name: str) -> bool:
        """
        Verifica se coluna deve ser excluída da detecção
        """
        column_lower = self._normalize_text(column_name)
        return any(excl in column_lower for excl in self.exclusion_keywords)
    
    def is_email_column(self, column_name: str, sample_values: List[str]) -> Tuple[bool, float]:
        """
        Detecta se uma coluna contém emails com score de confiança
        
        Returns:
            (is_email, confidence_score)
        """
        # Verificar exclusão
        if self._is_excluded_column(column_name):
            return False, 0.0
        
        # Score baseado em keywords
        keyword_score = self._calculate_keyword_score(column_name, self.email_keywords)
        
        # Se não há samples, usar apenas keyword
        if not sample_values or len(sample_values) == 0:
            return keyword_score >= self.confidence_threshold, keyword_score
        
        # Validar samples
        valid_samples = [v for v in sample_values if v and isinstance(v, str) and len(str(v).strip()) > 0]
        
        if not valid_samples:
            return keyword_score >= self.confidence_threshold, keyword_score
        
        # Score baseado em conteúdo
        email_count = 0
        for val in valid_samples:
            val_str = str(val).strip()
            # Email válido deve ter @ e domínio
            if '@' in val_str and self.email_pattern.fullmatch(val_str):
                email_count += 1
        
        content_score = email_count / len(valid_samples) if valid_samples else 0.0
        
        # Score final: média ponderada (keyword 40%, content 60%)
        final_score = (keyword_score * 0.4) + (content_score * 0.6)
        
        self.stats['email_detection_attempts'] += 1
        if final_score >= self.confidence_threshold:
            self.stats['email_detection_success'] += 1
        
        return final_score >= self.confidence_threshold, final_score
    
    def is_name_column(self, column_name: str, sample_values: List[str]) -> Tuple[bool, float]:
        """
        Detecta se uma coluna contém nomes com score de confiança
        
        Returns:
            (is_name, confidence_score)
        """
        # Verificar exclusão
        if self._is_excluded_column(column_name):
            return False, 0.0
        
        # Score baseado em keywords
        keyword_score = self._calculate_keyword_score(column_name, self.name_keywords)
        
        # Se não há samples, usar apenas keyword
        if not sample_values or len(sample_values) == 0:
            return keyword_score >= self.confidence_threshold, keyword_score
        
        # Validar samples
        valid_samples = [
            v for v in sample_values 
            if v and isinstance(v, str) and 3 <= len(str(v).strip()) <= 150
        ]
        
        if not valid_samples:
            return keyword_score >= self.confidence_threshold, keyword_score
        
        # Análise de conteúdo
        name_indicators = 0
        sample_limit = min(len(valid_samples), 20)  # Limitar análise
        
        for val in valid_samples[:sample_limit]:
            val_str = str(val).strip()
            
            # Skip valores muito curtos ou muito longos
            if len(val_str) < 3 or len(val_str) > 150:
                continue
            
            # Método 1: Heurística rápida
            if self._looks_like_name(val_str):
                name_indicators += 1
                continue
            
            # Método 2: spaCy (mais lento, usar com cache)
            if self._is_person_entity(val_str):
                name_indicators += 1
        
        content_score = name_indicators / sample_limit if sample_limit > 0 else 0.0
        
        # Score final: média ponderada (keyword 35%, content 65%)
        final_score = (keyword_score * 0.35) + (content_score * 0.65)
        
        self.stats['name_detection_attempts'] += 1
        if final_score >= self.confidence_threshold:
            self.stats['name_detection_success'] += 1
        
        return final_score >= self.confidence_threshold, final_score
    
    def _looks_like_name(self, text: str) -> bool:
        """
        Heurística otimizada para verificar se texto parece um nome
        """
        if not text or len(text) < 3 or len(text) > 150:
            return False
        
        # Normalizar espaços
        text = ' '.join(text.split())
        words = text.split()
        
        # Deve ter 2-5 palavras
        if len(words) < 2 or len(words) > 5:
            return False
        
        # Contar palavras capitalizadas (excluindo conectores)
        connectors = {'de', 'da', 'do', 'dos', 'das', 'e', 'van', 'von', 'del', 'della', 'di'}
        capitalized = sum(
            1 for w in words 
            if w and w[0].isupper() and w.lower() not in connectors
        )
        
        # Verificar se não contém palavras comuns
        normalized_words = [self._normalize_text(w) for w in words]
        if any(w in self.common_words for w in normalized_words):
            return False
        
        # Pelo menos 60% das palavras (exceto conectores) devem estar capitalizadas
        non_connector_words = [w for w in words if w.lower() not in connectors]
        if not non_connector_words:
            return False
        
        cap_ratio = capitalized / len(non_connector_words)
        
        # Verificar se não contém números
        has_numbers = any(char.isdigit() for char in text)
        
        # Verificar se não contém caracteres especiais (exceto acentos e hífen)
        has_special = bool(re.search(r'[^a-zA-ZÀ-ÿ\s\'-]', text))
        
        return cap_ratio >= 0.6 and not has_numbers and not has_special
    
    def _is_person_entity(self, text: str) -> bool:
        """
        Usa spaCy para verificar se é uma entidade PERSON (com cache)
        """
        # Verificar cache
        if text in self._spacy_cache:
            return self._spacy_cache[text]
        
        try:
            doc = self.nlp(text)
            is_person = any(ent.label_ == "PER" for ent in doc.ents)
            
            # Cachear resultado
            self._spacy_cache[text] = is_person
            
            # Limitar tamanho do cache
            if len(self._spacy_cache) > 1000:
                # Remover 20% mais antigos
                items_to_remove = list(self._spacy_cache.keys())[:200]
                for key in items_to_remove:
                    del self._spacy_cache[key]
            
            return is_person
        except Exception:
            return False
    
    def detect_pii_columns(self, column_samples: Dict[str, List[str]]) -> Dict[str, Tuple[str, float]]:
        """
        Detecta automaticamente colunas com PII
        
        Returns:
            {column_name: (pii_type, confidence_score)}
        """
        pii_columns = {}
        
        print("\n🔍 Detectando colunas com PII...")
        
        for column_name, sample_values in column_samples.items():
            # Filtrar valores None/NULL
            sample_values = [v for v in sample_values if v is not None]
            
            if not sample_values:
                continue
            
            # Testar email primeiro (mais específico)
            is_email, email_score = self.is_email_column(column_name, sample_values)
            if is_email:
                pii_columns[column_name] = ('email', email_score)
                print(f"   ✓ {column_name} → EMAIL (confiança: {email_score:.2%})")
                continue
            
            # Testar nome
            is_name, name_score = self.is_name_column(column_name, sample_values)
            if is_name:
                pii_columns[column_name] = ('name', name_score)
                print(f"   ✓ {column_name} → NAME (confiança: {name_score:.2%})")
                continue
        
        return pii_columns
    
    def anonymize_name(self, original_name: str) -> str:
        """
        Anonimiza um nome com validação aprimorada
        """
        if not original_name:
            return original_name
        
        name_str = str(original_name).strip()
        
        if not name_str or len(name_str) < 2:
            return original_name
        
        # Normalizar espaços
        name_str = ' '.join(name_str.split())
        
        if name_str not in self.name_mapping:
            # Gerar nome fake
            self.name_mapping[name_str] = self.fake.name()
            self.stats['unique_names_anonymized'] += 1
        
        self.stats['total_name_operations'] += 1
        return self.name_mapping[name_str]
    
    def anonymize_email(self, original_email: str) -> str:
        """
        Anonimiza email com validação e normalização aprimorada
        """
        if not original_email or '@' not in str(original_email):
            return original_email
        
        email_str = str(original_email).strip().lower()
        
        # Validar formato básico
        if not self.email_pattern.fullmatch(email_str):
            return original_email
        
        if email_str not in self.email_mapping:
            # Gerar email válido
            fake_email = self.fake.email()
            
            # Garantir formato válido (sem acentos, espaços)
            fake_email = self._sanitize_email(fake_email)
            
            self.email_mapping[email_str] = fake_email
            self.stats['unique_emails_anonymized'] += 1
        
        self.stats['total_email_operations'] += 1
        return self.email_mapping[email_str]
    
    def _sanitize_email(self, email: str) -> str:
        """
        Remove caracteres inválidos de email
        """
        if '@' not in email:
            return email
        
        local_part, domain = email.split('@', 1)
        
        # Substituir acentos
        local_part = self._normalize_text(local_part)
        
        # Remover caracteres inválidos
        local_part = re.sub(r'[^a-z0-9._+-]', '', local_part)
        
        # Garantir que não começa/termina com ponto
        local_part = local_part.strip('.')
        
        return f"{local_part}@{domain}"
    
    def anonymize_text(self, text: str) -> str:
        """
        Anonimiza PII em texto livre com melhor performance
        """
        if not text or not isinstance(text, str):
            return text
        
        text_str = str(text).strip()
        
        if len(text_str) < 10:  # Muito curto para conter PII relevante
            return text
        
        anonymized_text = text_str
        replacements = []  # Lista de (start, end, original, replacement)
        
        # Fase 1: Detectar e coletar emails
        for email_match in self.email_pattern.finditer(text_str):
            original_email = email_match.group()
            anonymized_email = self.anonymize_email(original_email)
            
            if original_email != anonymized_email:
                replacements.append((
                    email_match.start(),
                    email_match.end(),
                    original_email,
                    anonymized_email
                ))
        
        # Fase 2: Detectar nomes com spaCy
        try:
            doc = self.nlp(text_str)
            
            for ent in doc.ents:
                if ent.label_ != "PER":
                    continue
                
                # Skip se overlap com email
                overlaps = any(
                    start <= ent.start_char < end or start < ent.end_char <= end
                    for start, end, _, _ in replacements
                )
                if overlaps:
                    continue
                
                original_name = ent.text
                
                # Validar se realmente parece nome
                if not self._looks_like_name(original_name):
                    continue
                
                anonymized_name = self.anonymize_name(original_name)
                
                if original_name != anonymized_name:
                    replacements.append((
                        ent.start_char,
                        ent.end_char,
                        original_name,
                        anonymized_name
                    ))
        except Exception as e:
            self.stats['spacy_errors'] += 1
            # Continuar com replacements já coletados
        
        # Fase 3: Aplicar substituições de trás para frente
        replacements.sort(key=lambda x: x[0], reverse=True)
        
        for start, end, original, replacement in replacements:
            anonymized_text = (
                anonymized_text[:start] +
                replacement +
                anonymized_text[end:]
            )
            self.stats['text_replacements'] += 1
        
        return anonymized_text
    
    def get_statistics(self) -> Dict:
        """
        Retorna estatísticas detalhadas da anonimização
        """
        return {
            'detection': {
                'email_attempts': self.stats.get('email_detection_attempts', 0),
                'email_success': self.stats.get('email_detection_success', 0),
                'name_attempts': self.stats.get('name_detection_attempts', 0),
                'name_success': self.stats.get('name_detection_success', 0),
            },
            'anonymization': {
                'unique_names': self.stats.get('unique_names_anonymized', 0),
                'unique_emails': self.stats.get('unique_emails_anonymized', 0),
                'total_name_ops': self.stats.get('total_name_operations', 0),
                'total_email_ops': self.stats.get('total_email_operations', 0),
                'text_replacements': self.stats.get('text_replacements', 0),
            },
            'errors': {
                'spacy_errors': self.stats.get('spacy_errors', 0),
            },
            'mappings': {
                'total_names_mapped': len(self.name_mapping),
                'total_emails_mapped': len(self.email_mapping),
            },
            'sample_mappings': {
                'names': dict(list(self.name_mapping.items())[:5]),
                'emails': dict(list(self.email_mapping.items())[:3])
            },
            'cache': {
                'spacy_cache_size': len(self._spacy_cache)
            }
        }
    
    def clear_cache(self):
        """
        Limpa caches para liberar memória
        """
        self._spacy_cache.clear()
        self.stats['cache_clears'] = self.stats.get('cache_clears', 0) + 1