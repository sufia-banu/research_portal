-- ============================================================
-- FULL FIX FOR "Database error querying schema"
-- ============================================================

-- 1. Reload the schema cache to ensure PostgREST and Gotrue see the latest schema
NOTIFY pgrst, 'reload schema';

-- 2. Drop all conflicting policies on profiles
DROP POLICY IF EXISTS "profiles_elevated_select" ON public.profiles;
DROP POLICY IF EXISTS "profiles_admin_delete" ON public.profiles;
DROP POLICY IF EXISTS "profiles_admin_update" ON public.profiles;
DROP POLICY IF EXISTS "Users can view own profile" ON public.profiles;

-- 3. Ensure profiles allows basic SELECT for the owner
CREATE POLICY "Users can view own profile"
  ON public.profiles FOR SELECT
  USING (auth.uid() = id);

-- 4. Check the handle_new_user trigger
-- We ensure search_path includes both public and auth, just in case.
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, auth AS $$
BEGIN
    INSERT INTO public.profiles (
        id, 
        full_name, 
        email, 
        department, 
        role
    )
    VALUES (
        NEW.id,
        COALESCE(NEW.raw_user_meta_data->>'full_name', 'New User'),
        NEW.email,
        NULLIF(NEW.raw_user_meta_data->>'department', ''),
        COALESCE(NEW.raw_user_meta_data->>'role', 'faculty')
    )
    ON CONFLICT (id) DO UPDATE SET
        full_name = EXCLUDED.full_name,
        email = EXCLUDED.email;
    RETURN NEW;
END;
$$;

-- 5. Force schema reload again just to be safe
NOTIFY pgrst, 'reload schema';
