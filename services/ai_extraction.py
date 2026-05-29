"""
services/ai_extraction.py - AI Document Intelligence System
Extracts metadata from research papers (PDF, DOCX, TXT)
"""
import re
import io
import fitz  # PyMuPDF fallback
import pdfplumber
from docx import Document
from datetime import datetime

# Common regex patterns for metadata extraction
DOI_REGEX = r'(10\.\d{4,9}/[-._;()/:A-Z0-9]+)'
EMAIL_REGEX = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
YEAR_REGEX = r'\b(19|20)\d{2}\b'

def normalize_key(k: str) -> str:
    if not isinstance(k, str):
        return ""
    return re.sub(r'[^a-z0-9]', '', k.lower())

def extract_tables_from_pdf(file_bytes: bytes) -> dict:
    """Extract key-value pairs from tables in a PDF using pdfplumber."""
    extracted_data = {}
    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages[:3]: # Limit to first 3 pages
                tables = page.extract_tables()
                for table in tables:
                    for row in table:
                        # Only consider rows with at least 2 non-empty cells
                        row_clean = [str(cell).strip() if cell else "" for cell in row]
                        if len(row_clean) >= 2 and row_clean[0]:
                            key = normalize_key(row_clean[0])
                            val = " ".join(row_clean[1:]).strip()
                            # Prevent overwriting with empty values
                            if key and val:
                                extracted_data[key] = val
    except Exception as e:
        print(f"Table extraction error: {e}")
    return extracted_data

def extract_text_from_bytes(file_bytes: bytes, file_name: str) -> str:
    """Extract raw text from PDF, DOCX, or TXT — reads ALL pages."""
    text = ""
    ext = file_name.lower().split('.')[-1]
    try:
        if ext == 'pdf':
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            for page in doc:
                text += page.get_text("text") + "\n"
        elif ext == 'docx':
            doc = Document(io.BytesIO(file_bytes))
            for para in doc.paragraphs:
                text += para.text + "\n"
        elif ext == 'txt':
            text = file_bytes.decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"Text extraction error: {e}")
    return text


def _extract_clean_text_pdfplumber(file_bytes: bytes) -> str:
    """Use pdfplumber to get cleaner text from complex PDFs (strips most watermarks)."""
    lines = []
    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                # extract_text uses layout analysis which handles tables/columns better
                t = page.extract_text(x_tolerance=3, y_tolerance=3)
                if t:
                    lines.append(t)
    except Exception as e:
        print(f"pdfplumber clean extract error: {e}")
    return "\n".join(lines)


def _extract_italic_spans_fitz(file_bytes: bytes) -> list[str]:
    """
    Use PyMuPDF dict mode to find italic/bold-italic text spans.
    Indian patent certificates print the invention title in italics.
    Returns list of candidate italic phrases.
    """
    candidates = []
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        for page in doc:
            blocks = page.get_text("dict")["blocks"]
            for block in blocks:
                if block.get("type") != 0:   # text block only
                    continue
                for line in block.get("lines", []):
                    line_text = ""
                    is_italic = False
                    for span in line.get("spans", []):
                        flags = span.get("flags", 0)
                        # bit 1 = italic (fitz flags: 1=superscript,2=italic,4=serifed,8=mono,16=bold)
                        if flags & 2 or "Italic" in span.get("font", "") or "italic" in span.get("font", "").lower():
                            is_italic = True
                        line_text += span.get("text", "")
                    line_text = line_text.strip()
                    if is_italic and len(line_text) > 8:
                        candidates.append(line_text)
    except Exception as e:
        print(f"Italic span extraction error: {e}")
    return candidates


