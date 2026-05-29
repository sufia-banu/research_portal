-- ============================================================
-- RLS FIX: Eliminate infinite recursion on "profiles" table
-- Run this ENTIRE script in Supabase SQL Editor → New Query
-- ============================================================

-- ── STEP 1: Drop ALL old policies (clean slate) ───────────

DO $$ DECLARE r RECORD;
BEGIN
  FOR r IN SELECT policyname, tablename FROM pg_policies
           WHERE schemaname = 'public'
             AND tablename IN ('profiles','research_entries','departments','reminders')
  LOOP
    EXECUTE format('DROP POLICY IF EXISTS %I ON public.%I', r.policyname, r.tablename);
  END LOOP;
END $$;

-- ── STEP 2: SECURITY DEFINER helpers (bypass RLS safely) ─

-- Returns the role of the currently authenticated user
-- SECURITY DEFINER = runs as the function owner, bypasses RLS
-- This breaks the recursion cycle on the profiles table
CREATE OR REPLACE FUNCTION public.get_my_role()
RETURNS TEXT
LANGUAGE SQL
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
  SELECT role FROM public.profiles WHERE id = auth.uid();
$$;

-- Returns the department of the currently authenticated user
CREATE OR REPLACE FUNCTION public.get_my_department()
RETURNS TEXT
LANGUAGE SQL
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
  SELECT department FROM public.profiles WHERE id = auth.uid();
$$;

-- Grant execute to authenticated users
GRANT EXECUTE ON FUNCTION public.get_my_role()       TO authenticated;
GRANT EXECUTE ON FUNCTION public.get_my_department() TO authenticated;
-- Also grant to anon so registration page can call it (harmless — returns NULL for anon)
GRANT EXECUTE ON FUNCTION public.get_my_role()       TO anon;
GRANT EXECUTE ON FUNCTION public.get_my_department() TO anon;

-- ── STEP 3: PROFILES table policies (NO recursion) ────────

-- 3a. Own profile: pure auth.uid() = id comparison — zero recursion risk
CREATE POLICY "profiles_own_select"
  ON public.profiles FOR SELECT
  USING (auth.uid() = id);

-- 3b. Users update only their own profile
CREATE POLICY "profiles_own_update"
  ON public.profiles FOR UPDATE
  USING (auth.uid() = id)
  WITH CHECK (auth.uid() = id);

-- 3c. Self-insert on signup (trigger handles this, but policy needed)
CREATE POLICY "profiles_self_insert"
  ON public.profiles FOR INSERT
  WITH CHECK (auth.uid() = id);

-- ── STEP 4: DEPARTMENTS table policies ────────────────────

-- Departments are public info — readable by everyone including anon
-- (needed so the registration page can show departments without login)
CREATE POLICY "departments_public_read"
  ON public.departments FOR SELECT
  USING (true);

-- Only admin can modify departments
CREATE POLICY "departments_admin_write"
  ON public.departments FOR ALL
  USING (public.get_my_role() = 'admin')
  WITH CHECK (public.get_my_role() = 'admin');

-- ── STEP 5: RESEARCH_ENTRIES table policies ───────────────

-- 5a. Faculty sees only their own entries
CREATE POLICY "research_own_select"
  ON public.research_entries FOR SELECT
  USING (faculty_id = auth.uid());

-- 5b. HoD sees all entries in their department
CREATE POLICY "research_hod_select"
  ON public.research_entries FOR SELECT
  USING (
    public.get_my_role() = 'hod'
    AND department = public.get_my_department()
  );

-- 5c. R&D Coordinator and Admin see everything
CREATE POLICY "research_elevated_select"
  ON public.research_entries FOR SELECT
  USING (public.get_my_role() IN ('rd_coordinator', 'admin'));

-- 5d. Faculty inserts own entries
CREATE POLICY "research_faculty_insert"
  ON public.research_entries FOR INSERT
  WITH CHECK (faculty_id = auth.uid());

-- 5e. Faculty updates own entries
CREATE POLICY "research_faculty_update"
  ON public.research_entries FOR UPDATE
  USING (faculty_id = auth.uid())
  WITH CHECK (faculty_id = auth.uid());

-- 5f. Faculty deletes own entries
CREATE POLICY "research_faculty_delete"
  ON public.research_entries FOR DELETE
  USING (faculty_id = auth.uid());

-- 5g. Admin has full access to all entries
CREATE POLICY "research_admin_all"
  ON public.research_entries FOR ALL
  USING (public.get_my_role() = 'admin')
  WITH CHECK (public.get_my_role() = 'admin');

-- ── STEP 6: REMINDERS table policies ─────────────────────

-- Active reminders visible to their target role or 'all'
CREATE POLICY "reminders_target_select"
  ON public.reminders FOR SELECT
  USING (
    is_active = true
    AND (
      target_role = 'all'
      OR target_role = public.get_my_role()
    )
  );

-- Admin/R&D can see all reminders (for management)
CREATE POLICY "reminders_elevated_select"
  ON public.reminders FOR SELECT
  USING (public.get_my_role() IN ('admin', 'rd_coordinator'));

-- Admin/R&D can insert reminders
CREATE POLICY "reminders_admin_insert"
  ON public.reminders FOR INSERT
  WITH CHECK (public.get_my_role() IN ('admin', 'rd_coordinator'));

-- Admin full control
CREATE POLICY "reminders_admin_all"
  ON public.reminders FOR ALL
  USING (public.get_my_role() = 'admin');

-- ── STEP 7: Verify RLS is still enabled on all tables ─────
ALTER TABLE public.profiles         ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.research_entries ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.departments      ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.reminders        ENABLE ROW LEVEL SECURITY;

-- ── STEP 8: Grant table access to roles ───────────────────
GRANT SELECT ON public.departments TO anon, authenticated;
GRANT ALL    ON public.profiles         TO authenticated;
GRANT ALL    ON public.research_entries TO authenticated;
GRANT ALL    ON public.reminders        TO authenticated;

-- ── STEP 9: Quick sanity check ────────────────────────────
-- Run this after the script to verify policies exist:
-- SELECT tablename, policyname FROM pg_policies
-- WHERE schemaname = 'public' ORDER BY tablename, policyname;
