-- Run this in Supabase SQL Editor to add new columns to existing research_entries table
-- These are safe ALTER TABLE ADD COLUMN IF NOT EXISTS statements (won't break existing data)

ALTER TABLE public.research_entries
  ADD COLUMN IF NOT EXISTS filing_date       DATE,
  ADD COLUMN IF NOT EXISTS publication_date  DATE,
  ADD COLUMN IF NOT EXISTS grant_date        DATE,
  ADD COLUMN IF NOT EXISTS assignee          TEXT,
  ADD COLUMN IF NOT EXISTS inventors         TEXT,
  ADD COLUMN IF NOT EXISTS client_name       TEXT,
  ADD COLUMN IF NOT EXISTS project_duration  TEXT,
  ADD COLUMN IF NOT EXISTS document_url      TEXT,
  ADD COLUMN IF NOT EXISTS extracted_metadata JSONB,
  ADD COLUMN IF NOT EXISTS extraction_confidence JSONB,
  ADD COLUMN IF NOT EXISTS ai_processed      BOOLEAN DEFAULT FALSE;

-- Update the research_type check constraint to allow new types
ALTER TABLE public.research_entries
  DROP CONSTRAINT IF EXISTS research_entries_research_type_check;

ALTER TABLE public.research_entries
  ADD CONSTRAINT research_entries_research_type_check
  CHECK (research_type IN ('Publication','Patent','Research Proposal','FDP','Consultancy','Project'));