def extract_patent_fields_from_pdf(file_bytes: bytes) -> dict:
    """
    Dedicated extractor for Indian Patent Office / Design Registration Certificates.
    Uses three strategies:
      1. pdfplumber clean text  -> structured fields (Design No, Date, Date of Issue)
      2. PyMuPDF italic spans   -> title (invention name printed in italics)
      3. PyMuPDF raw text       -> fallback for any missed fields
    Returns a dict with patent-specific keys ready to merge into metadata result.
    """
    fields = {
        "patent_number": "",
        "filing_date": None,
        "publication_date": None,
        "title": "",
        "inventors": "",
        "assignee": "",
        "journal_or_patent_office": "",
        "confidence": {},
    }

    def _norm_date(raw: str):
        raw = raw.strip().rstrip("*:;, ")
        # DD/MM/YYYY (Indian standard)
        m = re.match(r'^(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})$', raw)
        if m:
            d, mo, y = m.groups()
            return f"{y}-{int(mo):02d}-{int(d):02d}"
        # YYYY-MM-DD already
        m = re.match(r'^(\d{4})[/\-](\d{1,2})[/\-](\d{1,2})$', raw)
        if m:
            y, mo, d = m.groups()
            return f"{y}-{int(mo):02d}-{int(d):02d}"
        return None

    DATE_PAT = r'(\d{1,2}[/\-]\d{2}[/\-]\d{4})'

    # ── Strategy 1: pdfplumber clean text ────────────────────────────────
    clean = _extract_clean_text_pdfplumber(file_bytes)
    clean_lower = clean.lower()

    # Patent / Design Number
    dn = re.search(
        r'(?:design\s*(?:no\.?|number|s\.?\s*no\.?)|डिज़ाइन\s*सं\.?)\s*[:/]?\s*([\d\-/]+)',
        clean, re.IGNORECASE
    )
    if dn:
        fields["patent_number"] = dn.group(1).strip()
        fields["confidence"]["patent_number"] = 0.98
    else:
        pn = re.search(
            r'(?:application|patent|pub)\.?\s*no\.?\s*[:/]?\s*'
            r'((?:IN|US|EP|WO|JP|CN|GB|DE|FR)[\s\-]?[\d/]{5,}[A-Z]?)',
            clean, re.IGNORECASE
        )
        if pn:
            fields["patent_number"] = pn.group(1).strip()
            fields["confidence"]["patent_number"] = 0.94

    # Filing Date — labelled "तारीख / Date" or "Date :" near the top
    fd = re.search(
        r'(?:त[ाा]र[ीि]ख\s*/\s*date|filing\s+date|date\s+of\s+filing|date\s*[:])\s*'
        + DATE_PAT,
        clean, re.IGNORECASE
    )
    if fd:
        normed = _norm_date(fd.group(1))
        if normed:
            fields["filing_date"] = normed
            fields["confidence"]["filing_date"] = 0.98

    # Fallback filing date: first date after Design No. line
    if not fields["filing_date"]:
        lines_c = clean.split('\n')
        found_dn = False
        for line in lines_c:
            if re.search(r'design\s*(no|sn)', line, re.IGNORECASE) or re.search(r'डिज़ाइन', line):
                found_dn = True
                continue
            if found_dn:
                dm = re.search(DATE_PAT, line)
                if dm:
                    normed = _norm_date(dm.group(1))
                    if normed:
                        fields["filing_date"] = normed
                        fields["confidence"]["filing_date"] = 0.85
                break

    # Publication Date (Date of Issue)
    # From debug: pdfplumber extracts "15/09/2025" as a STANDALONE LINE
    # immediately before/after the signature block (no label on same line)
    doi = re.search(
        r'(?:date\s+of\s+issue|\u091c\u093e\u0930\u0940\s+\u0915\u0930\u0928\u0947\s+\u0915\u0940\s+\u0924\u093f\u0925\u093f)'
        r'[\s\S]{0,60}?' + DATE_PAT,
        clean, re.IGNORECASE
    )
    if doi:
        normed = _norm_date(doi.group(1))
        if normed:
            fields["publication_date"] = normed
            fields["confidence"]["publication_date"] = 0.99

    # Fallback: search raw fitz text for Date of Issue (handles different layouts)
    if not fields["publication_date"]:
        raw_text = extract_text_from_bytes(file_bytes, "_.pdf")
        doi2 = re.search(
            r'(?:date\s+of\s+issue|\u091c\u093e\u0930\u0940\s+\u0915\u0930\u0928\u0947\s+\u0915\u0940\s+\u0924\u093f\u0925\u093f)'
            r'[\s\S]{0,60}?' + DATE_PAT,
            raw_text, re.IGNORECASE
        )
        if doi2:
            normed = _norm_date(doi2.group(1))
            if normed:
                fields["publication_date"] = normed
                fields["confidence"]["publication_date"] = 0.93

    # Last resort: collect ALL dates; last unique date != filing_date is Publication Date
    # (In Indian certs the filing date comes first, Date of Issue is always the last/latest date)
    if not fields["publication_date"]:
        all_dates_clean = re.findall(DATE_PAT, clean)
        all_dates_raw   = re.findall(DATE_PAT, extract_text_from_bytes(file_bytes, "_.pdf"))
        all_dates = list(dict.fromkeys(all_dates_clean + all_dates_raw))  # unique, order-preserving
        normed_dates = [_norm_date(d) for d in all_dates if _norm_date(d)]
        filing = fields.get("filing_date")
        # Take the last date that is different from the filing date
        for nd in reversed(normed_dates):
            if nd != filing:
                fields["publication_date"] = nd
                fields["confidence"]["publication_date"] = 0.82
                break

    # Patent Office
    # Note: "The Patent Office, Government Of India" is in the watermark/background
    # layer and cannot be extracted by any text tool.
    # We detect it from certificate identity keywords and hardcode it.
    _raw_for_office = extract_text_from_bytes(file_bytes, "_.pdf")
    _office_search_text = clean + "\n" + _raw_for_office
    _office_lower = _office_search_text.lower()

    # Check for Indian Design Certificate identity markers in extractable text
    _is_indian_ipo = any(kw in _office_lower for kw in [
        "designs act", "designs rules", "design no", "certificate of registration",
        "registration of design", "intellectual property india",
        "patent office", "controller general"
    ])
    if _is_indian_ipo:
        # Try to get exact string from raw text first
        po = re.search(
            r'((?:The\s+)?Patent\s+Office[,\s]+Government\s+(?:of|Of)\s+India)',
            _office_search_text, re.IGNORECASE
        )
        fields["journal_or_patent_office"] = po.group(1).strip() if po else "Patent Office, Government of India"
        fields["confidence"]["journal_or_patent_office"] = 0.99
        fields["assignee"] = fields["journal_or_patent_office"]
        fields["confidence"]["assignee"] = 0.99

    # Inventors — numbered list after "in the name of"
    inv_block = re.search(
        r'(?:in\s+the\s+name\s+of|name\s+of\s+applicant)'
        r'[\s\S]{0,20}?((?:\d+\.?\s*(?:Dr\.|Prof\.|Mr\.|Mrs\.|Ms\.|Sh\.|Smt\.)?\s*[A-Z][A-Za-z\s\.]{2,40}){1,12})',
        clean, re.IGNORECASE | re.DOTALL
    )
    if inv_block:
        raw_inv = inv_block.group(1)
        names = re.findall(
            r'\d+\.?\s*((?:Dr\.|Prof\.|Mr\.|Mrs\.|Ms\.)?\s*[A-Z][A-Za-z\s\.]{2,35}?)(?=\s+\d+\.|$|\n)',
            raw_inv
        )
        if names:
            clean_names = [n.strip().rstrip('.') for n in names if len(n.strip()) > 3]
            fields["inventors"] = ", ".join(clean_names[:8])
            fields["confidence"]["inventors"] = 0.93

    # ── Strategy 2: italic spans for title ───────────────────────────────
    italic_spans = _extract_italic_spans_fitz(file_bytes)
    for span in italic_spans:
        span_clean = span.strip()
        if len(span_clean) < 10:
            continue
        ascii_ratio = sum(1 for c in span_clean if ord(c) < 128) / max(len(span_clean), 1)
        if ascii_ratio < 0.6:
            continue
        skip_words = ['reciprocity', 'date', 'country', 'class', 'certificate', 'government',
                      'patent office', 'india', 'designs act', 'designs rule', 'intellectual']
        if any(w in span_clean.lower() for w in skip_words):
            continue
        word_count = len(span_clean.split())
        if word_count >= 2:
            fields["title"] = span_clean.strip()
            fields["confidence"]["title"] = 0.96
            break

    # ── Strategy 3: regex on clean text for title ─────────────────────────
    if not fields["title"]:
        # From debug: title appears as "design to AUTOMATIC ROBOT FOR AGRICULTURE\nSECTOR"
        # Grab everything after "design to" until "in the name"
        t_m = re.search(
            r'design\s+to\s+([A-Z][A-Z\s]{5,120}?)\s+in\s+the\s+name',
            clean, re.DOTALL
        )
        if t_m:
            raw_title = re.sub(r'\s+', ' ', t_m.group(1)).strip()
            fields["title"] = raw_title.title()
            fields["confidence"]["title"] = 0.95

    if not fields["title"]:
        # Also try: "application of such design to CAPS_PHRASE in the name"
        t_m2 = re.search(
            r'application\s+of\s+such\s+design\s+to\s+([A-Z][A-Z\s]{5,120}?)\s+in\s+the\s+name',
            clean, re.DOTALL
        )
        if t_m2:
            raw_title = re.sub(r'\s+', ' ', t_m2.group(1)).strip()
            fields["title"] = raw_title.title()
            fields["confidence"]["title"] = 0.93

    if not fields["title"]:
        # Last fallback: scan all-caps lines
        skip_caps = {'ORIGINAL', 'INDIA', 'GOVERNMENT', 'PATENT', 'CERTIFICATE',
                     'INTELLECTUAL', 'PROPERTY', 'OFFICE', 'CLASS', 'SERIAL', 'CONTROLLER'}
        for line in clean.split('\n'):
            s = line.strip()
            words = s.split()
            if (len(words) >= 3
                    and all(w.isupper() or not w.isalpha() for w in words)
                    and not any(w in skip_caps for w in words)
                    and sum(1 for c in s if ord(c) < 128) / max(len(s), 1) > 0.8):
                fields["title"] = s.title()
                fields["confidence"]["title"] = 0.87
                break

    return fields


