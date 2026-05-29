"""
pages/faculty_category.py - Per-category research entry management
Handles: Journal, Conference, Patent, Research Proposal, FDP, Consultancy, Project
"""
from __future__ import annotations
import streamlit as st
from datetime import date

from database.queries import (
    fetch_my_entries, add_research_entry, update_research_entry,
    delete_research_entry,
)
from services.auth_service import get_current_profile, get_current_user
from services.export_service import entries_to_dataframe, to_csv_bytes, to_excel_bytes
from services.ai_extraction import process_document
from services.storage_service import upload_document
from components.ui import section_header, status_badge
from utils.helpers import get_years_list, num_to_month_name
from utils.validators import sanitize_text
from config import (
    INDEXING_OPTIONS, PUBLICATION_STATUSES, PATENT_STATUSES,
    PROPOSAL_STATUSES, FDP_STATUSES, CONSULTANCY_STATUSES, PROJECT_STATUSES,
)

# ── Icons & labels per type ───────────────────────────────
TYPE_META = {
    "Journal":          {"icon": "📓", "color": "#3498DB", "desc": "Manage your journal publications"},
    "Conference":       {"icon": "🎙️", "color": "#9B59B6", "desc": "Track conference papers & presentations"},
    "Patent":           {"icon": "💡", "color": "#F18F01", "desc": "Track filed, published and granted patents"},
    "Research Proposal":{"icon": "📋", "color": "#E74C3C", "desc": "Monitor research funding proposals"},
    "FDP":              {"icon": "🎓", "color": "#1ABC9C", "desc": "Faculty Development Programs attended/organised"},
    "Consultancy":      {"icon": "🤝", "color": "#2ECC71", "desc": "Consultancy projects and client engagements"},
    "Project":          {"icon": "🔬", "color": "#2E86AB", "desc": "Sponsored & institutional research projects"},
}

def _parse_date(val) -> date | None:
    """Safely parse a date from a YYYY-MM-DD string or date object."""
    if val is None:
        return None
    if isinstance(val, date):
        return val
    if isinstance(val, str) and len(val) >= 10:
        try:
            return date.fromisoformat(val[:10])
        except ValueError:
            return None
    return None


def _status_opts(rtype: str) -> list:
    return {
        "Journal": PUBLICATION_STATUSES,
        "Conference": PUBLICATION_STATUSES,
        "Patent": PATENT_STATUSES,
        "Research Proposal": PROPOSAL_STATUSES,
        "FDP": FDP_STATUSES,
        "Consultancy": CONSULTANCY_STATUSES,
        "Project": PROJECT_STATUSES,
    }.get(rtype, PUBLICATION_STATUSES)


@st.dialog("Add New Entry", width="large")
def render_add_dialog(faculty_id: str, profile: dict, rtype: str):
    _add_form(faculty_id, profile, rtype)

@st.dialog("Edit Entry", width="large")
def render_edit_dialog(entry: dict, rtype: str):
    _edit_form(entry, rtype)

@st.dialog("Upload Document")
def render_upload_dialog(entry_id: str, title: str, faculty_id: str):
    st.markdown(f"Upload a supporting document for **{title}**")
    uploaded_file = st.file_uploader("Select PDF/DOCX/TXT", type=["pdf", "docx", "txt"], key=f"modal_up_{entry_id}")
    if uploaded_file and st.button("Upload & Save", use_container_width=True, type="primary"):
        with st.spinner("Uploading document..."):
            file_bytes = uploaded_file.read()
            doc_url = upload_document(file_bytes, uploaded_file.name, faculty_id)
            if doc_url:
                if update_research_entry(entry_id, {"document_url": doc_url}):
                    st.success("✅ Uploaded successfully!")
                    st.rerun()

