-- ====================================================================
-- FULL SCHEMA SETUP — Research Information Collection Portal
-- HKBK College of Engineering
-- ====================================================================
-- HOW TO USE:
--   1. Create a new Supabase project at https://supabase.com
--   2. Go to SQL Editor → New Query
--   3. Paste this ENTIRE file and click RUN
--   4. Update your .env file with the new project URL and keys
-- ====================================================================


-- ====================================================================
-- SECTION 1: EXTENSIONS
-- ====================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";


-- ====================================================================
-- SECTION 2: TABLES
-- ====================================================================

-- --------------------------------------------------------------------
-- TABLE: departments
-- --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.departments (
    id              UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    department_name TEXT        NOT NULL UNIQUE,
    code            TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- --------------------------------------------------------------------
-- TABLE: profiles  (extends Supabase auth.users)
-- --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.profiles (
    id          UUID        PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    full_name   TEXT        NOT NULL,
    email       TEXT        NOT NULL UNIQUE,
    department  TEXT        REFERENCES public.departments(department_name) ON DELETE SET NULL,
    role        TEXT        NOT NULL DEFAULT 'faculty'
                            CHECK (role IN ('faculty','hod','rd_coordinator','admin')),
    is_active   BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- --------------------------------------------------------------------
-- TABLE: research_entries
-- --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.research_entries (
    id                      UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    faculty_id              UUID        NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,

    -- Core fields
    title                   TEXT        NOT NULL,
    research_type           TEXT        NOT NULL
                            CHECK (research_type IN (
                                'Publication','Patent','Research Proposal',
                                'FDP','Consultancy','Project'
                            )),
    journal_or_patent_office TEXT,
    conference_name         TEXT,
    indexing                TEXT,
    impact_factor           NUMERIC(6,3),
    authors                 TEXT,
    doi                     TEXT,
    status                  TEXT        NOT NULL DEFAULT 'Submitted',
    submission_date         DATE,
    month                   INTEGER     CHECK (month BETWEEN 1 AND 12),
    year                    INTEGER     CHECK (year >= 2000),
    department              TEXT,
    academic_year           TEXT,
    notes                   TEXT,
    is_nba_relevant         BOOLEAN     NOT NULL DEFAULT TRUE,

    -- Patent-specific fields
    filing_date             DATE,
    publication_date        DATE,
    grant_date              DATE,
    assignee                TEXT,
    patent_number           TEXT,
    inventors               TEXT,

    -- Proposal / Consultancy / Project fields
    funding_agency          TEXT,
    funding_amount          NUMERIC(14,2),
    client_name             TEXT,
    project_duration        TEXT,

    -- AI document intelligence fields
    document_url            TEXT,
    extracted_metadata      JSONB,
    extraction_confidence   JSONB,
    ai_processed            BOOLEAN     DEFAULT FALSE,
    uploaded_at             TIMESTAMPTZ,

    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- --------------------------------------------------------------------
-- TABLE: reminders
-- --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.reminders (
    id          UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    message     TEXT        NOT NULL,
    target_role TEXT        NOT NULL
                            CHECK (target_role IN ('faculty','hod','rd_coordinator','admin','all')),
    target_dept TEXT,           -- NULL = all departments
    sent_by     UUID        REFERENCES public.profiles(id),
    is_active   BOOLEAN     NOT NULL DEFAULT TRUE,
    sent_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at  TIMESTAMPTZ
);


-- ====================================================================
-- SECTION 3: INDEXES
-- ====================================================================

CREATE INDEX IF NOT EXISTS idx_research_faculty  ON public.research_entries(faculty_id);
CREATE INDEX IF NOT EXISTS idx_research_dept     ON public.research_entries(department);
CREATE INDEX IF NOT EXISTS idx_research_type     ON public.research_entries(research_type);
CREATE INDEX IF NOT EXISTS idx_research_year     ON public.research_entries(year);
CREATE INDEX IF NOT EXISTS idx_research_month    ON public.research_entries(month);
CREATE INDEX IF NOT EXISTS idx_research_status   ON public.research_entries(status);
CREATE INDEX IF NOT EXISTS idx_profiles_dept     ON public.profiles(department);
CREATE INDEX IF NOT EXISTS idx_profiles_role     ON public.profiles(role);


-- ====================================================================
-- SECTION 4: FUNCTIONS & TRIGGERS
-- ====================================================================

-- --------------------------------------------------------------------
-- Trigger function: auto-update updated_at timestamp
-- --------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.handle_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_profiles_updated_at
    BEFORE UPDATE ON public.profiles
    FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();

CREATE TRIGGER trg_research_updated_at
    BEFORE UPDATE ON public.research_entries
    FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();

-- --------------------------------------------------------------------
-- Trigger function: auto-create profile row on Supabase Auth signup
-- SECURITY DEFINER allows bypass of RLS during signup
-- --------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, auth AS $$
BEGIN
    INSERT INTO public.profiles (id, full_name, email, department, role)
    VALUES (
        NEW.id,
        COALESCE(NEW.raw_user_meta_data->>'full_name', 'New User'),
        NEW.email,
        NULLIF(NEW.raw_user_meta_data->>'department', ''),
        COALESCE(NEW.raw_user_meta_data->>'role', 'faculty')
    )
    ON CONFLICT (id) DO UPDATE SET
        full_name  = EXCLUDED.full_name,
        email      = EXCLUDED.email;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_on_auth_user_created ON auth.users;
CREATE TRIGGER trg_on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- --------------------------------------------------------------------
-- SECURITY DEFINER helpers — breaks RLS recursion cycle safely
-- These allow RLS policies to check the current user's role/dept
-- WITHOUT causing infinite recursion on the profiles table.
-- --------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.get_my_role()
RETURNS TEXT
LANGUAGE SQL STABLE SECURITY DEFINER SET search_path = public AS $$
    SELECT role FROM public.profiles WHERE id = auth.uid();
$$;

CREATE OR REPLACE FUNCTION public.get_my_department()
RETURNS TEXT
LANGUAGE SQL STABLE SECURITY DEFINER SET search_path = public AS $$
    SELECT department FROM public.profiles WHERE id = auth.uid();
$$;

-- Grant execute rights
GRANT EXECUTE ON FUNCTION public.get_my_role()       TO authenticated, anon;
GRANT EXECUTE ON FUNCTION public.get_my_department() TO authenticated, anon;


-- ====================================================================
-- SECTION 5: ROW LEVEL SECURITY (RLS)
-- ====================================================================

-- Enable RLS on all tables
ALTER TABLE public.profiles         ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.research_entries ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.departments      ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.reminders        ENABLE ROW LEVEL SECURITY;

-- Drop all existing policies (clean slate — safe to re-run)
DO $$ DECLARE r RECORD;
BEGIN
  FOR r IN
    SELECT policyname, tablename FROM pg_policies
    WHERE schemaname = 'public'
      AND tablename IN ('profiles','research_entries','departments','reminders')
  LOOP
    EXECUTE format('DROP POLICY IF EXISTS %I ON public.%I', r.policyname, r.tablename);
  END LOOP;
END $$;

-- --------------------------------------------------------------------
-- PROFILES policies
-- --------------------------------------------------------------------

-- Each user can see and update their own profile
CREATE POLICY "profiles_own_select"
    ON public.profiles FOR SELECT
    USING (auth.uid() = id);

CREATE POLICY "profiles_own_update"
    ON public.profiles FOR UPDATE
    USING (auth.uid() = id)
    WITH CHECK (auth.uid() = id);

-- Self-insert on signup (trigger handles this — policy is a safety net)
CREATE POLICY "profiles_self_insert"
    ON public.profiles FOR INSERT
    WITH CHECK (auth.uid() = id);

-- HoD, R&D Coordinator, and Admin can view all profiles
CREATE POLICY "profiles_elevated_select"
    ON public.profiles FOR SELECT
    USING (public.get_my_role() IN ('hod', 'rd_coordinator', 'admin'));

-- --------------------------------------------------------------------
-- DEPARTMENTS policies
-- --------------------------------------------------------------------

-- Readable by everyone — registration page needs this without login
CREATE POLICY "departments_public_read"
    ON public.departments FOR SELECT
    USING (true);

-- Only admin can modify departments
CREATE POLICY "departments_admin_write"
    ON public.departments FOR ALL
    USING (public.get_my_role() = 'admin')
    WITH CHECK (public.get_my_role() = 'admin');

-- --------------------------------------------------------------------
-- RESEARCH_ENTRIES policies
-- --------------------------------------------------------------------

-- Faculty sees only their own entries
CREATE POLICY "research_own_select"
    ON public.research_entries FOR SELECT
    USING (faculty_id = auth.uid());

-- HoD sees all entries in their department
CREATE POLICY "research_hod_select"
    ON public.research_entries FOR SELECT
    USING (
        public.get_my_role() = 'hod'
        AND department = public.get_my_department()
    );

-- R&D Coordinator and Admin see everything
CREATE POLICY "research_elevated_select"
    ON public.research_entries FOR SELECT
    USING (public.get_my_role() IN ('rd_coordinator', 'admin'));

-- Faculty inserts their own entries
CREATE POLICY "research_faculty_insert"
    ON public.research_entries FOR INSERT
    WITH CHECK (faculty_id = auth.uid());

-- Faculty updates their own entries
CREATE POLICY "research_faculty_update"
    ON public.research_entries FOR UPDATE
    USING (faculty_id = auth.uid())
    WITH CHECK (faculty_id = auth.uid());

-- Faculty deletes their own entries
CREATE POLICY "research_faculty_delete"
    ON public.research_entries FOR DELETE
    USING (faculty_id = auth.uid());

-- Admin full access
CREATE POLICY "research_admin_all"
    ON public.research_entries FOR ALL
    USING (public.get_my_role() = 'admin')
    WITH CHECK (public.get_my_role() = 'admin');

-- --------------------------------------------------------------------
-- REMINDERS policies
-- --------------------------------------------------------------------

-- Visible to target audience (role match or 'all')
CREATE POLICY "reminders_target_select"
    ON public.reminders FOR SELECT
    USING (
        is_active = true
        AND (
            target_role = 'all'
            OR target_role = public.get_my_role()
        )
    );

-- Admin/R&D can view all reminders (for management)
CREATE POLICY "reminders_elevated_select"
    ON public.reminders FOR SELECT
    USING (public.get_my_role() IN ('admin', 'rd_coordinator'));

-- Admin/R&D can send reminders
CREATE POLICY "reminders_admin_insert"
    ON public.reminders FOR INSERT
    WITH CHECK (public.get_my_role() IN ('admin', 'rd_coordinator'));

-- Admin full control
CREATE POLICY "reminders_admin_all"
    ON public.reminders FOR ALL
    USING (public.get_my_role() = 'admin');


-- ====================================================================
-- SECTION 6: TABLE-LEVEL GRANTS
-- ====================================================================

GRANT SELECT              ON public.departments      TO anon, authenticated;
GRANT ALL                 ON public.profiles         TO authenticated;
GRANT ALL                 ON public.research_entries TO authenticated;
GRANT ALL                 ON public.reminders        TO authenticated;


-- ====================================================================
-- SECTION 7: STORAGE BUCKET (for AI document uploads)
-- ====================================================================

INSERT INTO storage.buckets (id, name, public)
VALUES ('research_documents', 'research_documents', false)
ON CONFLICT (id) DO NOTHING;

-- Allow authenticated users to upload documents
DROP POLICY IF EXISTS "storage_upload" ON storage.objects;
CREATE POLICY "storage_upload"
    ON storage.objects FOR INSERT TO authenticated
    WITH CHECK (bucket_id = 'research_documents');

-- Allow authenticated users to read documents
DROP POLICY IF EXISTS "storage_read" ON storage.objects;
CREATE POLICY "storage_read"
    ON storage.objects FOR SELECT TO authenticated
    USING (bucket_id = 'research_documents');

-- Allow users to update/delete their own documents
DROP POLICY IF EXISTS "storage_update_own" ON storage.objects;
CREATE POLICY "storage_update_own"
    ON storage.objects FOR UPDATE TO authenticated
    USING (bucket_id = 'research_documents' AND owner = auth.uid());

DROP POLICY IF EXISTS "storage_delete_own" ON storage.objects;
CREATE POLICY "storage_delete_own"
    ON storage.objects FOR DELETE TO authenticated
    USING (bucket_id = 'research_documents' AND owner = auth.uid());


-- ====================================================================
-- SECTION 8: SEED DATA — Departments (HKBK College of Engineering)
-- ====================================================================

INSERT INTO public.departments (department_name, code) VALUES
    ('Computer Science and Engineering',             'CSE'),
    ('Information Science and Engineering',          'ISE'),
    ('Artificial Intelligence and Machine Learning', 'AIML'),
    ('Electronics and Communication Engineering',    'ECE'),
    ('Mechanical Engineering',                       'ME'),
    ('Civil Engineering',                            'CE'),
    ('Humanities',                                   'HUM'),
    ('Basic Science',                                'BS')
ON CONFLICT (department_name) DO UPDATE
    SET code = EXCLUDED.code;


-- ====================================================================
-- SECTION 9: VERIFICATION QUERIES
-- Run these after setup to confirm everything is correct
-- ====================================================================

-- Check tables exist
-- SELECT table_name FROM information_schema.tables
-- WHERE table_schema = 'public' ORDER BY table_name;

-- Check policies exist
-- SELECT tablename, policyname, cmd FROM pg_policies
-- WHERE schemaname = 'public' ORDER BY tablename, policyname;

-- Check departments seeded
-- SELECT code, department_name FROM public.departments ORDER BY code;

-- Check triggers exist
-- SELECT trigger_name, event_object_table FROM information_schema.triggers
-- WHERE trigger_schema = 'public';

-- ====================================================================
-- SETUP COMPLETE ✓
-- Next steps:
--   1. Copy new Supabase URL and keys into your .env file
--   2. Run: venv\Scripts\streamlit run app.py
--   3. Register → go to Table Editor → profiles → set role = 'admin'
--      OR run: UPDATE public.profiles SET role='admin' WHERE email='your@email.com';
-- ====================================================================
