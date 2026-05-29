"""
database/sample_data.sql  — Insert sample data after running schema.sql
Run in Supabase SQL Editor after tables are created.
Departments are already seeded by schema.sql.
"""

-- ============================================================
-- NOTE: Run this AFTER creating your auth users manually or
-- via the admin panel. Replace the UUIDs with actual user IDs
-- from your auth.users table.
-- This script shows the STRUCTURE for sample data insertion.
-- ============================================================

-- ── Sample Research Entries (use real faculty UUIDs) ───────
-- Replace 'YOUR-FACULTY-UUID-1' etc. with actual UUIDs

-- INSERT INTO public.research_entries (
--     faculty_id, title, research_type, journal_or_patent_office,
--     indexing, impact_factor, authors, status, submission_date,
--     month, year, department, academic_year, is_nba_relevant
-- ) VALUES
-- (
--     'YOUR-FACULTY-UUID-1',
--     'Deep Learning-based Automated Crop Disease Detection Using CNN',
--     'Publication',
--     'IEEE Transactions on Neural Networks and Learning Systems',
--     'Scopus', 4.512,
--     'Smith J., Kumar A., Patel R.',
--     'Published',
--     '2024-09-15', 9, 2024,
--     'Computer Science and Engineering',
--     '2024-25', TRUE
-- ),
-- (
--     'YOUR-FACULTY-UUID-1',
--     'IoT-based Smart Water Quality Monitoring System',
--     'Patent',
--     'Indian Patent Office',
--     NULL, NULL,
--     'Kumar A., Smith J.',
--     'Filed',
--     '2024-07-20', 7, 2024,
--     'Computer Science and Engineering',
--     '2024-25', TRUE
-- ),
-- (
--     'YOUR-FACULTY-UUID-2',
--     'SERB-funded Research on Quantum Computing Applications',
--     'Research Proposal',
--     NULL,
--     NULL, NULL,
--     'Patel R.',
--     'Approved',
--     '2024-06-01', 6, 2024,
--     'Electronics and Communication Engineering',
--     '2024-25', TRUE
-- );

-- ============================================================
-- To quickly create demo users via Supabase Dashboard:
-- 1. Go to Authentication → Users → Invite User
-- 2. Or use the Registration form in the app
-- 3. Admin can assign roles via the Admin panel
-- ============================================================

-- ── View to check data integrity ─────────────────────────
CREATE OR REPLACE VIEW public.research_with_faculty AS
SELECT
    re.*,
    p.full_name  AS faculty_name,
    p.email      AS faculty_email,
    p.department AS faculty_department
FROM public.research_entries re
LEFT JOIN public.profiles p ON p.id = re.faculty_id;