def render_faculty_category(rtype: str):
    meta   = TYPE_META.get(rtype, TYPE_META["Journal"])
    user   = get_current_user()
    profile= get_current_profile()
    uid    = user["id"]

    # Header
    st.markdown(f"""
    <h1 style='margin-bottom:4px;font-size:2rem;font-weight:800;'>
        {meta['icon']} {rtype}s
    </h1>
    <p style='color:#64748B;margin-bottom:24px;'>{meta['desc']}</p>
    """, unsafe_allow_html=True)

    entries = [e for e in fetch_my_entries(uid) if e.get("research_type") == rtype]

    # Search / filter bar
    sc1, sc2, sc3 = st.columns([3, 1, 1])
    with sc1: srch = st.text_input("🔍 Search by title / number", key=f"srch_{rtype}")
    with sc2: yr   = st.selectbox("Year", ["All"] + [str(y) for y in get_years_list()], key=f"yr_{rtype}")
    with sc3: stat = st.selectbox("Status", ["All"] + _status_opts(rtype), key=f"st_{rtype}")

    filtered = [e for e in entries
                if (not srch or srch.lower() in (e.get("title","") or "").lower()
                               or srch.lower() in (e.get("patent_number","") or "").lower())
                and (yr   == "All" or str(e.get("year","")) == yr)
                and (stat == "All" or e.get("status","") == stat)]

    # Export + Add button row
    ex1, ex2, _, add_col = st.columns([1, 1, 3, 1])
    if filtered:
        df = entries_to_dataframe(filtered)
        with ex1:
            st.download_button("⬇ CSV",   to_csv_bytes(df),   f"{rtype.lower()}.csv", "text/csv", use_container_width=True)
        with ex2:
            st.download_button("⬇ Excel", to_excel_bytes(df), f"{rtype.lower()}.xlsx",
                               "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                               use_container_width=True)
    with add_col:
        if st.button(f"+ Add {rtype}", type="primary", use_container_width=True, key=f"add_btn_{rtype}"):
            render_add_dialog(uid, profile, rtype)

    st.markdown("---")

    # Entry list
    if not filtered:
        st.markdown(f"""
        <div style='text-align:center;padding:60px 20px;color:#94A3B8;'>
            <div style='font-size:3rem;margin-bottom:16px;'>{meta['icon']}</div>
            <p style='font-size:1.1rem;'>No {rtype.lower()}s found.</p>
        </div>""", unsafe_allow_html=True)
        if st.button(f"+ Add your first {rtype}", type="primary", key=f"first_add_{rtype}"):
            render_add_dialog(uid, profile, rtype)
    else:
        _render_entries_table(filtered, rtype)
        st.markdown(f"**{len(filtered)} record(s) found**")



def _smart_date(entry: dict, rtype: str) -> str:
    """Return the correct display date: publication_date for Patents, doc year for others."""
    try:
        if rtype == "Patent":
            for field in ("publication_date", "filing_date", "submission_date"):
                v = entry.get(field)
                if v and len(str(v)) >= 10:
                    from datetime import date as _d
                    return _d.fromisoformat(str(v)[:10]).strftime("%b %Y")
        # For all other types use the stored year + month, or submission_date
        yr = entry.get("year")
        mo = entry.get("month")
        if yr and mo:
            from datetime import date as _d
            return _d(int(yr), int(mo), 1).strftime("%b %Y")
        if yr:
            return str(yr)
        sub = entry.get("submission_date")
        if sub:
            from datetime import date as _d
            return _d.fromisoformat(str(sub)[:10]).strftime("%b %Y")
    except Exception:
        pass
    return "—"



def _render_entries_table(entries: list, rtype: str):
    """Renders entries as an interactive table with per-row inline Edit/Delete."""
    st.markdown("""
    <style>
    .rt-hdr{font-size:.68rem;font-weight:700;color:#64748B;text-transform:uppercase;
            letter-spacing:.07em;padding-bottom:4px;}
    .rt-title{font-size:.9rem;font-weight:600;color:#1E293B;line-height:1.35;}
    .rt-sub{font-size:.78rem;color:#475569;}
    .rt-chip{background:#F1F5F9;border-radius:20px;padding:2px 10px;
             font-size:.78rem;color:#475569;display:inline-block;}
    .inline-edit-box{background:#F8FAFC;border-left:3px solid #3B82F6;
                     border-radius:0 8px 8px 0;padding:14px 16px;margin:6px 0 10px 0;}
    .inline-del-box{background:#FEF2F2;border-left:3px solid #EF4444;
                    border-radius:0 8px 8px 0;padding:10px 16px;margin:6px 0 10px 0;}
    </style>
    """, unsafe_allow_html=True)

    # Column widths
    CW = [3.8, 1.8, 1.6, 1.1, 0.55, 0.48, 0.48]
    if rtype == "Patent":   extra_h = "Patent No."
    elif rtype in ("Consultancy", "Project"): extra_h = "Agency/Client"
    else:                   extra_h = "Venue"

    # Header row
    hcols = st.columns(CW)
    for hc, hl in zip(hcols, ["Title", extra_h, "Status", "Date", "Doc", "✏", "🗑"]):
        hc.markdown(f"<div class='rt-hdr'>{hl}</div>", unsafe_allow_html=True)
    st.markdown("<hr style='margin:2px 0 6px 0;border-color:#E2E8F0;'>", unsafe_allow_html=True)

    for i, e in enumerate(entries):
        eid = e["id"]
        title = (e.get("title") or "")

        if rtype == "Patent":
            extra_val = e.get("patent_number") or "—"
        elif rtype in ("Consultancy", "Project"):
            extra_val = (e.get("funding_agency") or e.get("client_name") or "—")[:28]
        else:
            extra_val = (e.get("journal_or_patent_office") or "")[:28]

        display_dt = _smart_date(e, rtype)
        doc_url    = e.get("document_url")

        # Data row
        rcols = st.columns(CW)
        rcols[0].markdown(f"<div class='rt-title'>{title[:52]}{'…' if len(title)>52 else ''}</div>",
                          unsafe_allow_html=True)
        rcols[1].markdown(f"<div class='rt-sub'>{extra_val}</div>", unsafe_allow_html=True)
        rcols[2].markdown(status_badge(e.get("status", "")), unsafe_allow_html=True)
        rcols[3].markdown(f"<span class='rt-chip'>{display_dt}</span>", unsafe_allow_html=True)
        if doc_url:
            rcols[4].markdown(f"<a href='{doc_url}' target='_blank' style='font-size:1.1rem;' title='Download Document'>&#11015;&#65039;</a>",
                              unsafe_allow_html=True)
        else:
            if rcols[4].button("⬆️", key=f"upbtn_{eid}", help="Upload Document", use_container_width=True):
                render_upload_dialog(eid, title, e.get("faculty_id"))

        # Edit button
        if rcols[5].button("✏️", key=f"eb_{eid}", help="Edit", use_container_width=True):
            render_edit_dialog(e, rtype)

        # Delete button
        if rcols[6].button("🗑️", key=f"db_{eid}", help="Delete", use_container_width=True):
            cur = st.session_state.get(f"id_{eid}", False)
            st.session_state[f"id_{eid}"] = not cur

        # Inline Delete confirmation
        if st.session_state.get(f"id_{eid}"):
            st.markdown("<div class='inline-del-box'>", unsafe_allow_html=True)
            st.warning(f"⚠️ Delete **\"{title[:45]}\"** permanently? This cannot be undone.")
            d1, d2, _ = st.columns([1, 1, 4])
            with d1:
                if st.button("✅ Yes, Delete", key=f"dyes_{eid}", type="primary"):
                    delete_research_entry(eid)
                    st.session_state.pop(f"id_{eid}", None)
                    st.rerun()
            with d2:
                if st.button("❌ Cancel", key=f"dno_{eid}"):
                    st.session_state.pop(f"id_{eid}", None)
                    st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        if i < len(entries) - 1:
            st.markdown("<hr style='margin:4px 0;border-color:#E2E8F0;opacity:1;'>",
                        unsafe_allow_html=True)


def _ai_upload_section(rtype: str, faculty_id: str):
    """Shared AI upload widget, returns (meta, doc_url)."""
    with st.expander("🤖 AI Document Upload — Auto-fill Fields", expanded=True):
        up = st.file_uploader("Upload PDF/DOCX/TXT", type=["pdf","docx","txt"], key=f"up_{rtype}")
        if up and st.button("✨ Extract Metadata", use_container_width=True, key=f"ext_{rtype}"):
            with st.spinner("Analysing document…"):
                fbytes = up.read()
                m = process_document(fbytes, up.name)
                dup = any(
                    e.get("title","").strip().lower() == (m.get("title","") or "").strip().lower()
                    for e in fetch_my_entries(faculty_id)
                )
                if dup:
                    st.error("🚫 Duplicate document detected — this title already exists.")
                else:
                    url = upload_document(fbytes, up.name, faculty_id)
                    st.session_state[f"ai_meta_{rtype}"] = m
                    if url:
                        st.session_state[f"ai_url_{rtype}"] = url
                    st.success(f"✅ `{up.name}` uploaded & metadata extracted.")
        if f"ai_meta_{rtype}" in st.session_state:
            conf = st.session_state[f"ai_meta_{rtype}"].get("confidence", {})
            if conf:
                st.markdown("##### 🔍 Extraction Confidence")
                cols = st.columns(min(len(conf), 4))
                for i,(k,v) in enumerate({k:v for k,v in conf.items() if v>0 and not k.startswith("_")}.items()):
                    with cols[i%4]: st.metric(k.replace("_"," ").title(), f"{int(v*100)}%")
    return (
        st.session_state.get(f"ai_meta_{rtype}", {}),
        st.session_state.get(f"ai_url_{rtype}", None)
    )


def _add_form(faculty_id: str, profile: dict, rtype: str):
    meta, doc_url = _ai_upload_section(rtype, faculty_id)
    st.markdown("---")

    with st.form(f"add_{rtype}_form", clear_on_submit=False):
        # ── Common fields ───────────────────────────────
        title = st.text_input("📌 Title *", value=meta.get("title",""))
        status = st.selectbox("📊 Status", _status_opts(rtype))
        # Smart date default: patent -> publication_date; others -> AI year
        if rtype == "Patent":
            _def = _parse_date(meta.get("publication_date")) or _parse_date(meta.get("filing_date")) or date.today()
        elif meta.get("year"):
            try: _def = date(int(meta["year"]), 1, 1)
            except Exception: _def = date.today()
        else:
            _def = date.today()
        sub_date = st.date_input("📅 Date", value=_def)

        # ── Type-specific fields ────────────────────────
        if rtype == "Patent":
            # Show AI confidence on extracted date fields
            conf = meta.get("confidence", {})
            filing_conf  = conf.get("filing_date", 0)
            pub_conf     = conf.get("publication_date", 0)

            c1, c2 = st.columns(2)
            with c1:
                patent_number    = st.text_input("📜 Patent / Design Number", value=meta.get("patent_number",""))
                fd_val           = _parse_date(meta.get("filing_date"))
                filing_label     = f"📅 Filing Date {'✅ AI-filled' if filing_conf >= 0.8 else ''}"
                filing_date      = st.date_input(filing_label, value=fd_val)
                pd_val           = _parse_date(meta.get("publication_date"))
                pub_label        = f"📅 Publication Date (Date of Issue) {'✅ AI-filled' if pub_conf >= 0.8 else ''}"
                publication_date = st.date_input(pub_label, value=pd_val)
            with c2:
                inventors = st.text_area("👥 Inventors", value=meta.get("inventors",""), height=90)
                assignee  = st.text_input("🏛️ Assignee",  value=meta.get("assignee",""))
                notes     = st.text_area("📝 Description",value=meta.get("abstract",""), height=90)
            venue = st.text_input(
                "🏛️ Patent Office",
                value=meta.get("journal_or_patent_office", "")
            )
            grant_date = None
            funding_agency = funding_amount = client_name = project_duration = None
            doi = indexing = ""
            impact_factor = 0.0

        elif rtype in ("Journal", "Conference"):
            c1, c2 = st.columns(2)
            with c1:
                venue = st.text_input(
                    "📓 Journal Name" if rtype=="Journal" else "🎙️ Conference Name",
                    value=meta.get("journal_or_patent_office","")
                )
                doi   = st.text_input("🔗 DOI", value=meta.get("doi",""))
            with c2:
                indexing      = st.selectbox("🔖 Indexing", [""]+INDEXING_OPTIONS)
                impact_factor = st.number_input("📈 Impact Factor", 0.0, step=0.001, format="%.3f")
            notes = st.text_area("📝 Abstract", value=meta.get("abstract",""), height=68)
            patent_number = filing_date = publication_date = grant_date = None
            inventors = assignee = ""
            funding_agency = funding_amount = client_name = project_duration = None

        elif rtype == "Research Proposal":
            c1, c2 = st.columns(2)
            with c1:
                funding_agency = st.text_input("🏛️ Funding Agency", value=meta.get("journal_or_patent_office",""))
                funding_amount = st.number_input("💰 Amount (₹)", 0.0, step=1000.0)
            with c2:
                doi = indexing = ""
                impact_factor  = 0.0
                venue = ""
            notes = st.text_area("📝 Description", value=meta.get("abstract",""), height=68)
            patent_number = filing_date = publication_date = grant_date = None
            inventors = assignee = client_name = project_duration = None

        elif rtype == "FDP":
            venue     = st.text_input("🏫 Organising Institution")
            notes     = st.text_area("📝 Details", height=68)
            doi = indexing = ""
            impact_factor  = 0.0
            patent_number = filing_date = publication_date = grant_date = None
            inventors = assignee = ""
            funding_agency = funding_amount = client_name = project_duration = None

        elif rtype == "Consultancy":
            c1, c2 = st.columns(2)
            with c1:
                client_name    = st.text_input("🏢 Client Name")
                funding_amount = st.number_input("💰 Amount (₹)", 0.0, step=1000.0)
            with c2:
                project_duration = st.text_input("⏱️ Duration (e.g. 6 months)")
                funding_agency   = st.text_input("🏛️ Funding Agency")
            notes = st.text_area("📝 Scope of Work", height=68)
            venue = doi = indexing = ""
            impact_factor = 0.0
            patent_number = filing_date = publication_date = grant_date = None
            inventors = assignee = ""

        else:  # Project
            c1, c2 = st.columns(2)
            with c1:
                funding_agency   = st.text_input("🏛️ Funding Agency / Sponsor")
                funding_amount   = st.number_input("💰 Amount (₹)", 0.0, step=1000.0)
            with c2:
                project_duration = st.text_input("⏱️ Duration")
                venue = ""
            notes = st.text_area("📝 Objectives", height=68)
            doi = indexing = ""
            impact_factor = 0.0
            patent_number = filing_date = publication_date = grant_date = None
            inventors = assignee = client_name = ""

        # Authors field only for non-patent types
        if rtype != "Patent":
            authors = st.text_input("👥 Authors / Team Members", value=meta.get("authors",""))
        else:
            authors = None
        is_nba  = st.checkbox("✅ Include in NBA Report", value=True)
        submitted = st.form_submit_button(f"🚀 Submit {rtype}", use_container_width=True, type="primary")

    if submitted:
        if not title.strip():
            st.error("❌ Title is required.")
            return
        row = {
            "faculty_id":              faculty_id,
            "title":                   sanitize_text(title),
            "research_type":           rtype,
            "journal_or_patent_office": sanitize_text(venue) if venue else None,
            "authors":                 sanitize_text(authors) or None,
            "doi":                     sanitize_text(doi) if doi else None,
            "indexing":                indexing or None,
            "impact_factor":           float(impact_factor) if impact_factor else None,
            "status":                  status,
            "submission_date":         sub_date.isoformat(),
            "month":                   sub_date.month,
            "year":                    sub_date.year,
            "department":              profile.get("department"),
            "funding_agency":          sanitize_text(funding_agency) if funding_agency else None,
            "funding_amount":          float(funding_amount) if funding_amount else None,
            "patent_number":           sanitize_text(patent_number) if patent_number else None,
            "inventors":               sanitize_text(inventors) if inventors else None,
            "assignee":                sanitize_text(assignee) if assignee else None,
            "filing_date":             filing_date.isoformat() if filing_date else None,
            "publication_date":        publication_date.isoformat() if publication_date else None,
            "grant_date":              grant_date.isoformat() if grant_date else None,
            "client_name":             sanitize_text(client_name) if client_name else None,
            "project_duration":        sanitize_text(project_duration) if project_duration else None,
            "notes":                   sanitize_text(notes) or None,
            "is_nba_relevant":         is_nba,
            "document_url":            doc_url,
            "extracted_metadata":      meta if meta else None,
            "ai_processed":            bool(meta),
        }
        with st.spinner("Saving…"):
            if add_research_entry(row):
                for k in (f"ai_meta_{rtype}", f"ai_url_{rtype}", f"show_add_{rtype}"):
                    st.session_state.pop(k, None)
                st.success(f"✅ {rtype} submitted successfully!")
                st.balloons()
                st.rerun()


def _edit_form(entry: dict, rtype: str):
    eid = entry["id"]
    with st.form(f"edit_{eid}"):
        title  = st.text_input("Title", value=entry.get("title",""))
        status = st.selectbox("Status", _status_opts(rtype),
                              index=_status_opts(rtype).index(entry.get("status", _status_opts(rtype)[0]))
                                    if entry.get("status") in _status_opts(rtype) else 0)
        sub_val  = entry.get("submission_date")
        sub_date = date.fromisoformat(sub_val[:10]) if sub_val else date.today()
        sub_date = st.date_input("Date", value=sub_date)

        if rtype == "Patent":
            c1, c2 = st.columns(2)
            with c1:
                patent_number    = st.text_input("Patent Number",  value=entry.get("patent_number","") or "")
                def _parse_d(v): return date.fromisoformat(v[:10]) if v and len(v)>=10 else None
                filing_date      = st.date_input("Filing Date",     value=_parse_d(entry.get("filing_date")))
                publication_date = st.date_input("Publication Date (Date of Issue)", value=_parse_d(entry.get("publication_date")))
            with c2:
                inventors = st.text_area("Inventors",    value=entry.get("inventors","") or "", height=80)
                assignee  = st.text_input("Assignee",    value=entry.get("assignee","") or "")
                notes     = st.text_area("Description",  value=entry.get("notes","") or "", height=80)
            venue = st.text_input("Patent Office", value=entry.get("journal_or_patent_office","") or "")
            grant_date = None
            funding_agency = funding_amount = client_name = project_duration = None
            doi = indexing = ""
        else:
            venue             = st.text_input("Venue / Office / Body", value=entry.get("journal_or_patent_office","") or "")
            notes             = st.text_area("Notes / Abstract",       value=entry.get("notes","") or "", height=68)
            patent_number     = None
            filing_date       = publication_date = grant_date = None
            inventors         = assignee = ""
            funding_agency    = st.text_input("Funding Agency",        value=entry.get("funding_agency","") or "")
            funding_amount    = st.number_input("Amount (₹)", 0.0, step=1000.0, value=float(entry.get("funding_amount") or 0))
            client_name       = st.text_input("Client",                value=entry.get("client_name","") or "")
            project_duration  = st.text_input("Duration",              value=entry.get("project_duration","") or "")
            doi = indexing    = ""

        is_nba = st.checkbox("Include in NBA Report", value=entry.get("is_nba_relevant", True))

        if st.form_submit_button("💾 Save Changes", use_container_width=True):
            updates = {
                "title":                    sanitize_text(title),
                "status":                   status,
                "submission_date":          sub_date.isoformat(),
                "month":                    sub_date.month,
                "year":                     sub_date.year,
                "journal_or_patent_office": sanitize_text(venue) if venue else None,
                "notes":                    sanitize_text(notes) or None,
                "patent_number":            sanitize_text(patent_number) if patent_number else None,
                "inventors":                sanitize_text(inventors) if inventors else None,
                "assignee":                 sanitize_text(assignee) if assignee else None,
                "filing_date":              filing_date.isoformat() if filing_date else None,
                "publication_date":         publication_date.isoformat() if publication_date else None,
                "grant_date":               grant_date.isoformat() if grant_date else None,
                "funding_agency":           sanitize_text(funding_agency) if funding_agency else None,
                "funding_amount":           float(funding_amount) if funding_amount else None,
                "client_name":              sanitize_text(client_name) if client_name else None,
                "project_duration":         sanitize_text(project_duration) if project_duration else None,
                "is_nba_relevant":          is_nba,
            }
            if update_research_entry(eid, updates):
                st.success("✅ Updated successfully!")
                st.rerun()
