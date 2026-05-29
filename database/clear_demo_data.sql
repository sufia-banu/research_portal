-- ============================================================
-- PRODUCTION DEPLOYMENT: CLEAN DEMO DATA
-- Run this script to permanently delete all demo seed data 
-- before launching the portal to real users.
-- ============================================================

-- 1. Clear all research entries (this drops publications, patents, and proposals)
DELETE FROM public.research_entries;

-- 2. Clear all reminders
DELETE FROM public.reminders;

-- 3. Clear all user profiles (this drops the faculty, hod, rd metadata)
DELETE FROM public.profiles;

-- 4. Delete all demo users from Supabase Auth
-- This ensures they cannot log in again. 
-- IMPORTANT: If you want to keep the "System Admin" (admin@hkbk.edu), change the WHERE clause.
DELETE FROM auth.users 
WHERE email LIKE '%@hkbk.edu';

-- 5. Force Schema Cache Reload (Crucial for GoTrue authentication safety)
NOTIFY pgrst, 'reload schema';

-- Done! Your database is now completely clean and ready for real users.
