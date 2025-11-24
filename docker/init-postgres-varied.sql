-- ========================================
-- Customers table (obvious field names)
-- ========================================

CREATE TABLE IF NOT EXISTS customers (
    id SERIAL PRIMARY KEY,
    customer_name VARCHAR(150),
    contact_email VARCHAR(150),
    created_at TIMESTAMP DEFAULT NOW()
);

INSERT INTO customers (customer_name, contact_email) VALUES
    ('João Silva', 'joao.silva@example.com'),
    ('Maria Santos Ferreira', 'maria.santos@example.com'),
    ('Pedro Oliveira Costa', 'pedro.oliveira@example.com'),
    ('Ana Paula Rodrigues', 'ana.rodrigues@example.com');

-- ==================================================
-- Employees table (different naming conventions)
-- ==================================================

CREATE TABLE IF NOT EXISTS employees (
    id SERIAL PRIMARY KEY,
    full_name VARCHAR(200),
    work_email VARCHAR(200),
    personal_mail VARCHAR(200),
    department VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);

INSERT INTO employees (full_name, work_email, personal_mail, department) VALUES
    ('Carlos Alberto Mendes', 'carlos.mendes@company.pt', 'carlos123@gmail.com', 'Engineering'),
    ('Sofia Isabel Costa', 'sofia.costa@company.pt', 'sofia.costa@yahoo.com', 'Marketing'),
    ('Ricardo Manuel Pereira', 'ricardo.pereira@company.pt', 'rpereira@hotmail.com', 'Sales');

-- ================================================
-- Articles table (names and emails in content )
-- ================================================

CREATE TABLE IF NOT EXISTS articles (
    id SERIAL PRIMARY KEY,
    title VARCHAR(300),
    author_name VARCHAR(150),
    content TEXT,
    reviewer_email VARCHAR(150),
    published_at TIMESTAMP DEFAULT NOW()
);

INSERT INTO articles (title, author_name, content, reviewer_email) VALUES
    (
        'Introduction to Python', 
        'Miguel Ângelo Ferreira',
        'This article was written by Miguel Ângelo Ferreira and reviewed by Teresa Santos. Contact: miguel.ferreira@blog.com for more info.',
        'teresa.santos@blog.com'
    ),
    (
        'JavaScript Best Practices',
        'Beatriz Marques',
        'Article by Beatriz Marques, edited by João Pedro Silva. For questions, reach out to beatriz.marques@blog.com',
        'joao.silva@blog.com'
    );

-- ========================================
-- Tickets table (nested field names)
-- ========================================

CREATE TABLE IF NOT EXISTS support_tickets (
    id SERIAL PRIMARY KEY,
    ticket_subject VARCHAR(200),
    requester_nome VARCHAR(150),
    requester_correio VARCHAR(150),
    assigned_to_person VARCHAR(150),
    description TEXT,
    status VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

INSERT INTO support_tickets (ticket_subject, requester_nome, requester_correio, assigned_to_person, description, status) VALUES
    (
        'Cannot login to system',
        'Luís Fernando Alves',
        'luis.alves@client.com',
        'Tiago Rodrigues',
        'User Luís Fernando Alves reported login issues. Assigned to support agent Tiago Rodrigues (tiago.rodrigues@support.com)',
        'open'
    ),
    (
        'Payment not processed',
        'Carla Pereira',
        'carla.pereira@client.com',
        'Sandra Costa',
        'Customer Carla Pereira (carla.pereira@client.com) contacted Sandra Costa regarding payment issues.',
        'pending'
    );

-- ========================================
-- Projects table 
-- ========================================

CREATE TABLE IF NOT EXISTS projects (
    id SERIAL PRIMARY KEY,
    project_name VARCHAR(200),
    project_owner VARCHAR(150),
    collaborator_emails TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

INSERT INTO projects (project_name, project_owner, collaborator_emails, notes) VALUES
    (
        'Website Redesign Q1 2025',
        'Rui Miguel Santos',
        'rui.santos@company.com, maria.silva@company.com, pedro.costa@company.com',
        'Project led by Rui Miguel Santos. Key stakeholders: Maria Silva and Pedro Costa. Weekly meetings every Monday.'
    ),
    (
        'Mobile App Development',
        'Inês Marques',
        'ines.marques@company.com, antonio.pereira@company.com',
        'Managed by Inês Marques with support from António Pereira (antonio.pereira@company.com)'
    );

-- ========================================
-- Contacts table (non-standard naming)
-- ========================================

CREATE TABLE IF NOT EXISTS contacts (
    id SERIAL PRIMARY KEY,
    pessoa VARCHAR(150),
    mail VARCHAR(150),
    telefone VARCHAR(20),
    observacoes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

INSERT INTO contacts (pessoa, mail, telefone, observacoes) VALUES
    ('Francisco José Lima', 'francisco.lima@example.com', '+351912345678', 'Contact Francisco José Lima for partnership inquiries at francisco.lima@example.com'),
    ('Cristina Ferreira', 'cristina.ferreira@example.com', '+351923456789', 'Key account: Cristina Ferreira, reach via cristina.ferreira@example.com');

-- ========================================
-- Reviews table (Mixed Content)
-- ========================================

CREATE TABLE IF NOT EXISTS reviews (
    id SERIAL PRIMARY KEY,
    product_name VARCHAR(200),
    reviewer VARCHAR(150),
    review_text TEXT,
    reviewer_contact VARCHAR(150),
    rating INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

INSERT INTO reviews (product_name, reviewer, review_text, reviewer_contact, rating) VALUES
    (
        'Laptop Model X',
        'Paulo Alexandre Rocha',
        'Great laptop! Review by Paulo Alexandre Rocha. If you have questions, email me at paulo.rocha@email.com',
        'paulo.rocha@email.com',
        5
    ),
    (
        'Smartphone Pro',
        'Marta Isabel Gomes',
        'Excellent phone. Contact Marta Isabel Gomes (marta.gomes@email.com) for more details about my experience.',
        'marta.gomes@email.com',
        4
    );