def parse_metadata(text: str, table_data: dict) -> dict:
    """Intelligently parse research metadata using table data first, then text heuristics."""
    result = {
        "title": "",
        "authors": "",
        "author_emails": "",
        "doi": "",
        "journal_or_patent_office": "",
        "year": datetime.now().year,
        "research_type": "Publication",
        "abstract": "",
        "indexing": "",
        "impact_factor": None,
        "department": "",
        # Patent-specific
        "patent_number": "",
        "inventors": "",
        "assignee": "",
        "filing_date": None,
        "publication_date": None,
        "grant_date": None,
        "confidence": {}
    }
    
    # ── 1. TABLE DATA MAPPING (Highest Priority) ──
    for key, val in table_data.items():
        if key in ('title', 'papertitle', 'researchtitle'):
            result["title"] = val
            result["confidence"]["title"] = 1.0
        elif key in ('authors', 'authornames', 'author'):
            result["authors"] = val
            result["confidence"]["authors"] = 1.0
        elif key in ('journal', 'journalname', 'conference', 'patentoffice'):
            result["journal_or_patent_office"] = val
            result["confidence"]["journal_or_patent_office"] = 1.0
        elif key in ('doi', 'doiurl'):
            result["doi"] = val
            result["confidence"]["doi"] = 1.0
        elif key in ('impactfactor', 'if'):
            try:
                # Extract first float/int found
                num = re.search(r'\d+(\.\d+)?', val)
                if num:
                    result["impact_factor"] = float(num.group(0))
                    result["confidence"]["impact_factor"] = 1.0
            except ValueError:
                pass
        elif key in ('department', 'dept'):
            result["department"] = val
            result["confidence"]["department"] = 1.0
        elif key in ('indexing', 'indexedin'):
            result["indexing"] = val
            result["confidence"]["indexing"] = 1.0
        elif key in ('publicationdate', 'submissiondate', 'date', 'year'):
            years = re.findall(YEAR_REGEX, val)
            if years:
                result["year"] = int(years[0])
                result["confidence"]["year"] = 1.0
        elif key in ('type', 'researchtype', 'category'):
            if 'patent' in val.lower():
                result["research_type"] = 'Patent'
            elif 'proposal' in val.lower():
                result["research_type"] = 'Research Proposal'
            else:
                result["research_type"] = 'Publication'
            result["confidence"]["research_type"] = 1.0
            
    # ── 2. RAW TEXT FALLBACK & ENRICHMENT ──
    text_lower = text.lower()
    
    if not result["doi"]:
        doi_match = re.search(DOI_REGEX, text, re.IGNORECASE)
        if doi_match:
            result["doi"] = doi_match.group(1)
            result["confidence"]["doi"] = 1.0
        else:
            result["confidence"]["doi"] = 0.0

    if not result["title"]:
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        title_candidates = []
        for i, line in enumerate(lines[:10]):
            ll = line.lower()
            ignore_keywords = ["copyright", "journal", "international conference", "proceedings", "symposium", "ieee", "vol.", "no.", "issn"]
            if len(line) > 15 and not line.isupper() and not any(k in ll for k in ignore_keywords):
                title_text = line
                # Check for title wrapping to the next line
                if i + 1 < len(lines):
                    next_line = lines[i+1].strip()
                    nl = next_line.lower()
                    if len(next_line) > 5 and "," not in next_line and "@" not in next_line and not any(x in nl for x in ["university", "institute", "department", "college"]):
                        title_text += " " + next_line
                title_candidates.append(title_text)
        if title_candidates:
            result["title"] = title_candidates[0][:200]
            result["confidence"]["title"] = 0.85
        else:
            result["confidence"]["title"] = 0.0

    if not result["author_emails"]:
        emails = re.findall(EMAIL_REGEX, text)
        # Check for grouped emails like {user1, user2}@domain.edu
        bracket_match = re.search(r'\{([^}]+)\}\s*@\s*([a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)', text)
        if bracket_match:
            prefixes = [p.strip() for p in bracket_match.group(1).split(',')]
            domain = bracket_match.group(2)
            emails.extend([f"{p}@{domain}" for p in prefixes if p])
            
        if emails:
            seen = set()
            unique_emails = [x for x in emails if not (x in seen or seen.add(x))]
            result["author_emails"] = ", ".join(unique_emails[:5])
            result["confidence"]["author_emails"] = 0.70
        else:
            result["confidence"]["author_emails"] = 0.0

    if not result["authors"]:
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        # Collect lines that are likely authors (between title and abstract/affiliations)
        author_candidates = []
        ignore_keywords = ["abstract", "ieee", "proceedings", "conference", "journal", "vol.", "issn"]
        affiliation_keywords = ["department", "university", "institute", "college", "school", "faculty", "laboratory", "center", "centre", "academy", "india", "usa", "uk", "china", "bangalore"]
        
        title_idx = -1
        if result["title"]:
            for i, line in enumerate(lines[:10]):
                if line in result["title"]:
                    title_idx = i
                    
        start_idx = title_idx + 1 if title_idx != -1 else 0
        
        for line in lines[start_idx:25]:
            cl = line.lower()
            if len(line) < 4 or len(line) > 200: continue
            if "@" in line: continue
            if "abstract" in cl and len(line) < 30: break
            if any(x in cl for x in ignore_keywords): continue
            if any(x in cl for x in affiliation_keywords): continue
            if re.match(r'^[\d\W]+$', line): continue # mostly symbols/numbers
            if result["title"] and line in result["title"]: continue
            
            author_candidates.append(line)
            
        if author_candidates:
            cleaned = [re.sub(r'[\d*†‡§]+', '', cand).strip() for cand in author_candidates]
            cleaned = [c for c in cleaned if c]
            joined = ", ".join(cleaned)
            joined = re.sub(r',\s*,', ',', joined).strip(', ')
            result["authors"] = joined[:150]
            result["confidence"]["authors"] = 0.75
        else:
            result["confidence"]["authors"] = 0.0

    if not result.get("confidence", {}).get("research_type"):
        if "patent" in text_lower[:1000]:
            result["research_type"] = "Patent"
            result["confidence"]["research_type"] = 0.90
            pat_match = re.search(r'(US|EP|WO|IN)\s*[-]?\s*(\d{5,12})', text_lower[:2000], re.IGNORECASE)
            if pat_match and not result["journal_or_patent_office"]:
                result["journal_or_patent_office"] = pat_match.group(1).upper() + pat_match.group(2)
                result["confidence"]["journal_or_patent_office"] = 0.95
        elif "proposal" in text_lower[:1000] or "grant" in text_lower[:1000]:
            result["research_type"] = "Research Proposal"
            result["confidence"]["research_type"] = 0.80
        else:
            result["confidence"]["research_type"] = 0.85

    if result["research_type"] == "Publication" and not result["journal_or_patent_office"]:
        if "ieee" in text_lower[:500]:
            result["journal_or_patent_office"] = "IEEE"
            if not result["indexing"]: result["indexing"] = "IEEE"
        elif "springer" in text_lower[:500]:
            result["journal_or_patent_office"] = "Springer"
            if not result["indexing"]: result["indexing"] = "Springer"
        elif "elsevier" in text_lower[:500]:
            result["journal_or_patent_office"] = "Elsevier"
            if not result["indexing"]: result["indexing"] = "Elsevier"
        elif "scopus" in text_lower[:1000]:
            if not result["indexing"]: result["indexing"] = "Scopus"
            
        if result["journal_or_patent_office"]:
            result["confidence"]["journal_or_patent_office"] = 0.90
            result["confidence"]["indexing"] = 0.90

    if not result["abstract"]:
        abstract_match = re.search(r'(?:Abstract|ABSTRACT)[\s:—-]*\n?(.*?)(?:\n\s*1\.\s*Introduction|\n\s*I\.\s*INTRODUCTION|\n\s*Keywords)', text, re.DOTALL | re.IGNORECASE)
        if abstract_match:
            abstract = abstract_match.group(1).replace('\n', ' ').strip()
            result["abstract"] = abstract[:500] + ("..." if len(abstract) > 500 else "")
            result["confidence"]["abstract"] = 0.95

    if not result.get("confidence", {}).get("year"):
        years = re.findall(YEAR_REGEX, text[:1000])
        if years:
            valid_years = [int(y) for y in years if 2000 <= int(y) <= datetime.now().year]
            if valid_years:
                result["year"] = max(valid_years)
                result["confidence"]["year"] = 0.85

    # ── 3. PATENT / DESIGN CERTIFICATE EXTRACTION ──────────────────────────
    # Detect patent/design certificate (Indian Patent Office + international)
    is_patent_doc = (
        result["research_type"] == "Patent"
        or "patent" in text_lower[:3000]
        or "design no" in text_lower[:3000]
        or "intellectual property" in text_lower[:3000]
        or "certificate of registration" in text_lower[:3000]
    )

    if is_patent_doc:
        result["research_type"] = "Patent"

        def _normalize_date(raw: str) -> str:
            """Convert DD/MM/YYYY or MM/DD/YYYY or textual dates to YYYY-MM-DD."""
            raw = raw.strip().rstrip("*:;,")
            # DD/MM/YYYY or DD-MM-YYYY (Indian format — most common)
            m = re.match(r'^(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})$', raw)
            if m:
                d, mo, y = m.groups()
                return f"{y}-{int(mo):02d}-{int(d):02d}"
            # YYYY/MM/DD or YYYY-MM-DD already
            m = re.match(r'^(\d{4})[/\-](\d{1,2})[/\-](\d{1,2})$', raw)
            if m:
                y, mo, d = m.groups()
                return f"{y}-{int(mo):02d}-{int(d):02d}"
            # Textual: "01 June 2025" / "June 01, 2025"
            months_map = {
                'jan':1,'feb':2,'mar':3,'apr':4,'may':5,'jun':6,
                'jul':7,'aug':8,'sep':9,'oct':10,'nov':11,'dec':12
            }
            m = re.match(r'(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})', raw)
            if m:
                d, mon, y = m.groups()
                mo = months_map.get(mon[:3].lower(), 0)
                if mo: return f"{y}-{mo:02d}-{int(d):02d}"
            m = re.match(r'([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})', raw)
            if m:
                mon, d, y = m.groups()
                mo = months_map.get(mon[:3].lower(), 0)
                if mo: return f"{y}-{mo:02d}-{int(d):02d}"
            return raw  # Return raw if cannot normalize

        # ── Patent / Design Number ───────────────────────────────────────
        if not result["patent_number"]:
            # Indian Design No. (e.g. 460919-001)
            dn = re.search(
                r'(?:design\s*no\.?|design\s*number|डिज़ाइन\s*स\.?\s*|design\s*s\.?\s*no\.?)'
                r'\s*[:/]?\s*([\d\-/]+)',
                text, re.IGNORECASE
            )
            if dn:
                result["patent_number"] = dn.group(1).strip()
                result["confidence"]["patent_number"] = 0.97
            else:
                # Indian patent application/pub no: IN202341012345, WO2023/..., US10123456
                pn = re.search(
                    r'(?:application\s*no\.?|patent\s*no\.?|pub\.?\s*no\.?)\s*[:/]?\s*'
                    r'((?:IN|US|EP|WO|JP|CN|GB|DE|FR)[-\s]?[\d/]{5,}(?:[A-Z]\d*)?)',
                    text, re.IGNORECASE
                )
                if pn:
                    result["patent_number"] = pn.group(1).strip()
                    result["confidence"]["patent_number"] = 0.93

        # ── Filing Date ──────────────────────────────────────────────────
        # Indian certs use "तारीख / Date" or "Date :" immediately after Design No.
        if not result["filing_date"]:
            # Priority 1: bilingual label "तारीख / Date : DD/MM/YYYY"
            fd = re.search(
                r'(?:त[ाा]र[ीि]ख\s*/\s*date|filing\s+date|filed\s+on|date\s+of\s+filing|date\s*[:/])\s*[:/]?\s*'
                r'(\d{1,2}[/\-]\d{1,2}[/\-]\d{4}|\d{4}[/\-]\d{1,2}[/\-]\d{1,2}|\d{1,2}\s+\w+\s+\d{4})',
                text, re.IGNORECASE
            )
            if fd:
                result["filing_date"] = _normalize_date(fd.group(1))
                result["confidence"]["filing_date"] = 0.97
            else:
                # Fallback: first standalone date in top portion after Design No.
                fd2 = re.search(
                    r'(?:^|\n)\s*(\d{1,2}[/\-]\d{1,2}[/\-]\d{4})',
                    text[:2000], re.MULTILINE
                )
                if fd2:
                    result["filing_date"] = _normalize_date(fd2.group(1))
                    result["confidence"]["filing_date"] = 0.80

        # ── Publication Date = "Date of Issue" ───────────────────────────
        if not result["publication_date"]:
            pd_m = re.search(
                r'(?:date\s+of\s+issue|publication\s+date|published\s+on|issue\s+date|जारी\s+करने\s+की\s+तिथि)'
                r'\s*[:/]?\s*'
                r'(\d{1,2}[/\-]\d{1,2}[/\-]\d{4}|\d{4}[/\-]\d{1,2}[/\-]\d{1,2}|\d{1,2}\s+\w+\s+\d{4})',
                text, re.IGNORECASE
            )
            if pd_m:
                result["publication_date"] = _normalize_date(pd_m.group(1))
                result["confidence"]["publication_date"] = 0.97

        # ── Grant Date ───────────────────────────────────────────────────
        if not result["grant_date"]:
            gd = re.search(
                r'(?:grant\s+date|date\s+of\s+grant|granted\s+on|date\s+of\s+patent)\s*[:/]?\s*'
                r'(\d{1,2}[/\-]\d{1,2}[/\-]\d{4}|\d{4}[/\-]\d{1,2}[/\-]\d{1,2}|\d{1,2}\s+\w+\s+\d{4})',
                text, re.IGNORECASE
            )
            if gd:
                result["grant_date"] = _normalize_date(gd.group(1))
                result["confidence"]["grant_date"] = 0.95

        # ── Title ─────────────────────────────────────────────────────────
        # Indian design/patent certs: title is the italicised ALL-CAPS noun phrase
        # e.g. "AUTOMATIC ROBOT FOR AGRICULTURE SECTOR"
        if not result["title"] or len(result["title"]) < 5:
            # Pattern 1: after "design to" / "applied to" text
            title_m = re.search(
                r'design\s+to\s+([A-Z][A-Z\s]{5,100})(?:\s+from\s+class|\s+se\s+|\n)',
                text
            )
            if not title_m:
                # Pattern 2: ALL-CAPS block that looks like a product/invention name
                title_m = re.search(
                    r'\b([A-Z][A-Z\s]{8,100}(?:SECTOR|SYSTEM|DEVICE|METHOD|APPARATUS|ROBOT|MACHINE|PROCESS|TECHNOLOGY|EQUIPMENT|TOOL|UNIT|MODULE|ASSEMBLY))\b',
                    text
                )
            if not title_m:
                # Pattern 3: between "design" keyword lines — find first standalone CAPS block
                for line in text.split('\n'):
                    stripped = line.strip()
                    if (len(stripped) > 10
                            and stripped.isupper()
                            and not any(x in stripped for x in ['ORIGINAL','INDIA','OFFICE','PATENT','CERTIFICATE','GOVERNMENT','SERIAL','CLASS'])
                       ):
                        result["title"] = stripped.title()
                        result["confidence"]["title"] = 0.88
                        break
            if title_m and not result.get("title"):
                result["title"] = title_m.group(1).strip().title()
                result["confidence"]["title"] = 0.93

        # ── Inventors ────────────────────────────────────────────────────
        if not result["inventors"]:
            # Pattern 1: numbered list "1.Dr. X 2. Y 3.Prof. Z"
            inv_block = re.search(
                r'(?:in\s+the\s+name\s+of|name\s+of\s+applicant[s]?|inventor[s]?\s*[:/]|applicant[s]?\s*[:/])'
                r'\s*((?:(?:\d+\.?\s*)?(?:Dr\.|Prof\.|Mr\.|Mrs\.|Ms\.|Sh\.|Smt\.)?'
                r'\s*[A-Z][a-zA-Z\s\.]+){1,10})',
                text, re.IGNORECASE | re.DOTALL
            )
            if inv_block:
                raw_inv = inv_block.group(1)
                # Split on numbered list pattern "1. 2. 3." or newlines
                names = re.findall(
                    r'(?:\d+\.?\s*)?((?:Dr\.|Prof\.|Mr\.|Mrs\.|Ms\.|Sh\.|Smt\.)?\s*[A-Z][A-Za-z\s\.]{2,40})',
                    raw_inv
                )
                if names:
                    clean = [n.strip().rstrip('.') for n in names if len(n.strip()) > 3]
                    result["inventors"] = ", ".join(clean[:8])
                    result["confidence"]["inventors"] = 0.92

        # ── Patent Office / Assignee ─────────────────────────────────────
        if not result["journal_or_patent_office"]:
            # Grab the English header line: "The Patent Office, Government Of India"
            po_m = re.search(
                r'((?:The\s+)?Patent\s+Office[,\s]+Government\s+(?:Of|of)\s+India)',
                text, re.IGNORECASE
            )
            if po_m:
                result["journal_or_patent_office"] = po_m.group(1).strip()
                result["confidence"]["journal_or_patent_office"] = 0.99
            elif "intellectual property india" in text_lower:
                result["journal_or_patent_office"] = "Patent Office, Government of India"
                result["confidence"]["journal_or_patent_office"] = 0.95

        if not result["assignee"]:
            # Assignee = issuing authority for Indian certs
            if "patent office" in text_lower or "intellectual property india" in text_lower:
                result["assignee"] = result["journal_or_patent_office"] or "Patent Office, Government of India"
                result["confidence"]["assignee"] = 0.97
            else:
                asgn = re.search(
                    r'(?:assignee|assigned\s+to|applicant\s+organization|institution)\s*[:/]\s*'
                    r'([A-Za-z0-9 ,&.\-]+?)(?:\n|$)',
                    text, re.IGNORECASE
                )
                if asgn:
                    result["assignee"] = asgn.group(1).strip()[:150]
                    result["confidence"]["assignee"] = 0.85

        # ── Sync year from filing_date ────────────────────────────────────
        if result["filing_date"] and not result.get("confidence", {}).get("year"):
            yr_from_filing = re.search(r'(\d{4})', result["filing_date"])
            if yr_from_filing:
                result["year"] = int(yr_from_filing.group(1))
                result["confidence"]["year"] = 0.95

    return result

