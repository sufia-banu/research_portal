"""
pages/faculty_dashboard.py - Enhanced Faculty Dashboard
"""
from __future__ import annotations
import streamlit as st
import pandas as pd
from datetime import date

from database.queries import (
    fetch_my_entries, add_research_entry, update_research_entry,
    delete_research_entry, get_faculty_stats, fetch_active_reminders,
)
from services.auth_service import get_current_profile, get_current_user, get_current_role
from services.export_service import entries_to_dataframe, to_csv_bytes, to_excel_bytes
from components.ui import metric_card, page_header, section_header, reminder_card, status_badge
from utils.charts import (
    pie_chart, yearly_comparison,
    horizontal_bar, line_chart,
)
from utils.helpers import get_years_list, num_to_month_name
from utils.validators import validate_research_entry, sanitize_text
from config import (
    RESEARCH_TYPES, INDEXING_OPTIONS, MONTHS,
    PUBLICATION_STATUSES, PATENT_STATUSES, PROPOSAL_STATUSES,
    FDP_STATUSES, CONSULTANCY_STATUSES, PROJECT_STATUSES,
)
from services.ai_extraction import process_document
from services.storage_service import upload_document, download_document_bytes
from pages.faculty_category import render_faculty_category, render_upload_dialog  # re-export for router
import json


def _status_opts(rtype): 
    return {"Publication": PUBLICATION_STATUSES,
            "Journal": PUBLICATION_STATUSES,
            "Conference": PUBLICATION_STATUSES,
            "Book": PUBLICATION_STATUSES,
            "Patent": PATENT_STATUSES}.get(rtype, PROPOSAL_STATUSES)


