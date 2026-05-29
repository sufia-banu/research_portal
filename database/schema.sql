"""
database/schema.sql  — Complete PostgreSQL schema for Supabase
Run this in the Supabase SQL Editor (Project → SQL Editor → New Query)
"""

-- ============================================================
-- ENABLE UUID EXTENSION
-- ============================================================
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================
-- TABLE: departments
-- ============================================================
CREATE TABLE IF NOT EXISTS public.departments (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    department_name TEXT NOT NULL UNIQUE,
    code        TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- TABLE: profiles  (extends Supabase auth.users)
-- ============================================================
CREATE TABLE IF NOT EXISTS public.profiles (
    id          UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    full_name   TEXT NOT NULL,
    email       TEXT NOT NULL UNIQUE,
    department  TEXT REFERENCES public.departments(department_name) ON DELETE SET NULL,
    role        TEXT NOT NULL DEFAULT 'faculty'
                CHECK (role IN ('faculty','hod','rd_coordinator','admin','iqac','principal')),
    is_active   BOOLEAN NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- TABLE: research_entries
-- ============================================================
CREATE TABLE IF NOT EXISTS public.research_entries (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    faculty_id              UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    title                   TEXT NOT NULL,
    research_type           TEXT NOT NULL
                            CHECK (research_type IN ('Publication','Patent','Research Proposal','FDP','Consultancy','Project')),
    journal_or_patent_office TEXT,
    conference_name         TEXT,
    indexing                TEXT,
    impact_factor           NUMERIC(6,3),
    authors                 TEXT,
    doi                     TEXT,
    status                  TEXT NOT NULL DEFAULT 'Submitted',
    submission_date         DATE,
    filing_date             DATE,          -- Patent specific
    publication_date        DATE,          -- Patent specific
    grant_date              DATE,          -- Patent specific
    assignee                TEXT,          -- Patent specific (institution/company)
    patent_number           TEXT,          -- Patent specific
    inventors               TEXT,          -- Patent specific
    month                   INTEGER CHECK (month BETWEEN 1 AND 12),
    year                    INTEGER CHECK (year >= 2000),
    department              TEXT,
    academic_year           TEXT,
    funding_agency          TEXT,
    funding_amount          NUMERIC(14,2),
    client_name             TEXT,          -- Consultancy specific
    project_duration        TEXT,          -- Project/Consultancy duration
    notes                   TEXT,
    is_nba_relevant         BOOLEAN NOT NULL DEFAULT TRUE,
    document_url            TEXT,
    extracted_metadata      JSONB,
    extraction_confidence   JSONB,
    ai_processed            BOOLEAN DEFAULT FALSE,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- TABLE: reminders
-- ============================================================
CREATE TABLE IF NOT EXISTS public.reminders (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    message     TEXT NOT NULL,
    target_role TEXT NOT NULL
                CHECK (target_role IN ('faculty','hod','rd_coordinator','admin','all')),
    target_dept TEXT,   -- NULL means all departments
    sent_by     UUID REFERENCES public.profiles(id),
    is_active   BOOLEAN NOT NULL DEFAULT TRUE,
    sent_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at  TIMESTAMPTZ
);

-- ============================================================
-- INDEXES
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_research_faculty    ON public.research_entries(faculty_id);
CREATE INDEX IF NOT EXISTS idx_research_dept       ON public.research_entries(department);
CREATE INDEX IF NOT EXISTS idx_research_type       ON public.research_entries(research_type);
CREATE INDEX IF NOT EXISTS idx_research_year       ON public.research_entries(year);
CREATE INDEX IF NOT EXISTS idx_research_month      ON public.research_entries(month);
CREATE INDEX IF NOT EXISTS idx_research_status     ON public.research_entries(status);
CREATE INDEX IF NOT EXISTS idx_profiles_dept       ON public.profiles(department);
CREATE INDEX IF NOT EXISTS idx_profiles_role       ON public.profiles(role);

-- ============================================================
-- TRIGGER: auto-update updated_at
-- ============================================================
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

-- ============================================================
-- TRIGGER: auto-create profile on auth signup
-- ============================================================
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER LANGUAGE plpgsql SECURITY DEFINER AS $$
BEGIN
    INSERT INTO public.profiles (id, full_name, email, department, role)
    VALUES (
        NEW.id,
        COALESCE(NEW.raw_user_meta_data->>'full_name', 'New User'),
        NEW.email,
        NEW.raw_user_meta_data->>'department',
        COALESCE(NEW.raw_user_meta_data->>'role', 'faculty')
    )
    ON CONFLICT (id) DO NOTHING;
    RETURN NEW;
END;
$$;

CREATE OR REPLACE TRIGGER trg_on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- ============================================================
-- ROW LEVEL SECURITY
-- ============================================================

ALTER TABLE public.profiles        ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.research_entries ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.departments     ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.reminders       ENABLE ROW LEVEL SECURITY;

-- ── profiles policies ─────────────────────────────────────

-- Anyone authenticated can view their OWN profile
CREATE POLICY "profiles_select_own"
    ON public.profiles FOR SELECT
    USING (auth.uid() = id);

-- HoD can view profiles in their department
CREATE POLICY "profiles_select_hod"
    ON public.profiles FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.profiles p
            WHERE p.id = auth.uid()
              AND p.role IN ('hod','rd_coordinator','admin','iqac','principal')
        )
    );

-- Only admin can insert/update/delete profiles
CREATE POLICY "profiles_admin_all"
    ON public.profiles FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM public.profiles p
            WHERE p.id = auth.uid() AND p.role = 'admin'
        )
    );

