# 🔒 Sistema de Anonimização Automática de PII

## 🎯 O Que Este Sistema Faz

Este sistema **detecta e anonimiza automaticamente** todos os emails e nomes em **qualquer base de dados** sem precisar de configuração manual.

## ✨ Principais Características

### Antes (Sistema Original)
❌ Precisava de ficheiro YAML com configuração manual  
❌ Só funcionava com schemas conhecidos  
❌ Perdia PII em campos de texto  

### Agora (Sistema Novo)
✅ **Zero configuração** - funciona automaticamente  
✅ Funciona com **qualquer schema** de base de dados  
✅ Deteta nomes e emails em todo o lado  
✅ Suporta campos nested no MongoDB  
✅ Mantém consistência (mesmo original → mesmo fake)  

## 🚀 Instalação Rápida (5 minutos)

### 1. Instalar Dependências
```bash
pip install -r requirements.txt
python -m spacy download pt_core_news_lg
```

### 2. Configurar Ambiente
```bash
cp .env.example .env
# Editar .env com as suas credenciais de base de dados
```

### 3. Iniciar Bases de Dados de Teste
```bash
docker-compose up -d
sleep 15
```

### 4. Executar Anonimização
```bash
# PostgreSQL
python -m src.scripts.anonymize_postgresql

# MongoDB
python -m src.scripts.anonymize_mongodb
```

## 🔍 Como Funciona a Detecção

### Detecção de Emails
- 🔍 Palavras-chave: `email`, `mail`, `correio`, `contact`
- 🔍 Padrão regex para validar emails
- 🔍 Analisa conteúdo: se >50% são emails → campo de email

### Detecção de Nomes
- 🔍 Palavras-chave: `name`, `nome`, `author`, `pessoa`, `reviewer`
- 🔍 spaCy NLP: deteta entidades PERSON
- 🔍 Heurísticas: 2-4 palavras capitalizadas
- 🔍 Analisa conteúdo: se >40% parecem nomes → campo de nome

### Processo em 2 Fases
**Fase 1:** Colunas estruturadas (campos dedicados de nome/email)  
**Fase 2:** Texto livre (encontra PII embutido em descrições, notas, etc.)

## 📊 Exemplos de Schemas Detetados

O sistema deteta automaticamente todos estes padrões:

### PostgreSQL
```sql
-- Padrão Inglês
CREATE TABLE customers (
    customer_name VARCHAR(100),     -- ✅ Detetado
    contact_email VARCHAR(100)      -- ✅ Detetado
);

-- Padrão Português  
CREATE TABLE contactos (
    pessoa VARCHAR(100),            -- ✅ Detetado
    mail VARCHAR(100)               -- ✅ Detetado
);

-- Sem palavras-chave óbvias
CREATE TABLE data (
    field1 VARCHAR(100),            -- Contém "João Silva" 
    field2 VARCHAR(100)             -- Contém "joao@email.com"
);
-- ✅ Detetado pela análise de conteúdo!
```

### MongoDB
```javascript
// Campos simples
{ 
    name: "João Silva",             // ✅ Detetado
    email: "joao@example.com"       // ✅ Detetado
}

// Campos nested
{
    reviewer: {
        name: "Maria Santos",       // ✅ Detetado como reviewer.name
        email: "maria@blog.com"     // ✅ Detetado como reviewer.email
    }
}

// Arrays
{
    team: [
        { member_name: "Pedro Costa" }  // ✅ Detetado
    ]
}
```

## 🧪 Bases de Dados de Teste Incluídas

Incluí **15+ estruturas diferentes** para testar:

### PostgreSQL (7 tabelas)
- E-commerce: `customers`, `orders`
- RH: `employees` com metadata
- CMS: `articles` com PII embutido
- Suporte: `tickets` com estrutura complexa
- Nomes portugueses: `contactos`, `pessoa`, `correio`

### MongoDB (8 coleções)
- Estruturas simples
- Campos nested (`metadata.author`)
- Arrays de objetos (`team[].member_name`)
- Nesting profundo (`customer.info.full_name`)

## 📁 Estrutura do Projeto

```
anonymization-system/
├── 📄 QUICKSTART.md                # 👈 Comece aqui!
├── 📄 README.md                    # Documentação completa (inglês)
├── 📄 LEIA-ME.md                   # Este ficheiro
├── 📄 SUMMARY.md                   # Resumo completo
├── 📄 CHANGES.md                   # O que mudou
├── 📄 ARCHITECTURE.md              # Diagramas do sistema
│
├── src/scripts/                    # Sistema principal
│   ├── anonymizer.py               # 🧠 Lógica de detecção
│   ├── anonymize_postgresql.py     # PostgreSQL
│   └── anonymize_mongodb.py        # MongoDB
│
├── docker/                         # Dados de teste
│   ├── init-postgres-varied.sql    # 7 tabelas variadas
│   └── init-mongo-varied.js        # 8 coleções variadas
│
├── tests/                          # 29 testes
│   ├── test_auto_detection.py      # Testes de detecção
│   └── ...
│
└── .github/workflows/              # GitHub Actions
    └── anonymize-auto-demo.yml
```

