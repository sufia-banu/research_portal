-- ============================================================
-- HKBK College — Engineering Departments ONLY
-- Run in Supabase SQL Editor AFTER rls_fix.sql
-- ============================================================

-- Safe upsert — won't error if departments already exist
INSERT INTO public.departments (department_name, code) VALUES
  ('Computer Science and Engineering',             'CSE'),
  ('Information Science and Engineering',          'ISE'),
  ('Artificial Intelligence and Machine Learning', 'AIML'),
  ('Electronics and Communication Engineering',    'ECE'),
  ('Mechanical Engineering',                       'ME'),
  ('Civil Engineering',                            'CE'),
  ('Basic Science',                                'BS')
ON CONFLICT (department_name) DO UPDATE
  SET code = EXCLUDED.code;

-- Remove any previously seeded non-engineering departments
DELETE FROM public.departments
WHERE department_name IN (
  'Master of Business Administration',
  'Master of Computer Applications',
  'MBA', 'MCA',
  'PhD in Computer Science',
  'PhD in Electronics and Communication',
  'PhD in Mechanical Engineering',
  'PhD in Civil Engineering',
  'PhD in Physics',
  'PhD in Chemistry',
  'PhD in Mathematics',
  'PhD in Management Studies',
  'Electrical and Electronics Engineering',
  'Biotechnology',
  'Mathematics',
  'Physics',
  'Chemistry',
  'Management Studies'
);

-- Verify — should show exactly 7 rows
SELECT code, department_name FROM public.departments ORDER BY code;
