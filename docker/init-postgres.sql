CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE plans (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200),
    reviewed_by_name VARCHAR(100),
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Inserir dados de TESTE (para anonimizar)
INSERT INTO users (name, email) VALUES
    ('João Silva', 'joao.silva@empresa.pt'),
    ('Maria Santos', 'maria.santos@empresa.pt'),
    ('Pedro Oliveira', 'pedro.oliveira@empresa.pt');

INSERT INTO plans (title, reviewed_by_name, description) VALUES
    (
        'Plano Q1 2025', 
        'João Silva',
        'Plano revisto por João Silva e aprovado por Maria Santos em reunião dia 10/11'
    ),
    (
        'Estratégia Marketing',
        'Maria Santos',
        'Maria Santos coordenou com Pedro Oliveira para definir KPIs'
    );