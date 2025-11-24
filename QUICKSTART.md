# 🚀 Quick Start Guide

## 1. Install Dependencies

```bash
# Install Python packages
pip install -r requirements.txt

# Download spaCy Portuguese model (required for name detection)
python -m spacy download pt_core_news_lg
```

## 2. Setup Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your database credentials
# (default values work with docker-compose)
nano .env
```

## 3. Start Test Databases

```bash
# Start PostgreSQL and MongoDB containers
docker-compose up -d

# Wait for databases to be ready (about 10-15 seconds)
sleep 15

# Verify containers are running
docker ps
```

## 4. Run Anonymization

### Option A: Run Both (Recommended)
```bash
# Anonymize PostgreSQL
python -m src.scripts.anonymize_postgresql

# Anonymize MongoDB
python -m src.scripts.anonymize_mongodb
```

### Option B: Run Tests
```bash
# Run all tests including integration tests
pytest tests/ -v

# Run just auto-detection tests
pytest tests/test_auto_detection.py -v
```

## 5. Verify Results

### PostgreSQL
```bash
# Connect to PostgreSQL
docker exec -it test_postgres psql -U postgres -d demo_db

# Check tables
\dt

# View anonymized data
SELECT * FROM customers LIMIT 5;

# Exit
\q
```

### MongoDB
```bash
# Connect to MongoDB
docker exec -it test_mongodb mongosh "mongodb://mongo:mongo123@localhost:27017/demo_db2?authSource=admin"

# Show collections
show collections

# View anonymized data
db.customers.find().limit(5)

# Exit
exit
```

## 6. Stop Databases

```bash
# Stop containers
docker-compose down

# To also remove volumes (will delete all data):
docker-compose down -v
```

## What You Should See

### During Anonymization:

```
🔒 Iniciando anonimização automática PostgreSQL...

📊 Encontradas 7 tabelas: customers, employees, articles, ...

📋 Processando tabela: customers
   Colunas: id, customer_name, contact_email, created_at

🔍 Detectando colunas com PII...
   ✓ customer_name → NAME
   ✓ contact_email → EMAIL

   ✓ customer_name (name): 4 registos anonimizados
   ✓ contact_email (email): 4 registos anonimizados

...

✅ PostgreSQL anonimizado com sucesso!
📊 Total de campos anonimizados: 35
📊 Estatísticas: {
  'total_names_anonymized': 18,
  'total_emails_anonymized': 17
}

🔍 Segunda passagem: Detectando PII em campos de texto livre...
   ✓ content: 2 registos processados
```

## Troubleshooting

### Issue: spaCy model not found
```bash
python -m spacy download pt_core_news_lg
```

### Issue: Port already in use
```bash
# Stop any existing containers
docker-compose down

# Or change ports in docker-compose.yml
```

### Issue: Permission denied
```bash
# On Linux, you might need to add your user to docker group
sudo usermod -aG docker $USER
# Then log out and log back in
```

### Issue: Connection refused
```bash
# Check if containers are running
docker ps

# Check container logs
docker logs test_postgres
docker logs test_mongodb

# Restart containers
docker-compose restart
```

## Next Steps

1. **Customize Detection**: Edit thresholds in `src/scripts/anonymizer.py`
2. **Add Your Database**: Update `.env` with your database credentials
3. **Test on Copy**: Always test on a database copy first!
4. **GitHub Actions**: Push to GitHub and use the workflow for CI/CD

## GitHub Actions Usage

1. Push your code to GitHub
2. Go to **Actions** tab
3. Select **"Anonymization Auto-Detection Demo"**
4. Click **"Run workflow"**
5. Choose test scenario:
   - **varied**: Tests 15+ different schemas (recommended)
   - **simple**: Basic test
   - **both**: Runs both scenarios
6. View results in workflow logs

## Learn More

- Read the full [README.md](README.md) for detailed documentation
- Check [CHANGES.md](CHANGES.md) for what's new in this version
- Review test files in `tests/` for usage examples

---

**Need help? Open an issue on GitHub!**
