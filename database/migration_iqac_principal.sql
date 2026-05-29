-- ============================================================
-- MIGRATION: Add 'iqac' and 'principal' roles to the system
-- Run this in the Supabase SQL Edito
-- ============================================================

-- 1. Update the CHECK constraint on public.profiles.role
-- We must drop the existing constraint and add the new one.
ALTER TABLE public.profiles DROP CONSTRAINT IF EXISTS profiles_role_check;
ALTER TABLE public.profiles ADD CONSTRAINT profiles_role_check 
    CHECK (role IN ('faculty', 'hod', 'rd_coordinator', 'admin', 'iqac', 'principal'));

-- 2. Update the check constraint on public.reminders.target_role
ALTER TABLE public.reminders DROP CONSTRAINT IF EXISTS reminders_target_role_check;
ALTER TABLE public.reminders ADD CONSTRAINT reminders_target_role_check 
    CHECK (target_role IN ('faculty', 'hod', 'rd_coordinator', 'admin', 'iqac', 'principal', 'all'));

-- 3. Recreate the RLS policy for viewing profiles
DROP POLICY IF EXISTS "profiles_select_hod" ON public.profiles;
CREATE POLICY "profiles_select_hod"
    ON public.profiles FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.profiles p
            WHERE p.id = auth.uid()
              AND p.role IN ('hod','rd_coordinator','admin','iqac','principal')
        )
    );

-- 4. Recreate the RLS policy for viewing research entries (admin/rd/iqac/principal)
DROP POLICY IF EXISTS "research_select_rd_admin" ON public.research_entries;
CREATE POLICY "research_select_rd_admin"
    ON public.research_entries FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.profiles p
            WHERE p.id = auth.uid()
              AND p.role IN ('rd_coordinator','admin','iqac','principal')
        )
    );

-- 5. Recreate the RLS policy for inserting reminders
DROP POLICY IF EXISTS "reminders_insert_admin" ON public.reminders;
CREATE POLICY "reminders_insert_admin"
    ON public.reminders FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.profiles p
            WHERE p.id = auth.uid() AND p.role IN ('admin','rd_coordinator','iqac','principal')
        )
    );

SELECT 'Migration completed successfully. IQAC and Principal roles added.' as status;
