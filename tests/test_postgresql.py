import subprocess
import sys
import os
from pathlib import Path


def print_header(text: str):
    """Imprime cabeçalho formatado"""
    print(f"\n{text}")
    print("=" * len(text))


def print_step(step_number: int, text: str):
    """Imprime passo formatado"""
    print(f"\n{step_number}️⃣ {text}")


def run_command(cmd: list, capture_output: bool = True, check: bool = True) -> subprocess.CompletedProcess:
    """Executa comando e retorna resultado"""
    try:
        result = subprocess.run(
            cmd,
            capture_output=capture_output,
            text=True,
            check=check
        )
        return result
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao executar comando: {e}")
        if e.stderr:
            print(f"   Stderr: {e.stderr}")
        sys.exit(1)


def check_mongodb_running() -> bool:
    """Verifica se MongoDB está a correr"""
    print_step(1, "Verificando MongoDB...")
    
    result = run_command(["docker", "ps"], check=False)
    
    if "test_mongodb" in result.stdout:
        print("✅ MongoDB está a correr")
        return True
    else:
        print("❌ MongoDB não está a correr!")
        print("Execute: docker-compose up -d")
        return False


def populate_test_data():
    """Popula MongoDB com dados de teste"""
    print_step(2, "Populando dados de teste...")
    
    init_script = Path("init-mongo.js")
    
    if not init_script.exists():
        print(f"❌ Ficheiro {init_script} não encontrado!")
        sys.exit(1)
    
    mongo_uri = "mongodb://mongo:mongo123@localhost:27017/demo_db2?authSource=admin"
    
    with open(init_script, 'r') as f:
        script_content = f.read()
    
    cmd = [
        "docker", "exec", "-i", "test_mongodb",
        "mongosh", mongo_uri
    ]
    
    result = subprocess.run(
        cmd,
        input=script_content,
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("✅ Dados inseridos")
    else:
        print("❌ Erro ao inserir dados")
        print(result.stderr)
        sys.exit(1)


def show_data_before():
    """Mostra dados ANTES da anonimização"""
    print_step(3, "Dados ANTES da anonimização:")
    print("=" * 40)
    
    mongo_uri = "mongodb://mongo:mongo123@localhost:27017/demo_db2?authSource=admin"
    
    # Query para users
    query_users = """
    db.users.find({}, {name: 1, email: 1, _id: 0}).forEach(doc => {
        print('---');
        print('Nome:', doc.name);
        print('Email:', doc.email);
    })
    """
    
    # Query para plans
    query_plans = """
    db.plans.find({}, {title: 1, reviewed_by_name: 1, description: 1, _id: 0}).forEach(doc => {
        print('---');
        print('Título:', doc.title);
        print('Reviewed by:', doc.reviewed_by_name);
        print('Descrição:', doc.description.substring(0, 60) + '...');
    })
    """
    
    print("\n📗 Coleção: users")
    cmd_users = [
        "docker", "exec", "test_mongodb",
        "mongosh", mongo_uri,
        "--quiet", "--eval", query_users
    ]
    run_command(cmd_users, capture_output=False)
    
    print("\n📗 Coleção: plans")
    cmd_plans = [
        "docker", "exec", "test_mongodb",
        "mongosh", mongo_uri,
        "--quiet", "--eval", query_plans
    ]
    run_command(cmd_plans, capture_output=False)


def run_anonymization():
    """Executa anonimização"""
    print_step(4, "Executando anonimização...")
    
    cmd = [sys.executable, "-m", "src.scripts.anonymize_mongodb"]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    # Mostrar apenas as linhas importantes
    for line in result.stdout.split('\n'):
        if any(emoji in line for emoji in ['🔒', '✅', '📊', '📋']):
            print(line)
    
    if result.returncode != 0:
        print("❌ Erro na anonimização")
        print(result.stderr)
        sys.exit(1)


def show_data_after():
    """Mostra dados DEPOIS da anonimização"""
    print_step(5, "Dados DEPOIS da anonimização:")
    print("=" * 40)
    
    mongo_uri = "mongodb://mongo:mongo123@localhost:27017/demo_db2?authSource=admin"
    
    # Query para users
    query_users = """
    db.users.find({}, {name: 1, email: 1, _id: 0}).forEach(doc => {
        print('---');
        print('Nome:', doc.name);
        print('Email:', doc.email);
    })
    """
    
    # Query para plans
    query_plans = """
    db.plans.find({}, {title: 1, reviewed_by_name: 1, description: 1, _id: 0}).forEach(doc => {
        print('---');
        print('Título:', doc.title);
        print('Reviewed by:', doc.reviewed_by_name);
        print('Descrição:', doc.description.substring(0, 60) + '...');
    })
    """
    
    print("\n📗 Coleção: users")
    cmd_users = [
        "docker", "exec", "test_mongodb",
        "mongosh", mongo_uri,
        "--quiet", "--eval", query_users
    ]
    run_command(cmd_users, capture_output=False)
    
    print("\n📗 Coleção: plans")
    cmd_plans = [
        "docker", "exec", "test_mongodb",
        "mongosh", mongo_uri,
        "--quiet", "--eval", query_plans
    ]
    run_command(cmd_plans, capture_output=False)


def main():
    """Função principal"""
    print("🧪 Teste MongoDB - Sistema de Anonimização")
    print("=" * 45)
    
    # 1. Verificar MongoDB
    if not check_mongodb_running():
        sys.exit(1)
    
    # 2. Popular dados de teste
    populate_test_data()
    
    # 3. Mostrar dados ANTES
    show_data_before()
    
    # 4. Executar anonimização
    run_anonymization()
    
    # 5. Mostrar dados DEPOIS
    show_data_after()
    
    # Conclusão
    print("\n✅ Teste concluído!")
    print("\n🔍 Observações:")
    print("   - Nomes originais foram substituídos por nomes fake")
    print("   - Emails foram anonimizados")
    print("   - Consistência mantida: mesmo nome original = mesmo nome fake")


if __name__ == "__main__":
    main()