def render_faculty_dashboard():
    profile = get_current_profile()
    user    = get_current_user()

    page_header("Faculty Dashboard",
                f"My Research Portfolio · {profile.get('department','')}", "")

    # Limit Warnings (from previous submission)
    if "limit_warning" in st.session_state:
        st.warning(st.session_state.pop("limit_warning"))

    # Reminders
    reminders = fetch_active_reminders("faculty")
    if reminders:
        with st.expander(f"🔔 {len(reminders)} Active Reminder(s)"):
            for r in reminders: reminder_card(r)

    # Stats row
    stats = get_faculty_stats(user["id"])
    c1, c2, c3, c4 = st.columns(4)
    with c1: metric_card("Total", stats["total"], "📄", color="#2E86AB")
    with c2: metric_card("Journals", stats["journals"], "📓", color="#3498DB")
    with c3: metric_card("Conferences", stats["conferences"], "🎙️", color="#9B59B6")
    with c4: metric_card("Patents", stats["patents"], "💡", color="#F18F01")
    c5, c6, c7, c8 = st.columns(4)
    with c5: metric_card("Research Proposals", stats["proposals"], "📋", color="#E74C3C")
    with c6: metric_card("FDPs", stats["fdps"], "🎓", color="#1ABC9C")
    with c7: metric_card("Consultancy", stats["consultancies"], "🤝", color="#2ECC71")
    with c8: metric_card("Projects", stats["projects"], "🔬", color="#8E44AD")

    st.markdown("<br>", unsafe_allow_html=True)
    tab_entries, tab_analytics = st.tabs(
        ["📋 My Entries", "📊 Analytics"])

    # ── MY ENTRIES ────────────────────────────────────────
    with tab_entries:
        # Google Scholar Import Section
        with st.expander("🤖 Import from Google Scholar", expanded=st.session_state.get("scholar_expanded", False)):
            scholar_link = profile.get("google_scholar_link")
            if not scholar_link:
                st.warning("⚠️ You haven't added a Google Scholar link to your profile. Please add it in 'My Profile' to use this feature.")
            else:
                st.info(f"🔗 **Connected Profile:** {scholar_link}")
                if st.button("Fetch Publications from Google Scholar", type="primary"):
                    st.session_state["scholar_expanded"] = True
                    with st.spinner("Fetching from Google Scholar..."):
                        from services.google_scholar_service import fetch_scholar_publications
                        success, data = fetch_scholar_publications(scholar_link)
                        if not success:
                            st.error(data)
                        else:
                            st.session_state["scholar_results"] = data
                            st.rerun()
                            
            if "scholar_results" in st.session_state:
                results = st.session_state["scholar_results"]
                st.success(f"Found {len(results)} publications!")
                
                existing_titles = {e.get("title", "").strip().lower() for e in fetch_my_entries(user["id"])}
                
                st.write("Select publications to import (duplicates are auto-detected):")
                with st.form("scholar_import_form"):
                    selected_indices = []
                    for i, r in enumerate(results):
                        title = r.get("title","")
                        is_dup = title.strip().lower() in existing_titles
                        label = f"**{title}**" if not is_dup else f"~~{title}~~ *(Already Imported)*"
                        
                        col1, col2, col3 = st.columns([0.1, 3, 1])
                        with col1:
                            # Note: Checkboxes inside forms don't return dynamic state until submit. 
                            # We can capture the checked state upon submit by using the session_state key or checking return value.
                            # Streamlit form widgets return their value upon submit!
                            chk = st.checkbox("", key=f"sch_{i}", value=not is_dup, disabled=is_dup)
                        with col2:
                            st.markdown(label)
                            st.caption(f"{r.get('authors','')} - {r.get('journal_or_patent_office','')}")
                        with col3:
                            st.caption(f"Year: {r.get('year','')}")
                            
                    st.markdown("---")
                    col_btn1, col_btn2, _ = st.columns([2, 1, 3])
                    with col_btn1:
                        submitted = st.form_submit_button("Import Selected Publications", type="primary")
                    with col_btn2:
                        cancelled = st.form_submit_button("Cancel")

                    if submitted:
                        selected_count = 0
                        for i, r in enumerate(results):
                            if st.session_state.get(f"sch_{i}", False):
                                data_to_insert = {
                                    "faculty_id": user["id"],
                                    "title": sanitize_text(r.get("title", "")),
                                    "research_type": "Publication",
                                    "journal_or_patent_office": sanitize_text(r.get("journal_or_patent_office", ""))[:255] if r.get("journal_or_patent_office") else None,
                                    "authors": sanitize_text(r.get("authors", "")),
                                    "year": r.get("year"),
                                    "month": 1,
                                    "status": "Published",
                                    "department": profile.get("department"),
                                    "notes": f"Cited by: {r.get('cited_by', 0)}\nGoogle Scholar Link: {r.get('link', '')}",
                                    "is_nba_relevant": True
                                }
                                if add_research_entry(data_to_insert):
                                    selected_count += 1
                        st.success(f"Successfully imported {selected_count} publications!")
                        st.session_state.pop("scholar_results", None)
                        st.session_state["scholar_expanded"] = False
                        st.rerun()
                        
                    if cancelled:
                        st.session_state.pop("scholar_results", None)
                        st.session_state["scholar_expanded"] = False
                        st.rerun()
                        
        st.markdown("<br>", unsafe_allow_html=True)
        entries = fetch_my_entries(user["id"])
        fc1, fc2, fc3 = st.columns(3)
        with fc1: ftype  = st.selectbox("Type", ["All"] + RESEARCH_TYPES, key="fe_t")
        with fc2: fyear  = st.selectbox("Year", ["All"] + [str(y) for y in get_years_list()], key="fe_y")
        with fc3: fsrch  = st.text_input("🔍 Search Title", key="fe_s")

        filtered = [e for e in entries
                    if (ftype == "All" or e["research_type"] == ftype)
                    and (fyear == "All" or str(e.get("year","")) == fyear)
                    and (not fsrch or fsrch.lower() in e.get("title","").lower())]

        if filtered:
            df_exp = entries_to_dataframe(filtered)
            ex1, ex2, _ = st.columns([1, 1, 4])
            with ex1:
                st.download_button("⬇ CSV", to_csv_bytes(df_exp),
                                   "my_research.csv", "text/csv", use_container_width=True)
            with ex2:
                st.download_button("⬇ Excel", to_excel_bytes(df_exp),
                                   "my_research.xlsx",
                                   "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                   use_container_width=True)

        st.markdown(f"**{len(filtered)} record(s)**")
        if not filtered:
            st.info("No entries yet. Use **Add Entry** to submit your research.")
        else:
            _render_table(filtered, show_faculty=False)

    # Add entry tab removed.

    # ── ANALYTICS ────────────────────────────────────────
    with tab_analytics:
        section_header("My Research Analytics", "📊")
        all_e = fetch_my_entries(user["id"])
        if not all_e:
            st.info("Submit entries to see analytics.")
            return

        # Row 1: type + status pie
        r1c1, r1c2 = st.columns(2)
        with r1c1:
            st.plotly_chart(pie_chart(
                ["Journal", "Conference", "Patent", "Research Proposal"],
                [stats["journals"], stats["conferences"], stats["patents"], stats["proposals"]],
                "Research Type Distribution"), use_container_width=True)
        with r1c2:
            sc = {}
            for e in all_e:
                s = e.get("status", "Unknown"); sc[s] = sc.get(s, 0) + 1
            st.plotly_chart(pie_chart(list(sc.keys()), list(sc.values()),
                                      "Status Distribution"), use_container_width=True)

        # Row 2: Year-wise output (single clean chart replacing duplicates)
        section_header("Year-wise Research Output", "📅")
        yr_data = {}
        for e in all_e:
            y = e.get("year")
            t = e.get("research_type", "Other")
            if y:
                if y not in yr_data:
                    yr_data[y] = {"Journal": 0, "Conference": 0, "Patent": 0, "Research Proposal": 0}
                yr_data[y][t] = yr_data[y].get(t, 0) + 1
        if yr_data:
            years_sorted = sorted(yr_data.keys())
            st.plotly_chart(yearly_comparison(all_e, "Year-wise Research Output"),
                            use_container_width=True)


# ── TABLE with inline Edit / Delete ─────────────────────────────────────────
def _render_table(entries, show_faculty=False):
    st.markdown("""
    <style>
    .ov-hdr{font-size:.67rem;font-weight:700;color:#64748B;text-transform:uppercase;
            letter-spacing:.07em;padding-bottom:3px;}
    .ov-title{font-size:.88rem;font-weight:600;color:#1E293B;line-height:1.3;}
    .ov-sub{font-size:.76rem;color:#475569;}
    .ov-chip{background:#F1F5F9;border-radius:20px;padding:2px 9px;
             font-size:.76rem;color:#475569;display:inline-block;}
    .ov-edit-panel{background:#F8FAFC;border-left:3px solid #3B82F6;
                   border-radius:0 8px 8px 0;padding:14px 16px;margin:4px 0 10px 0;}
    .ov-del-panel{background:#FEF2F2;border-left:3px solid #EF4444;
                  border-radius:0 8px 8px 0;padding:10px 16px;margin:4px 0 10px 0;}
    </style>
    """, unsafe_allow_html=True)

    # Column layout: Title | Type | Venue | Indexing | Status | Date | Doc | ✏ | 🗑
    CW = [3.2, 1.2, 1.8, 1.0, 1.3, 1.0, 0.5, 0.42, 0.42]
    hdrs = ["Title", "Type", "Journal/Office", "Indexing", "Status", "Date", "Doc", "✏", "🗑"]
    if show_faculty:
        CW = [1.5] + CW
        hdrs = ["Faculty"] + hdrs

    hcols = st.columns(CW)
    for hc, hl in zip(hcols, hdrs):
        hc.markdown(f"<div class='ov-hdr'>{hl}</div>", unsafe_allow_html=True)
    st.markdown("<hr style='margin:2px 0 6px 0;border-color:#E2E8F0;'>", unsafe_allow_html=True)

    for i, e in enumerate(entries):
        eid  = e["id"]
        title = (e.get("title") or "")
        rtype = e.get("research_type", "")
        venue = (e.get("journal_or_patent_office") or "")[:28]
        idx   = e.get("indexing") or "—"
        doc   = e.get("document_url")
        # Smart date: for patents use publication_date, else year/month
        try:
            if rtype == "Patent":
                pdate = e.get("publication_date") or e.get("filing_date") or e.get("submission_date")
                disp_date = date.fromisoformat(str(pdate)[:10]).strftime("%b %Y") if pdate else "—"
            else:
                yr = e.get("year"); mo = e.get("month")
                disp_date = date(int(yr), int(mo or 1), 1).strftime("%b %Y") if yr else "—"
        except Exception:
            disp_date = str(e.get("year", "—"))

        rcols = st.columns(CW)
        col_offset = 0
        if show_faculty:
            fac = e.get("profiles", {})
            fname = fac.get("full_name", "—") if isinstance(fac, dict) else "—"
            rcols[0].markdown(f"<div class='ov-sub'>{fname}</div>", unsafe_allow_html=True)
            col_offset = 1

        rcols[col_offset+0].markdown(
            f"<div class='ov-title'>{title[:50]}{'…' if len(title)>50 else ''}</div>",
            unsafe_allow_html=True)
        rcols[col_offset+1].markdown(
            f"<span class='type-badge type-{rtype.lower().replace(' ','-')}'>{rtype}</span>",
            unsafe_allow_html=True)
        rcols[col_offset+2].markdown(f"<div class='ov-sub'>{venue}</div>", unsafe_allow_html=True)
        rcols[col_offset+3].markdown(f"<div class='ov-sub'>{idx}</div>", unsafe_allow_html=True)
        rcols[col_offset+4].markdown(status_badge(e.get("status", "")), unsafe_allow_html=True)
        rcols[col_offset+5].markdown(f"<span class='ov-chip'>{disp_date}</span>", unsafe_allow_html=True)
        if doc:
            rcols[col_offset+6].markdown(
                f"<a href='{doc}' target='_blank' style='font-size:1.1rem;' title='Download Document'>&#11015;&#65039;</a>",
                unsafe_allow_html=True)
        else:
            if rcols[col_offset+6].button("⬆️", key=f"dash_up_{eid}", help="Upload Document", use_container_width=True):
                render_upload_dialog(eid, title, e.get("faculty_id"))

        # Edit toggle
        if rcols[col_offset+7].button("✏️", key=f"ov_eb_{eid}", help="Edit", use_container_width=True):
            cur = st.session_state.get(f"ov_ie_{eid}", False)
            st.session_state[f"ov_ie_{eid}"] = not cur
            st.session_state.pop(f"ov_id_{eid}", None)

        # Delete toggle
        if rcols[col_offset+8].button("🗑️", key=f"ov_db_{eid}", help="Delete", use_container_width=True):
            cur = st.session_state.get(f"ov_id_{eid}", False)
            st.session_state[f"ov_id_{eid}"] = not cur
            st.session_state.pop(f"ov_ie_{eid}", None)

        # Inline Edit panel
        if st.session_state.get(f"ov_ie_{eid}"):
            st.markdown("<div class='ov-edit-panel'>", unsafe_allow_html=True)
            _edit_form(e)
            st.markdown("</div>", unsafe_allow_html=True)

        # Inline Delete confirmation
        if st.session_state.get(f"ov_id_{eid}"):
            st.markdown("<div class='ov-del-panel'>", unsafe_allow_html=True)
            st.warning(f"⚠️ Delete **\"{title[:45]}\"** permanently?")
            da, db, _ = st.columns([1, 1, 5])
            with da:
                if st.button("✅ Yes", key=f"ov_dyes_{eid}", type="primary"):
                    if delete_research_entry(eid):
                        st.session_state.pop(f"ov_id_{eid}", None)
                        st.rerun()
            with db:
                if st.button("❌ Cancel", key=f"ov_dno_{eid}"):
                    st.session_state.pop(f"ov_id_{eid}", None)
                    st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        if i < len(entries) - 1:
            st.markdown("<hr style='margin:4px 0;border-color:#E2E8F0;opacity:1;'>",
                        unsafe_allow_html=True)


# ── ADD FORM ─────────────────────────────────────────────
def _venue_label(rtype: str) -> tuple[str, str]:
    """Return (field label, placeholder) based on research type."""
    if rtype == "Journal":
        return "📓 Journal Name", "e.g. IEEE Transactions, Springer Nature, Elsevier ESWA"
    elif rtype == "Conference":
        return "🎙️ Conference Name", "e.g. IEEE ICML, NeurIPS, CVPR"
    elif rtype == "Book":
        return "📖 Publisher Name", "e.g. Springer, O'Reilly, CRC Press"
    elif rtype == "Patent":
        return "🏛️ Patent Office", "e.g. Indian Patent Office, USPTO, EPO"
    else:  # Research Proposal
        return "🏛️ Funding Body", "e.g. DST, SERB, AICTE, DBT"


def _add_form(faculty_id, profile):
    # ── AI Upload Section ───────────────────────────────
    with st.expander("🤖 AI Document Upload (Auto-fill Metadata)", expanded=True):
        uploaded_file = st.file_uploader(
            "Upload PDF/DOCX to automatically extract details",
            type=["pdf", "docx", "txt"]
        )

        if uploaded_file and st.button("Extract Metadata with AI ✨", use_container_width=True):
            with st.spinner("Analyzing document…"):
                file_bytes = uploaded_file.read()
                metadata   = process_document(file_bytes, uploaded_file.name)

                # ── Duplicate check before upload ──────────────
                extracted_title = metadata.get("title", "")
                duplicate = False
                if extracted_title:
                    existing = fetch_my_entries(faculty_id)
                    clean_title = sanitize_text(extracted_title).strip().lower()
                    duplicate = any(
                        e.get("title", "").strip().lower() == clean_title
                        for e in existing
                    )

                if duplicate:
                    st.error(
                        "🚫 **Duplicate Document Detected!**  \n"
                        f"You have already submitted an entry with the title: *{extracted_title}*.  \n"
                        "Upload and AI extraction aborted."
                    )
                else:
                    # Upload to Supabase Storage
                    doc_url = upload_document(file_bytes, uploaded_file.name, faculty_id)

                    st.session_state["extracted_meta"] = metadata
                    if doc_url:
                        st.session_state["extracted_url"] = doc_url
                        st.session_state["doc_uploaded"]  = True

                    # ✅ Document upload success banner
                    st.success(
                        f"✅ **Document uploaded & metadata extracted successfully!**  \n"
                        f"📄 `{uploaded_file.name}` has been stored. "
                        f"Please review the auto-filled fields below before submitting."
                    )

        # Extraction confidence display
        if "extracted_meta" in st.session_state:
            conf = st.session_state["extracted_meta"].get("confidence", {})
            if conf:
                st.markdown("##### 🔍 Extraction Confidence")
                cols = st.columns(min(len(conf), 4))
                for i, (k, v) in enumerate(
                    {k: v for k, v in conf.items() if v > 0 and not k.startswith("_")}.items()
                ):
                    with cols[i % 4]:
                        st.metric(k.replace("_", " ").title(), f"{int(v * 100)}%")

    st.markdown("---")

    # Pre-fill from AI extraction
    meta    = st.session_state.get("extracted_meta", {})
    doc_url = st.session_state.get("extracted_url", None)

    # Auto-detect research type from extraction
    r_type_val = meta.get("research_type", RESEARCH_TYPES[0])
    r_type_idx = RESEARCH_TYPES.index(r_type_val) if r_type_val in RESEARCH_TYPES else 0
    auto_detected = bool(meta.get("research_type"))

    with st.form("add_entry_form", clear_on_submit=False):
        c1, c2 = st.columns(2)

        with c1:
            title = st.text_input(
                "📌 Title *",
                value=meta.get("title", ""),
                placeholder="Full title of the work"
            )

            # Type with auto-detected badge
            type_label = "📂 Type *"
            if auto_detected:
                type_label += f"  ✨ Auto-detected: **{r_type_val}**"
            rtype = st.selectbox(
                "📂 Research Type *",
                RESEARCH_TYPES,
                index=r_type_idx,
                help="Auto-detected from your document. Change if incorrect."
            )
            if auto_detected:
                st.caption(f"✨ AI detected: **{r_type_val}** — change above if incorrect")

            # Context-aware venue field (changes based on Type)
            venue_label, venue_placeholder = _venue_label(rtype)
            venue = st.text_input(
                venue_label,
                value=meta.get("journal_or_patent_office", ""),
                placeholder=venue_placeholder,
            )

            authors_names = st.text_input(
                "👥 Author Names",
                value=meta.get("authors", ""),
                placeholder="e.g. Smith J., Doe A."
            )
            authors_emails = st.text_input(
                "📧 Co-Author Gmail IDs",
                value=meta.get("author_emails", ""),
                placeholder="e.g. alice@gmail.com, bob@gmail.com"
            )
            doi = st.text_input("🔗 DOI / URL", value=meta.get("doi", ""))

        with c2:
            idx_val = meta.get("indexing", "")
            idx_idx = ([""] + INDEXING_OPTIONS).index(idx_val) \
                      if idx_val in ([""] + INDEXING_OPTIONS) else 0
            indexing      = st.selectbox("🔖 Indexing", [""] + INDEXING_OPTIONS, index=idx_idx)
            impact_factor = st.number_input("📈 Impact Factor", 0.0, step=0.001, format="%.3f")
            status        = st.selectbox("📊 Status *", _status_opts(rtype))
            
            # Pre-fill date from extraction if available
            default_date = date.today()
            if meta.get("year"):
                try:
                    default_date = date(int(meta.get("year")), int(meta.get("month") or 1), 1)
                except (ValueError, TypeError):
                    pass
            sub_date      = st.date_input("📅 Date", value=default_date)
            is_nba        = st.checkbox("✅ Include in NBA Report", value=True)

        # Type-specific extra fields
        funding_agency = funding_amount = patent_number = None
        if rtype == "Research Proposal":
            pa, pb = st.columns(2)
            with pa: funding_agency = st.text_input("🏛️ Funding Agency")
            with pb: funding_amount = st.number_input("💰 Funding Amount (₹)", 0.0, step=1000.0)
        if rtype == "Patent":
            patent_number = st.text_input("📜 Patent Number")

        notes = st.text_area(
            "📝 Abstract",
            value=meta.get("abstract", ""),
            height=70
        )
        btn = st.form_submit_button("🚀 Submit Entry", use_container_width=True, type="primary")

    if btn:
        a_n = sanitize_text(authors_names).strip()
        a_e = sanitize_text(authors_emails).strip()
        if a_n and a_e:
            combined_authors = f"{a_n} <{a_e}>"
        elif a_e:
            combined_authors = f"<{a_e}>"
        else:
            combined_authors = a_n

        data = {
            "faculty_id":              faculty_id,
            "title":                   sanitize_text(title),
            "research_type":           rtype,
            "journal_or_patent_office": sanitize_text(venue),
            "authors":                 combined_authors or None,
            "doi":                     sanitize_text(doi) or None,
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
            "notes":                   sanitize_text(notes) or None,
            "is_nba_relevant":         is_nba,
            "document_url":            doc_url,
            "extracted_metadata":      meta if meta else None,
            "extraction_confidence":   meta.get("confidence") if meta else None,
            "ai_processed":            bool(meta),
        }

        # ── Step 1: Field validation ───────────────────
        ok, msg = validate_research_entry(data)
        if not ok:
            st.error(f"❌ {msg}")
            st.stop()

        # ── Step 2: Duplicate entry check ─────────────
        existing   = fetch_my_entries(faculty_id)
        clean_title = sanitize_text(title).strip().lower()
        duplicate  = any(
            e.get("title", "").strip().lower() == clean_title
            for e in existing
        )
        if duplicate:
            st.error(
                "🚫 **Duplicate Entry Blocked!**  \n"
                "You have already submitted a research entry with this exact title.  \n"
                "Please use a unique title or edit the existing entry instead."
            )
            st.stop()

        # ── Step 3: Save ───────────────────────────────
        with st.spinner("Saving your entry…"):
            if add_research_entry(data):
                # ── Step 4: Semester limit check ─────────────
                all_entries = fetch_my_entries(faculty_id)
                m, y = data.get("month", 0), data.get("year", 0)
                
                if m in [8, 9, 10, 11, 12, 1, 2]:
                    sem_range = [8, 9, 10, 11, 12, 1, 2]
                    sem_label = "Aug to Feb"
                else:
                    sem_range = [3, 4, 5, 6, 7, 8, 9]
                    sem_label = "March to September"
                
                sem_entries = [e for e in all_entries if e.get("month") in sem_range and e.get("year") == y]
                j_count = sum(1 for e in sem_entries if e["research_type"] == "Journal")
                c_count = sum(1 for e in sem_entries if e["research_type"] == "Conference")
                
                limit_msg = ""
                if j_count > 3:
                    limit_msg += f"⚠️ **Journal limit exceeded!** You have submitted {j_count} journals in the {sem_label} semester.  \n"
                if c_count > 3:
                    limit_msg += f"⚠️ **Conference limit exceeded!** You have submitted {c_count} conferences in the {sem_label} semester.  \n"
                
                if limit_msg:
                    limit_msg += "💡 **Suggestion:** We recommend improvising in other research fields such as **Patents** or **Research Proposals** to maintain a balanced portfolio."
                    st.session_state["limit_warning"] = limit_msg

                # Clear session state
                for key in ("extracted_meta", "extracted_url", "doc_uploaded"):
                    st.session_state.pop(key, None)

                st.success(
                    "✅ **Entry submitted successfully!**  \n"
                    f"Your **{rtype}** — *\"{sanitize_text(title)[:80]}\"* — "
                    "has been saved and is now visible in My Entries."
                )
                st.balloons()
                st.rerun()


# ── EDIT FORM ─────────────────────────────────────────────
def _edit_form(entry):
    eid   = entry["id"]
    rtype = entry.get("research_type", RESEARCH_TYPES[0])
    with st.form(f"edit_{eid}"):
        title = st.text_input("Title", value=entry.get("title", ""))
        rtype_edit = st.selectbox(
            "Research Type", RESEARCH_TYPES,
            index=RESEARCH_TYPES.index(rtype) if rtype in RESEARCH_TYPES else 0
        )
        
        journal = st.text_input(
            "📓 Venue / Office / Funding Body",
            value=entry.get("journal_or_patent_office", "") or "",
            help="Enter Journal Name, Conference Name, Patent Office, or Funding Agency"
        )
        
        doi = st.text_input("🔗 DOI / URL", value=entry.get("doi", "") or "")

        import re
        existing_authors = entry.get("authors", "") or ""
        names_match = re.match(r'^(.*?)(?:\s*<(.*)>)?$', existing_authors)
        if names_match:
            a_names = names_match.group(1).strip()
            a_emails = names_match.group(2) or ""
        else:
            a_names = existing_authors
            a_emails = ""

        authors_names = st.text_input("👥 Author Names", value=a_names)
        authors_emails = st.text_input("📧 Co-Author Gmail IDs", value=a_emails)

        c1, c2 = st.columns(2)
        with c1:
            indexing = st.selectbox(
                "🔖 Indexing", [""] + INDEXING_OPTIONS,
                index=([""] + INDEXING_OPTIONS).index(entry.get("indexing") or "")
            )
        with c2:
            impact = st.number_input(
                "📈 Impact Factor", 0.0, step=0.001,
                value=float(entry.get("impact_factor") or 0), format="%.3f"
            )

        c3, c4 = st.columns(2)
        with c3:
            all_statuses = ["Published", "Accepted", "Under Review", "Draft", "Granted", "Filed", "Approved", "Submitted", "Rejected"]
            cur = entry.get("status", "Draft")
            status = st.selectbox("📊 Status", all_statuses, index=all_statuses.index(cur) if cur in all_statuses else 3)
        with c4:
            sub_val = entry.get("submission_date")
            if sub_val and len(sub_val) >= 10:
                parsed_date = date.fromisoformat(sub_val[:10])
            elif entry.get("year"):
                try:
                    parsed_date = date(int(entry.get("year")), int(entry.get("month") or 1), 1)
                except (ValueError, TypeError):
                    parsed_date = date.today()
            else:
                parsed_date = date.today()
            sub_date = st.date_input("📅 Date", value=parsed_date)

        patent_number = st.text_input("📜 Patent Number (if Patent)", value=entry.get("patent_number", "") or "")
        
        pa, pb = st.columns(2)
        with pa:
            funding_agency = st.text_input("🏛️ Funding Agency (if Proposal)", value=entry.get("funding_agency", "") or "")
        with pb:
            funding_amount = st.number_input("💰 Funding Amount (₹)", 0.0, step=1000.0, value=float(entry.get("funding_amount") or 0))

        is_nba = st.checkbox("✅ Include in NBA Report", value=entry.get("is_nba_relevant", True))
        notes  = st.text_area("📝 Abstract", value=entry.get("notes", "") or "", height=68)

        if st.form_submit_button("💾 Save Changes", use_container_width=True):
            edit_a_n = sanitize_text(authors_names).strip()
            edit_a_e = sanitize_text(authors_emails).strip()
            if edit_a_n and edit_a_e:
                combined_edit_authors = f"{edit_a_n} <{edit_a_e}>"
            elif edit_a_e:
                combined_edit_authors = f"<{edit_a_e}>"
            else:
                combined_edit_authors = edit_a_n

            if update_research_entry(eid, {
                "title":                    sanitize_text(title),
                "research_type":            rtype_edit,
                "journal_or_patent_office": sanitize_text(journal),
                "authors":                  combined_edit_authors or None,
                "doi":                      sanitize_text(doi) or None,
                "indexing":                 indexing or None,
                "impact_factor":            float(impact) if impact else None,
                "status":                   status,
                "submission_date":          sub_date.isoformat(),
                "month":                    sub_date.month,
                "year":                     sub_date.year,
                "patent_number":            sanitize_text(patent_number) if patent_number else None,
                "funding_agency":           sanitize_text(funding_agency) if funding_agency else None,
                "funding_amount":           float(funding_amount) if funding_amount else None,
                "is_nba_relevant":          is_nba,
                "notes":                    sanitize_text(notes) or None,
            }):
                st.session_state.pop(f"ov_ie_{eid}", None)
                st.session_state.pop(f"ov_id_{eid}", None)
                st.success("✅ Entry updated successfully!")
                st.rerun()


