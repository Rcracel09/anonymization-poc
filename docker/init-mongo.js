// Script de inicialização do MongoDB
// Dados idênticos ao PostgreSQL para testes de anonimização

db = db.getSiblingDB('demo_db2');

// =======================
// COLEÇÃO: users
// =======================
db.users.drop();

db.users.insertMany([
    {
        name: "João Silva",
        email: "joao.silva@empresa.pt",
        created_at: new Date()
    },
    {
        name: "Maria Santos",
        email: "maria.santos@empresa.pt",
        created_at: new Date()
    },
    {
        name: "Pedro Oliveira",
        email: "pedro.oliveira@empresa.pt",
        created_at: new Date()
    }
]);

print("✅ Coleção 'users' criada com 3 documentos");

// =======================
// COLEÇÃO: plans
// =======================
db.plans.drop();

db.plans.insertMany([
    {
        title: "Plano Q1 2025",
        reviewed_by_name: "João Silva",
        description: "Plano revisto por João Silva e aprovado por Maria Santos em reunião dia 10/11",
        created_at: new Date()
    },
    {
        title: "Estratégia Marketing",
        reviewed_by_name: "Maria Santos",
        description: "Maria Santos coordenou com Pedro Oliveira para definir KPIs",
        created_at: new Date()
    }
]);

print("✅ Coleção 'plans' criada com 2 documentos");

// =======================
// RESUMO
// =======================
print("\n📊 Resumo da Inicialização:");
print("   - Users:", db.users.countDocuments());
print("   - Plans:", db.plans.countDocuments());

print("\n🔍 Preview dos dados:");
print("\n--- USERS ---");
db.users.find({}, {_id: 0}).forEach(printjson);

print("\n--- PLANS ---");
db.plans.find({}, {_id: 0}).forEach(printjson);