def process_document(file_bytes: bytes, file_name: str) -> dict:
    """
    Full pipeline:
      - For patent/design certificates: runs dedicated patent extractor first
      - For research papers: uses table + text heuristics
    """
    table_data = {}
    is_pdf = file_name.lower().endswith('.pdf')

    # Quick-detect if this is a patent/design certificate PDF
    _sniff_text = ""
    if is_pdf:
        try:
            _doc = fitz.open(stream=file_bytes, filetype="pdf")
            _sniff_text = _doc[0].get_text("text")[:3000].lower()
        except Exception:
            pass

    is_patent_cert = any(kw in _sniff_text for kw in [
        "design no", "डिज़ाइन", "intellectual property india",
        "certificate of registration", "patent office, government",
        "registration of design",
    ])

    if is_pdf and is_patent_cert:
        # ── PATENT CERTIFICATE PIPELINE ──────────────────────────────────
        patent_fields = extract_patent_fields_from_pdf(file_bytes)
        # Build a full result dict using patent fields
        text = extract_text_from_bytes(file_bytes, file_name)   # still need for year etc.
        result = {
            "title":                    patent_fields.get("title", ""),
            "authors":                  "",
            "author_emails":            "",
            "doi":                      "",
            "journal_or_patent_office": patent_fields.get("journal_or_patent_office", ""),
            "year":                     datetime.now().year,
            "research_type":            "Patent",
            "abstract":                 "",
            "indexing":                 "",
            "impact_factor":            None,
            "department":               "",
            "patent_number":            patent_fields.get("patent_number", ""),
            "inventors":                patent_fields.get("inventors", ""),
            "assignee":                 patent_fields.get("assignee", ""),
            "filing_date":              patent_fields.get("filing_date"),
            "publication_date":         patent_fields.get("publication_date"),
            "grant_date":               None,
            "confidence":               patent_fields.get("confidence", {}),
        }
        # Sync year from filing_date
        if result["filing_date"]:
            yr_m = re.search(r'(\d{4})', result["filing_date"])
            if yr_m:
                result["year"] = int(yr_m.group(1))
        result["_debug"] = {
            "pipeline": "patent_certificate",
            "raw_text_snippet": text[:800],
        }
        return result

    # ── RESEARCH PAPER PIPELINE ───────────────────────────────────────────
    if is_pdf:
        table_data = extract_tables_from_pdf(file_bytes)
    text = extract_text_from_bytes(file_bytes, file_name)
    metadata = parse_metadata(text, table_data)
    metadata["_debug"] = {
        "pipeline": "research_paper",
        "table_data": table_data,
        "raw_text_snippet": text[:800] + "..." if len(text) > 800 else text,
    }
    return metadata
