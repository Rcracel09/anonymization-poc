# Sistema de Anonimização - E-Catalog LTPLabs

Sistema automatizado para anonimização de dados em PostgreSQL e MongoDB.

## 🚀 Quick Start
```bash
# 1. Clonar repo
git clone https://github.com/your-org/anonymization-poc.git

# 2. Setup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m spacy download pt_core_news_lg


# 3. Iniciar BDs de teste
cd docker && docker-compose up -d

# 4. Configurar
cp .env.example .env

# 5. Executar
python scripts/anonymize_postgresql.py
```

## 📖 Documentação Completa

Ver [GUIA_IMPLEMENTACAO.md](./docs/GUIA_IMPLEMENTACAO.md)