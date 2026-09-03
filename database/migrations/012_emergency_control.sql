CREATE TABLE IF NOT EXISTS execution_emergency_control (
    control_id SMALLINT PRIMARY KEY CHECK (control_id = 1),
    active BOOLEAN NOT NULL,
    reason TEXT NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

INSERT INTO execution_emergency_control (control_id, active, reason, updated_at)
VALUES (1, TRUE, 'fail-closed initial state', NOW())
ON CONFLICT (control_id) DO NOTHING;
