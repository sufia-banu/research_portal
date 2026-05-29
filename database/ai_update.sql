-- ============================================================
-- SQL Update: AI Document Intelligence System
-- Run this in Supabase SQL Editor
-- ============================================================

-- 1. Add new columns to research_entries for AI metadata and storage
ALTER TABLE public.research_entries
ADD COLUMN IF NOT EXISTS document_url TEXT,
ADD COLUMN IF NOT EXISTS extracted_metadata JSONB,
ADD COLUMN IF NOT EXISTS extraction_confidence JSONB,
ADD COLUMN IF NOT EXISTS ai_processed BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS uploaded_at TIMESTAMPTZ;

-- 2. Create the Storage Bucket for research documents
INSERT INTO storage.buckets (id, name, public) 
VALUES ('research_documents', 'research_documents', false)
ON CONFLICT (id) DO NOTHING;

-- 3. Storage RLS Policies
-- Allow authenticated users to upload their own documents
DROP POLICY IF EXISTS "Allow authenticated users to upload documents" ON storage.objects;
CREATE POLICY "Allow authenticated users to upload documents"
ON storage.objects FOR INSERT TO authenticated WITH CHECK (
  bucket_id = 'research_documents' 
);

-- Allow authenticated users to read their own documents (or R&D/Admin to read all)
DROP POLICY IF EXISTS "Allow users to read documents" ON storage.objects;
CREATE POLICY "Allow users to read documents"
ON storage.objects FOR SELECT TO authenticated USING (
  bucket_id = 'research_documents'
);

-- Allow faculty to update/delete their own documents
DROP POLICY IF EXISTS "Allow users to update own documents" ON storage.objects;
CREATE POLICY "Allow users to update own documents"
ON storage.objects FOR UPDATE TO authenticated USING (
  bucket_id = 'research_documents' AND owner = auth.uid()
);

DROP POLICY IF EXISTS "Allow users to delete own documents" ON storage.objects;
CREATE POLICY "Allow users to delete own documents"
ON storage.objects FOR DELETE TO authenticated USING (
  bucket_id = 'research_documents' AND owner = auth.uid()
);