-- Users can update their own profile (limited fields)
CREATE POLICY "profiles_update_own"
    ON public.profiles FOR UPDATE
    USING (auth.uid() = id);

-- ── research_entries policies ─────────────────────────────

-- Faculty sees only own entries
CREATE POLICY "research_select_faculty_own"
    ON public.research_entries FOR SELECT
    USING (faculty_id = auth.uid());

-- HoD sees department entries
CREATE POLICY "research_select_hod"
    ON public.research_entries FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.profiles p
            WHERE p.id = auth.uid()
              AND p.role = 'hod'
              AND p.department = research_entries.department
        )
    );

-- R&D Coordinator and Admin see all
CREATE POLICY "research_select_rd_admin"
    ON public.research_entries FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.profiles p
            WHERE p.id = auth.uid()
              AND p.role IN ('rd_coordinator','admin','iqac','principal')
        )
    );

-- Faculty can insert own entries
CREATE POLICY "research_insert_faculty"
    ON public.research_entries FOR INSERT
    WITH CHECK (faculty_id = auth.uid());

-- Faculty can update own entries
CREATE POLICY "research_update_faculty"
    ON public.research_entries FOR UPDATE
    USING (faculty_id = auth.uid());

-- Faculty can delete own entries
CREATE POLICY "research_delete_faculty"
    ON public.research_entries FOR DELETE
    USING (faculty_id = auth.uid());

-- Admin can do everything
CREATE POLICY "research_admin_all"
    ON public.research_entries FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM public.profiles p
            WHERE p.id = auth.uid() AND p.role = 'admin'
        )
    );

-- ── departments policies ──────────────────────────────────

-- Everyone can read departments
CREATE POLICY "departments_select_all"
    ON public.departments FOR SELECT
    USING (auth.role() = 'authenticated');

-- Only admin can modify
CREATE POLICY "departments_admin_all"
    ON public.departments FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM public.profiles p
            WHERE p.id = auth.uid() AND p.role = 'admin'
        )
    );

-- ── reminders policies ────────────────────────────────────

-- All authenticated see reminders targeted to them
CREATE POLICY "reminders_select_targeted"
    ON public.reminders FOR SELECT
    USING (
        auth.role() = 'authenticated'
        AND is_active = TRUE
        AND (
            target_role = 'all'
            OR target_role = (SELECT role FROM public.profiles WHERE id = auth.uid())
        )
    );

-- Only admin/rd can insert reminders
CREATE POLICY "reminders_insert_admin"
    ON public.reminders FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.profiles p
            WHERE p.id = auth.uid() AND p.role IN ('admin','rd_coordinator','iqac','principal')
        )
    );

CREATE POLICY "reminders_admin_all"
    ON public.reminders FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM public.profiles p
            WHERE p.id = auth.uid() AND p.role = 'admin'
        )
    );

-- ============================================================
-- SAMPLE DATA — Departments
-- ============================================================
INSERT INTO public.departments (department_name, code) VALUES
    ('Computer Science and Engineering', 'CSE'),
    ('Electronics and Communication Engineering', 'ECE'),
    ('Mechanical Engineering', 'ME'),
    ('Civil Engineering', 'CE'),
    ('Electrical and Electronics Engineering', 'EEE'),
    ('Information Science and Engineering', 'ISE'),
    ('Artificial Intelligence and Machine Learning', 'AIML'),
    ('Biotechnology', 'BT'),
    ('Mathematics', 'MATH'),
    ('Physics', 'PHY'),
    ('Chemistry', 'CHEM'),
    ('Management Studies', 'MBA')
ON CONFLICT (department_name) DO NOTHING;
