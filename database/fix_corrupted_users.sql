-- ============================================================
-- FIX CORRUPTED AUTH USERS
-- Run this in the Supabase SQL Editor
-- ============================================================
-- The original demo_seed.sql manually inserted rows into auth.users.
-- Manual inserts break Supabase GoTrue because they are missing internal encrypted fields, 
-- causing the "Database error querying schema" on login.
-- This script safely deletes the corrupted manually-inserted users.
-- We will recreate them using the proper Supabase Admin API afterward.

-- 1. Delete all profiles (to avoid foreign key constraint issues during deletion)
DELETE FROM public.profiles;

-- 2. Delete ALL manually inserted/corrupted users from auth.users
-- We will wipe all @hkbk.edu accounts so generate_seed.py can cleanly rebuild them all.
DELETE FROM auth.users 
WHERE email LIKE '%@hkbk.edu';

-- 3. Reload schema cache for safety
NOTIFY pgrst, 'reload schema';
