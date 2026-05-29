-- ============================================================
-- MIGRATION: Fix Infinite Recursion in Profiles RLS
-- ============================================================

-- 1. Create a SECURITY DEFINER function to fetch the current user's role safely.
-- SECURITY DEFINER bypasses RLS, so it will never trigger an infinite loop.
CREATE OR REPLACE FUNCTION public.get_auth_role()
RETURNS text
LANGUAGE sql
SECURITY DEFINER
SET search_path = public
AS $$
  SELECT role FROM public.profiles WHERE id = auth.uid();
$$;

-- 2. Drop the recursive policies on public.profiles
DROP POLICY IF EXISTS "profiles_select_hod" ON public.profiles;
DROP POLICY IF EXISTS "profiles_admin_all" ON public.profiles;

-- 3. Recreate them using the safe function
CREATE POLICY "profiles_select_hod"
    ON public.profiles FOR SELECT
    USING ( public.get_auth_role() IN ('hod','rd_coordinator','admin','iqac','principal') );

CREATE POLICY "profiles_admin_all"
    ON public.profiles FOR ALL
    USING ( public.get_auth_role() = 'admin' );

-- 4. Also fix other policies that might cause recursion if evaluated
-- (Optional but recommended for stability)
DROP POLICY IF EXISTS "research_select_hod" ON public.research_entries;
CREATE POLICY "research_select_hod"
    ON public.research_entries FOR SELECT
    USING (
        public.get_auth_role() = 'hod' 
        AND department = (SELECT department FROM public.profiles WHERE id = auth.uid())
    );

DROP POLICY IF EXISTS "research_select_rd_admin" ON public.research_entries;
CREATE POLICY "research_select_rd_admin"
    ON public.research_entries FOR SELECT
    USING ( public.get_auth_role() IN ('rd_coordinator','admin','iqac','principal') );

DROP POLICY IF EXISTS "research_admin_all" ON public.research_entries;
CREATE POLICY "research_admin_all"
    ON public.research_entries FOR ALL
    USING ( public.get_auth_role() = 'admin' );

DROP POLICY IF EXISTS "departments_admin_all" ON public.departments;
CREATE POLICY "departments_admin_all"
    ON public.departments FOR ALL
    USING ( public.get_auth_role() = 'admin' );

DROP POLICY IF EXISTS "reminders_insert_admin" ON public.reminders;
CREATE POLICY "reminders_insert_admin"
    ON public.reminders FOR INSERT
    WITH CHECK ( public.get_auth_role() IN ('admin','rd_coordinator','iqac','principal') );

DROP POLICY IF EXISTS "reminders_admin_all" ON public.reminders;
CREATE POLICY "reminders_admin_all"
    ON public.reminders FOR ALL
    USING ( public.get_auth_role() = 'admin' );

SELECT 'Infinite recursion fixed successfully' as status;
