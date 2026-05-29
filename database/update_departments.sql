-- =================================================================================
-- database/update_departments.sql
-- Run this in your Supabase SQL Editor to sync the departments
-- =================================================================================

-- 1. Remove the unwanted departments
DELETE FROM public.departments WHERE department_name = 'Biotechnology';
DELETE FROM public.departments WHERE department_name = 'Civil Engineering';
DELETE FROM public.departments WHERE department_name = 'Electrical and Electronics Engineering';
DELETE FROM public.departments WHERE department_name = 'Management Studies';
DELETE FROM public.departments WHERE department_name = 'Mathematics';
DELETE FROM public.departments WHERE department_name = 'Physics';
DELETE FROM public.departments WHERE department_name = 'Chemistry';

-- 2. Add the new department
INSERT INTO public.departments (department_name, code) VALUES 
('Humanities', 'HUM')
ON CONFLICT (department_name) DO NOTHING;

-- Reload schema cache just in case
NOTIFY pgrst, 'reload schema';
