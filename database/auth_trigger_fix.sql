-- ============================================================
-- FIX: Supabase Auth Trigger and RLS Insert Policies
-- Run this in the Supabase SQL Editor to resolve the missing profiles issue.
-- ============================================================

-- 1. Ensure the trigger function uses SECURITY DEFINER
-- This allows the function to bypass RLS when inserting into public.profiles
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

-- 2. Drop the existing trigger if it exists and recreate it
DROP TRIGGER IF EXISTS trg_on_auth_user_created ON auth.users;

CREATE TRIGGER trg_on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- 3. Add an RLS policy to allow new authenticated users to insert their OWN profile
-- This serves as an extra layer of protection in case the trigger fails and the 
-- fallback logic in the Python app attempts to insert it via service role / authenticated session.
DROP POLICY IF EXISTS "profiles_insert_own" ON public.profiles;

CREATE POLICY "profiles_insert_own"
    ON public.profiles FOR INSERT
    WITH CHECK (auth.uid() = id);

-- 4. Verify existing admin insert policies
-- (Service role implicitly bypasses RLS, but it's good practice to allow admin explicitly)
DROP POLICY IF EXISTS "profiles_admin_insert" ON public.profiles;

CREATE POLICY "profiles_admin_insert"
    ON public.profiles FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.profiles p
            WHERE p.id = auth.uid() AND p.role = 'admin'
        )
    );
