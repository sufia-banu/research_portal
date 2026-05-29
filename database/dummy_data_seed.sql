-- ====================================================================
-- SEED DUMMY USERS AND DATA (SQL VERSION)
-- Run this in your Supabase SQL Editor to create dummy accounts.
-- ====================================================================
-- Password for all accounts will be: password123
-- ====================================================================

CREATE EXTENSION IF NOT EXISTS pgcrypto;

DO $$
DECLARE
  faculty_uid UUID := uuid_generate_v4();
  hod_uid UUID := uuid_generate_v4();
  rd_uid UUID := uuid_generate_v4();
BEGIN

  -- ==========================================
  -- 1. CREATE FACULTY USER
  -- Email: faculty_demo@hkbk.edu
  -- ==========================================
  INSERT INTO auth.users (
    id, instance_id, aud, role, email, encrypted_password, email_confirmed_at, 
    raw_app_meta_data, raw_user_meta_data, created_at, updated_at
  ) VALUES (
    faculty_uid, '00000000-0000-0000-0000-000000000000', 'authenticated', 'authenticated', 
    'faculty_demo@hkbk.edu', crypt('password123', gen_salt('bf')), now(), 
    '{"provider":"email","providers":["email"]}', 
    '{"full_name": "Dr. Faculty Demo", "department": "Computer Science and Engineering", "role": "faculty"}', 
    now(), now()
  );

  INSERT INTO auth.identities (id, user_id, provider_id, provider, identity_data, last_sign_in_at, created_at, updated_at)
  VALUES (
    uuid_generate_v4(), faculty_uid, faculty_uid::text, 'email', 
    jsonb_build_object('sub', faculty_uid, 'email', 'faculty_demo@hkbk.edu'), 
    now(), now(), now()
  );

  -- ==========================================
  -- 2. CREATE HOD USER
  -- Email: hod_demo@hkbk.edu
  -- ==========================================
  INSERT INTO auth.users (
    id, instance_id, aud, role, email, encrypted_password, email_confirmed_at, 
    raw_app_meta_data, raw_user_meta_data, created_at, updated_at
  ) VALUES (
    hod_uid, '00000000-0000-0000-0000-000000000000', 'authenticated', 'authenticated', 
    'hod_demo@hkbk.edu', crypt('password123', gen_salt('bf')), now(), 
    '{"provider":"email","providers":["email"]}', 
    '{"full_name": "Dr. HOD Demo", "department": "Computer Science and Engineering", "role": "hod"}', 
    now(), now()
  );

  INSERT INTO auth.identities (id, user_id, provider_id, provider, identity_data, last_sign_in_at, created_at, updated_at)
  VALUES (
    uuid_generate_v4(), hod_uid, hod_uid::text, 'email', 
    jsonb_build_object('sub', hod_uid, 'email', 'hod_demo@hkbk.edu'), 
    now(), now(), now()
  );

  -- ==========================================
  -- 3. CREATE R&D COORDINATOR USER
  -- Email: rd_demo@hkbk.edu
  -- ==========================================
  INSERT INTO auth.users (
    id, instance_id, aud, role, email, encrypted_password, email_confirmed_at, 
    raw_app_meta_data, raw_user_meta_data, created_at, updated_at
  ) VALUES (
    rd_uid, '00000000-0000-0000-0000-000000000000', 'authenticated', 'authenticated', 
    'rd_demo@hkbk.edu', crypt('password123', gen_salt('bf')), now(), 
    '{"provider":"email","providers":["email"]}', 
    '{"full_name": "Dr. RD Demo", "department": "Computer Science and Engineering", "role": "rd_coordinator"}', 
    now(), now()
  );

  INSERT INTO auth.identities (id, user_id, provider_id, provider, identity_data, last_sign_in_at, created_at, updated_at)
  VALUES (
    uuid_generate_v4(), rd_uid, rd_uid::text, 'email', 
    jsonb_build_object('sub', rd_uid, 'email', 'rd_demo@hkbk.edu'), 
    now(), now(), now()
  );

  -- NOTE: The public.profiles are automatically created via the `trg_on_auth_user_created` trigger.

  -- ==========================================
  -- 4. INSERT DUMMY RESEARCH ENTRIES
  -- ==========================================
  INSERT INTO public.research_entries (
    faculty_id, title, research_type, status, year, month, academic_year, department, is_nba_relevant, indexing, impact_factor
  ) VALUES 
    (faculty_uid, 'AI in Healthcare', 'Publication', 'Published', 2024, 5, '2023-24', 'Computer Science and Engineering', true, 'Scopus', 2.5),
    (faculty_uid, 'IoT Smart City Framework', 'Research Proposal', 'Funded', 2024, 1, '2023-24', 'Computer Science and Engineering', true, NULL, NULL),
    (hod_uid, 'Machine Learning Patent Method', 'Patent', 'Granted', 2023, 8, '2023-24', 'Computer Science and Engineering', true, NULL, NULL),
    (rd_uid, 'Cloud Computing Optimization', 'Publication', 'Published', 2022, 11, '2022-23', 'Computer Science and Engineering', false, 'SCI', 4.1);

END $$;
