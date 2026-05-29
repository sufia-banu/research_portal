-- ====================================================================
-- SEED DUMMY USERS AND DATA FOR AIML AND ISE DEPARTMENTS
-- Run this in your Supabase SQL Editor.
-- Password for all accounts will be: password123
-- ====================================================================

CREATE EXTENSION IF NOT EXISTS pgcrypto;

DO $$
DECLARE
  aiml_uid UUID := uuid_generate_v4();
  ise_uid UUID := uuid_generate_v4();
BEGIN

  -- ==========================================
  -- 1. CREATE AIML FACULTY USER
  -- Email: aiml_demo@hkbk.edu
  -- ==========================================
  INSERT INTO auth.users (
    id, instance_id, aud, role, email, encrypted_password, email_confirmed_at, 
    raw_app_meta_data, raw_user_meta_data, created_at, updated_at
  ) VALUES (
    aiml_uid, '00000000-0000-0000-0000-000000000000', 'authenticated', 'authenticated', 
    'aiml_demo@hkbk.edu', crypt('password123', gen_salt('bf')), now(), 
    '{"provider":"email","providers":["email"]}', 
    '{"full_name": "Dr. AI Expert", "department": "Artificial Intelligence and Machine Learning", "role": "faculty"}', 
    now(), now()
  );

  INSERT INTO auth.identities (id, user_id, provider_id, provider, identity_data, last_sign_in_at, created_at, updated_at)
  VALUES (
    uuid_generate_v4(), aiml_uid, aiml_uid::text, 'email', 
    jsonb_build_object('sub', aiml_uid, 'email', 'aiml_demo@hkbk.edu'), 
    now(), now(), now()
  );

  -- ==========================================
  -- 2. CREATE ISE FACULTY USER
  -- Email: ise_demo@hkbk.edu
  -- ==========================================
  INSERT INTO auth.users (
    id, instance_id, aud, role, email, encrypted_password, email_confirmed_at, 
    raw_app_meta_data, raw_user_meta_data, created_at, updated_at
  ) VALUES (
    ise_uid, '00000000-0000-0000-0000-000000000000', 'authenticated', 'authenticated', 
    'ise_demo@hkbk.edu', crypt('password123', gen_salt('bf')), now(), 
    '{"provider":"email","providers":["email"]}', 
    '{"full_name": "Dr. ISE Scholar", "department": "Information Science and Engineering", "role": "faculty"}', 
    now(), now()
  );

  INSERT INTO auth.identities (id, user_id, provider_id, provider, identity_data, last_sign_in_at, created_at, updated_at)
  VALUES (
    uuid_generate_v4(), ise_uid, ise_uid::text, 'email', 
    jsonb_build_object('sub', ise_uid, 'email', 'ise_demo@hkbk.edu'), 
    now(), now(), now()
  );


  -- ==========================================
  -- 3. INSERT DUMMY RESEARCH ENTRIES (AIML)
  -- ==========================================
  INSERT INTO public.research_entries (
    faculty_id, title, research_type, status, year, month, academic_year, department, is_nba_relevant, indexing, impact_factor
  ) VALUES 
    (aiml_uid, 'Deep Learning for Medical Image Classification', 'Publication', 'Published', 2024, 2, '2023-24', 'Artificial Intelligence and Machine Learning', true, 'Scopus', 3.8),
    (aiml_uid, 'Transformers in Natural Language Processing', 'Publication', 'Presented', 2023, 11, '2023-24', 'Artificial Intelligence and Machine Learning', true, 'IEEE', NULL),
    (aiml_uid, 'Automated System for Crop Disease Detection using CNN', 'Patent', 'Granted', 2023, 6, '2022-23', 'Artificial Intelligence and Machine Learning', true, NULL, NULL),
    (aiml_uid, 'Generative AI Applications in Education', 'Research Proposal', 'Funded', 2024, 1, '2023-24', 'Artificial Intelligence and Machine Learning', false, NULL, NULL);

  -- ==========================================
  -- 4. INSERT DUMMY RESEARCH ENTRIES (ISE)
  -- ==========================================
  INSERT INTO public.research_entries (
    faculty_id, title, research_type, status, year, month, academic_year, department, is_nba_relevant, indexing, impact_factor
  ) VALUES 
    (ise_uid, 'Blockchain for Secure Supply Chain Management', 'Publication', 'Published', 2023, 9, '2023-24', 'Information Science and Engineering', true, 'Web of Science', 4.2),
    (ise_uid, 'Cloud Computing Resource Allocation Algorithms', 'Publication', 'Presented', 2022, 5, '2021-22', 'Information Science and Engineering', false, 'Springer', NULL),
    (ise_uid, 'Method for Secure Data Transmission in IoT', 'Patent', 'Filed', 2024, 4, '2023-24', 'Information Science and Engineering', true, NULL, NULL),
    (ise_uid, 'Advanced Database Sharding Techniques', 'Publication', 'Published', 2021, 12, '2021-22', 'Information Science and Engineering', true, 'Scopus', 2.1);

END $$;
