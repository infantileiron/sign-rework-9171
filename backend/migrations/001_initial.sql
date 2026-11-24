CREATE TABLE IF NOT EXISTS accounts (
    email varchar(100) PRIMARY KEY,
    display_name varchar(60) NOT NULL,
    password_hash text NOT NULL,
    role varchar(12) NOT NULL CHECK (role IN ('owner', 'analyst', 'viewer'))
);

CREATE TABLE IF NOT EXISTS crews (
    code varchar(8) PRIMARY KEY,
    name varchar(60) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS orders (
    code varchar(20) PRIMARY KEY,
    title varchar(90) NOT NULL,
    crew varchar(8) NOT NULL REFERENCES crews(code),
    minutes double precision NOT NULL CHECK (minutes >= 0.01 AND minutes <= 180),
    shots integer NOT NULL CHECK (shots BETWEEN 1 AND 1000),
    switches integer NOT NULL CHECK (switches BETWEEN 0 AND 1000 AND switches <= shots - 1),
    hours double precision NOT NULL CHECK (hours BETWEEN 0 AND 200)
);

CREATE TABLE IF NOT EXISTS plans (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name varchar(64) NOT NULL UNIQUE,
    alpha double precision NOT NULL CHECK (alpha BETWEEN 0.001 AND 100),
    features text[] NOT NULL CHECK (cardinality(features) BETWEEN 1 AND 3),
    created_by varchar(100) NOT NULL REFERENCES accounts(email),
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS reports (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    plan_id bigint NOT NULL REFERENCES plans(id),
    plan_name varchar(64) NOT NULL,
    holdout varchar(8) NOT NULL REFERENCES crews(code),
    snapshot jsonb NOT NULL,
    fingerprint char(64) NOT NULL,
    status varchar(12) NOT NULL DEFAULT 'queued'
        CHECK (status IN ('queued', 'succeeded', 'failed', 'published')),
    result jsonb,
    error text,
    created_by varchar(100) NOT NULL REFERENCES accounts(email),
    created_at timestamptz NOT NULL DEFAULT now(),
    completed_at timestamptz,
    published_by varchar(100) REFERENCES accounts(email),
    published_at timestamptz
);

CREATE INDEX IF NOT EXISTS reports_queue ON reports (id) WHERE status = 'queued';

CREATE TABLE IF NOT EXISTS audit (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    actor varchar(100) REFERENCES accounts(email),
    action varchar(30) NOT NULL,
    entity_key text NOT NULL,
    occurred_at timestamptz NOT NULL DEFAULT now()
);

INSERT INTO crews (code, name) VALUES
    ('G01', '晨桥组'), ('G02', '松影组'), ('G03', '雨廊组'),
    ('G04', '灯塔组'), ('G05', '石阶组'), ('G06', '渡口组')
ON CONFLICT DO NOTHING;
