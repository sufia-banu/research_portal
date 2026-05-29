"""
pages/nba_module.py - NBA Accreditation reporting module
"""
from __future__ import annotations
import streamlit as st
import pandas as pd
from datetime import datetime

from database.queries import fetch_all_entries, fetch_departments
from services.auth_service import get_current_profile, get_current_role
from services.export_service import entries_to_dataframe, to_csv_bytes, to_excel_bytes
from components.ui import page_header, section_header, metric_card
from utils.helpers import build_academic_year_list
from config import RESEARCH_TYPES, INSTITUTION_NAME


def render_nba_module():
    profile = get_current_profile()
    role = get_current_role()

    page_header("NBA Accreditation Module", "", "")

    # ── Filters ─────────────────────────────────────────────


    fc1, fc2, fc3 = st.columns(3)
    with fc1:
        academic_years = build_academic_year_list(2018)
        ay_options = ["All Academic Years"] + academic_years
        selected_ay = st.selectbox("📅 Academic Year", ay_options, index=0, key="nba_ay")
    with fc2:
        depts = fetch_departments()
        dept_options = ["All Departments"] + [d["department_name"] for d in depts]
        if role == "hod":
            dept_options = [profile.get("department", "")]
        selected_dept = st.selectbox("🏛️ Department", dept_options, key="nba_dept")
    with fc3:
        selected_type = st.selectbox("📂 Research Type", ["All"] + RESEARCH_TYPES, key="nba_type")

    # ── Fetch & Filter ───────────────────────────────────────
    filters = {}
    if selected_ay != "All Academic Years":
        filters["academic_year"] = selected_ay
    if selected_dept != "All Departments":
        filters["department"] = selected_dept
    if selected_type != "All":
        filters["research_type"] = selected_type
    
    # Restrict visibility for faculty to only their own entries
    if role == "faculty":
        filters["faculty_id"] = profile.get("id")

    entries = fetch_all_entries(filters)
    # Only NBA-relevant
    entries = [e for e in entries if e.get("is_nba_relevant", True)]

    st.markdown("<br>", unsafe_allow_html=True)

    # ── KPI Metrics ─────────────────────────────────────────
    section_header(f"Key Metrics — AY {selected_ay}", "📊")
    total_jour = sum(1 for e in entries if e["research_type"] == "Journal")
    total_conf = sum(1 for e in entries if e["research_type"] == "Conference")
    total_pat = sum(1 for e in entries if e["research_type"] == "Patent")
    total_prop = sum(1 for e in entries if e["research_type"] == "Research Proposal")
    total_funded = sum(1 for e in entries if e.get("funding_amount") and float(e.get("funding_amount") or 0) > 0)
    scopus_count = sum(1 for e in entries if e.get("indexing") in ("Scopus", "SCI", "Web of Science"))
    total_funding = sum(float(e.get("funding_amount") or 0) for e in entries)

    m1, m2, m3, m4, m5, m6, m7 = st.columns(7)
    with m1: metric_card("Journals", total_jour, "📓", color="#3498DB")
    with m2: metric_card("Conferences", total_conf, "🎙️", color="#9B59B6")
    with m3: metric_card("Patents", total_pat, "💡", color="#F18F01")
    with m4: metric_card("Research Proposals", total_prop, "📋", color="#E74C3C")
    with m5: metric_card("Funded Projects", total_funded, "💰", color="#2ECC71")
    with m6: metric_card("Scopus/SCI", scopus_count, "🔖", color="#f39c12")
    with m7: metric_card("Funding (₹)", f"{total_funding:,.0f}", "🏦", color="#1ABC9C")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Tabbed Report Sections ───────────────────────────────
    # ── Tabbed Report Sections ───────────────────────────────
    tab_jour, tab_conf, tab_pat, tab_prop, tab_summary, tab_export = st.tabs([
        "📓 Journals", "🎙️ Conferences", "💡 Patents", "📋 Research Proposals", "📑 Summary", "⬇ Export"
    ])

    # ── Journals ─────────────────────────────────────────
    with tab_jour:
        jours = [e for e in entries if e["research_type"] == "Journal"]
        _render_nba_table(jours, "Journals", show_faculty=True, show_indexing=True)

    # ── Conferences ───────────────────────────────────────
    with tab_conf:
        confs = [e for e in entries if e["research_type"] == "Conference"]
        _render_nba_table(confs, "Conferences", show_faculty=True, show_indexing=True)

    # ── Patents ──────────────────────────────────────────────
    with tab_pat:
        pats = [e for e in entries if e["research_type"] == "Patent"]
        _render_nba_table(pats, "Patents", show_faculty=True, show_patent=True)

    # ── Proposals ────────────────────────────────────────────
    with tab_prop:
        props = [e for e in entries if e["research_type"] == "Research Proposal"]
        _render_nba_table(props, "Research Proposals", show_faculty=True, show_funding=True)

    # ── Summary Report ───────────────────────────────────────
    with tab_summary:
        _render_summary_report(entries, selected_ay, selected_dept)

    # ── Export ────────────────────────────────────────────────
    with tab_export:
        section_header("Export NBA Evidence Package", "⬇")
        df_all = entries_to_dataframe(entries)

        st.markdown(f"**{len(entries)} NBA-relevant records for AY {selected_ay}**")

        xc1, xc2 = st.columns(2)
        with xc1:
            st.download_button(
                f"⬇ Download All (CSV)",
                to_csv_bytes(df_all),
                f"NBA_Report_{selected_ay.replace('-','_')}.csv",
                "text/csv",
                use_container_width=True
            )
        with xc2:
            st.download_button(
                f"⬇ Download All (Excel)",
                to_excel_bytes(df_all, f"AY {selected_ay}"),
                f"NBA_Report_{selected_ay.replace('-','_')}.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

        # Per-type downloads
        st.markdown("---")
        # Per-type downloads
        st.markdown("---")
        st.markdown("**Download by Category:**")
        ex1, ex2, ex3, ex4 = st.columns(4)
        with ex1:
            jour_df = entries_to_dataframe([e for e in entries if e["research_type"] == "Journal"])
            st.download_button("📓 Journals (CSV)", to_csv_bytes(jour_df),
                               f"NBA_Journals_{selected_ay.replace('-','_')}.csv",
                               "text/csv", use_container_width=True)
        with ex2:
            conf_df = entries_to_dataframe([e for e in entries if e["research_type"] == "Conference"])
            st.download_button("🎙️ Conferences (CSV)", to_csv_bytes(conf_df),
                               f"NBA_Conferences_{selected_ay.replace('-','_')}.csv",
                               "text/csv", use_container_width=True)
        with ex3:
            pats_df = entries_to_dataframe([e for e in entries if e["research_type"] == "Patent"])
            st.download_button("💡 Patents (CSV)", to_csv_bytes(pats_df),
                               f"NBA_Patents_{selected_ay.replace('-','_')}.csv",
                               "text/csv", use_container_width=True)
        with ex4:
            props_df = entries_to_dataframe([e for e in entries if e["research_type"] == "Research Proposal"])
            st.download_button("📋 Proposals (CSV)", to_csv_bytes(props_df),
                               f"NBA_Proposals_{selected_ay.replace('-','_')}.csv",
                               "text/csv", use_container_width=True)

        with st.expander("📋 Preview Report Data"):
            st.dataframe(df_all, use_container_width=True, hide_index=True)


# ════════════════════════════════════════════════════════════
# HELPERS
# ════════════════════════════════════════════════════════════

def _render_nba_table(entries: list[dict], label: str,
                       show_faculty: bool = False,
                       show_indexing: bool = False,
                       show_patent: bool = False,
                       show_funding: bool = False):
    if not entries:
        st.info(f"No {label} found for the selected filters.")
        return

    rows = []
    for i, e in enumerate(entries, 1):
        fac = e.get("profiles", {})
        fname = fac.get("full_name", "—") if isinstance(fac, dict) else "—"
        row = {
            "S.No": i,
            "Title": e.get("title", ""),
            "Department": e.get("department", ""),
            "Status": e.get("status", ""),
            "Year": e.get("year", ""),
        }
        if show_faculty:
            row["Faculty"] = fname
        if show_indexing:
            row["Journal"] = e.get("journal_or_patent_office", "") or "—"
            row["Indexing"] = e.get("indexing", "") or "—"
        if show_patent:
            row["Patent Office"] = e.get("journal_or_patent_office", "") or "—"
            row["Patent No."] = e.get("patent_number", "") or "—"
        if show_funding:
            row["Funding Agency"] = e.get("funding_agency", "") or "—"
            row["Amount (₹)"] = e.get("funding_amount", "") or "—"
        rows.append(row)

    df = pd.DataFrame(rows)
    st.markdown(f"**{len(entries)} {label}**")
    st.dataframe(df, use_container_width=True, hide_index=True)


def _render_summary_report(entries: list[dict], ay: str, dept: str):
    institution = INSTITUTION_NAME
    generated_on = datetime.now().strftime("%B %d, %Y %I:%M %p")

    # Simple text title
    st.markdown("### 📑 Research Summary Report")

    # Department-wise breakdown
    dept_breakdown = {}
    for e in entries:
        d = e.get("department", "Unknown")
        rtype = e.get("research_type", "Unknown")
        if d not in dept_breakdown:
            dept_breakdown[d] = {"Journal": 0, "Conference": 0, "Patent": 0, "Research Proposal": 0}
        dept_breakdown[d][rtype] = dept_breakdown[d].get(rtype, 0) + 1

    section_header("Department-wise Summary", "🏛️")
    if dept_breakdown:
        summary_rows = []
        for d, v in sorted(dept_breakdown.items()):
            summary_rows.append({
                "Department": d,
                "Journals": v.get("Journal", 0),
                "Conferences": v.get("Conference", 0),
                "Patents": v.get("Patent", 0),
                "Proposals": v.get("Research Proposal", 0),
                "Total": sum(v.values()),
            })
        df_summ = pd.DataFrame(summary_rows)
        # Add total row
        total_row = pd.DataFrame([{
            "Department": "TOTAL",
            "Journals": df_summ["Journals"].sum(),
            "Conferences": df_summ["Conferences"].sum(),
            "Patents": df_summ["Patents"].sum(),
            "Proposals": df_summ["Proposals"].sum(),
            "Total": df_summ["Total"].sum(),
        }])
        df_final = pd.concat([df_summ, total_row], ignore_index=True)
        st.dataframe(df_final, use_container_width=True, hide_index=True)

    # Indexing summary
    section_header("Indexing Summary (Journals & Conferences)", "🔖")
    pub_entries = [e for e in entries if e["research_type"] in ("Journal", "Conference")]
    index_counts = {}
    for e in pub_entries:
        idx = e.get("indexing") or "Not Indexed"
        index_counts[idx] = index_counts.get(idx, 0) + 1
    if index_counts:
        idx_df = pd.DataFrame(
            [(k, v) for k, v in sorted(index_counts.items(), key=lambda x: x[1], reverse=True)],
            columns=["Indexing", "Count"]
        )
        st.dataframe(idx_df, use_container_width=True, hide_index=True)

    st.markdown("""
    <p style='color:#7F8C8D;font-size:0.78rem;margin-top:24px;text-align:center;'>
    This report is auto-generated from the Research Information Collection Portal.<br>
    Data is sourced from faculty submissions and is subject to verification.
    </p>
    """, unsafe_allow_html=True)
