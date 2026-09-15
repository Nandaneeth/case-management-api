-- Educational SQL examples for the case-management database.
-- These examples use the existing cases table unless noted otherwise.

-- 1. SELECT: retrieve selected columns from every case.
SELECT id, case_number, title, status, priority
FROM cases;

-- 2. INSERT: add one new case.
-- created_at and updated_at use their database defaults.
INSERT INTO cases (case_number, title, description, status, priority)
VALUES (
    'CASE-100',
  'Failed payment at checkout',
  'Customer reports that a card payment fails at checkout despite having sufficient funds.',
    'open',
    'medium'
);

-- 3. UPDATE: change the status and priority of one case.
UPDATE cases
SET status = 'in_progress',
    priority = 'high',
    updated_at = CURRENT_TIMESTAMP
WHERE case_number = 'CASE-100';

-- 4. WHERE: return only open, high-priority cases.
SELECT id, case_number, title
FROM cases
WHERE status = 'open'
  AND priority = 'high';

-- 5. ORDER BY: list the newest cases first.
SELECT id, case_number, title, created_at
FROM cases
ORDER BY created_at DESC;

-- 6. GROUP BY: count how many cases exist in each status.
SELECT status, COUNT(*) AS case_count
FROM cases
GROUP BY status
ORDER BY status;

-- 7. JOIN: hypothetical example using a related case_assignments table.
-- The application does not create this table; it is shown only for training.
-- Assume case_assignments has case_id and assignee_name columns.
SELECT cases.case_number, cases.title, case_assignments.assignee_name
FROM cases
JOIN case_assignments
  ON case_assignments.case_id = cases.id;

-- 8. CTE: first find open cases, then query the named result.
WITH open_cases AS (
    SELECT id, case_number, title, priority
    FROM cases
    WHERE status = 'open'
)
SELECT case_number, title, priority
FROM open_cases
ORDER BY priority, case_number;

-- 9. Window function: number cases within each status by newest first.
-- Unlike GROUP BY, this keeps every individual case row.
SELECT
    case_number,
    status,
    created_at,
    ROW_NUMBER() OVER (
        PARTITION BY status
        ORDER BY created_at DESC
    ) AS status_position
FROM cases;

-- 10. Transaction: make a change that can be committed or rolled back.
BEGIN TRANSACTION;

UPDATE cases
SET priority = 'critical',
    updated_at = CURRENT_TIMESTAMP
WHERE case_number = 'CASE-100';

-- Use COMMIT to keep the change.
COMMIT;

-- Use ROLLBACK instead of COMMIT to undo the transaction.
-- ROLLBACK;
