-- =================================================================================
-- database/update_admin_email.sql
-- Run this in your Supabase SQL Editor to update the existing admin email
-- =================================================================================

-- 1. Update the auth.users table (this is the actual login email)
UPDATE auth.users 
SET email = 'iqac@hkbk.edu' 
WHERE email = 'admin@hkbk.edu';

-- 2. Update the profiles table (this is the display email)
UPDATE public.profiles 
SET email = 'iqac@hkbk.edu' 
WHERE email = 'admin@hkbk.edu';