## 💡 Exemplo de Uso

```python
from src.scripts.anonymize_postgresql import PostgreSQLAnonymizer

# Inicializar (sem configuração!)
anonymizer = PostgreSQLAnonymizer()

# Auto-detecção e anonimização
anonymizer.anonymize_all()

# Segunda passagem para texto livre
anonymizer.anonymize_text_columns()

anonymizer.close()
```

## 📊 O Que Vai Ver

```
🔒 Iniciando anonimização automática PostgreSQL...

📊 Encontradas 7 tabelas: customers, employees, articles...

📋 Processando tabela: customers
   Colunas: id, customer_name, contact_email, created_at

🔍 Detectando colunas com PII...
   ✓ customer_name → NAME
   ✓ contact_email → EMAIL

   ✓ customer_name (name): 4 registos anonimizados
   ✓ contact_email (email): 4 registos anonimizados

✅ PostgreSQL anonimizado com sucesso!
📊 Total de campos anonimizados: 35
```

## ✅ Garantia de Consistência

O sistema mantém consistência em todos os locais:

**Base de Dados Original:**
```
João Silva | joao.silva@example.com | "Contactar João Silva"
João Silva | joao.silva@example.com | "Autor: João Silva"  
```

**Depois da Anonimização:**
```
Ricardo Fernandes | ricardo89@example.org | "Contactar Ricardo Fernandes"
Ricardo Fernandes | ricardo89@example.org | "Autor: Ricardo Fernandes"
```

✅ Mesmo original → Mesmo fake em todo o lado!

## 🧪 Executar Testes

```bash
# Todos os testes
pytest tests/ -v

# Apenas testes de detecção
pytest tests/test_auto_detection.py -v

# Com cobertura
pytest tests/ --cov=src --cov-report=html
```

## 🚨 Checklist para Produção

Antes de executar em produção:

- [ ] **Fazer backup da base de dados!**
- [ ] Testar numa cópia/staging primeiro
- [ ] Rever colunas detetadas nos logs
- [ ] Verificar registos anonimizados de amostra
- [ ] Confirmar que não ficou PII por anonimizar

## 🔧 Personalização

### Ajustar Sensibilidade de Detecção

Editar `src/scripts/anonymizer.py`:

```python
# Threshold de emails (padrão 50%)
return email_count / len(sample_values) > 0.5  # Alterar para 0.7 para mais rigoroso

# Threshold de nomes (padrão 40%)  
return person_count / total > 0.4  # Alterar para 0.6 para mais rigoroso
```

### Adicionar Palavras-Chave Personalizadas

```python
self.name_keywords = [
    # Adicionar as suas palavras-chave
    'username', 'cliente_nome', 'utilizador'
]
```

## 📚 Documentação

1. **QUICKSTART.md** - Guia de instalação rápida
2. **README.md** - Documentação técnica completa
3. **SUMMARY.md** - Resumo abrangente do sistema
4. **CHANGES.md** - O que mudou do sistema original
5. **ARCHITECTURE.md** - Diagramas e arquitectura

## 🤝 Suporte

**Precisa de Ajuda?**

1. Consulte o QUICKSTART.md para instalação
2. Consulte o README.md para documentação completa
3. Reveja os ficheiros de teste para exemplos
4. Abra uma issue no GitHub

## 🎯 Características Principais

- ✅ **Zero Configuração** - Não precisa de ficheiros YAML
- ✅ **Universal** - Funciona com qualquer schema
- ✅ **Inteligente** - Usa NLP + Regex + Keywords
- ✅ **Abrangente** - Encontra PII em todo o lado
- ✅ **Consistente** - Mesmo original → mesmo fake
- ✅ **Escalável** - Funciona com bases de dados grandes
- ✅ **Testado** - 29 testes abrangentes
- ✅ **Documentado** - Guias extensivos

## 🚀 Próximos Passos

1. **Teste Localmente**: Use docker-compose para testar
2. **Execute Testes**: Valide a funcionalidade
3. **Teste com Cópia**: Use numa cópia da sua BD
4. **Produção**: Execute na base de dados real (com backup!)

---

**⚡ Construído para tratamento de dados com privacidade em primeiro lugar**

*Dúvidas? Problemas? Abra uma issue no GitHub!*
