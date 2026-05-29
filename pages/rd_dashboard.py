"""
pages/rd_dashboard.py - Enhanced R&D Coordinator Dashboard
"""
from __future__ import annotations
import streamlit as st
import pandas as pd

from database.queries import (
    fetch_all_entries, fetch_departments,
    get_institution_stats, fetch_active_reminders,
    fetch_department_entries, fetch_all_profiles
)
from services.export_service import entries_to_dataframe, to_csv_bytes, to_excel_bytes, to_pdf_bytes
from components.ui import metric_card, page_header, section_header, reminder_card, status_badge, render_faculty_profile_card
from utils.charts import (
    pie_chart, department_comparison_chart,
    horizontal_bar, stacked_bar,
)
from utils.helpers import get_years_list
from config import RESEARCH_TYPES


def render_rd_dashboard():
    page_header("R&D Coordinator Dashboard",
                "Institution-wide Research Intelligence & KPI Overview", "")

    reminders = fetch_active_reminders("rd_coordinator")
    if reminders:
        with st.expander(f"🔔 {len(reminders)} Reminder(s)"):
            for r in reminders: reminder_card(r)

    stats = get_institution_stats()
    c1,c2,c3,c4,c5,c6,c7 = st.columns(7)
    with c1: metric_card("Total",       stats["total"],              "📄", color="#2E86AB")
    with c2: metric_card("Journals",    stats["journals"],           "📓", color="#3498DB")
    with c3: metric_card("Conferences", stats["conferences"],        "🎙️", color="#9B59B6")
    with c4: metric_card("Patents",     stats["patents"],            "💡", color="#F18F01")
    with c5: metric_card("Research Proposals",   stats["proposals"],          "📋", color="#E74C3C")
    with c6: metric_card("Researchers", stats["active_researchers"], "👥", color="#2ECC71")
    with c7: metric_card("Departments", stats["total_departments"],  "🏛️", color="#00BCD4")

    st.markdown("<br>", unsafe_allow_html=True)
    tab_ov, tab_dept, tab_fac, tab_entries, tab_props, tab_export = st.tabs(
        ["📊 Overview", "🏛️ Departments", "👥 Faculty Profiles", "📋 Entries", "📋 Research Proposals", "⬇ Export"])

    # ── OVERVIEW ─────────────────────────────────────────
    with tab_ov:
        all_e = fetch_all_entries()
        if not all_e:
            st.info("No institutional data yet.")
        else:
            r1, r2 = st.columns(2)
            with r1:
                st.plotly_chart(pie_chart(
                    ["Journal","Conference","Patent","Research Proposal"],
                    [stats["journals"],stats["conferences"],stats["patents"],stats["proposals"]],
                    "Institution Research Mix"), use_container_width=True)
            with r2:
                sc = {}
                for e in all_e:
                    s=e.get("status","Unknown"); sc[s]=sc.get(s,0)+1
                st.plotly_chart(pie_chart(list(sc.keys()),list(sc.values()),
                                          "Status Distribution"), use_container_width=True)



            # Indexing breakdown
            section_header("Journal & Conference Indexing Analysis","🔖")
            pubs = [e for e in all_e if e["research_type"] in ("Journal", "Conference") and e.get("indexing")]
            if pubs:
                idx = {}
                for e in pubs: i=e["indexing"]; idx[i]=idx.get(i,0)+1
                sorted_idx = sorted(idx.items(), key=lambda x:x[1], reverse=True)
                names,vals = zip(*sorted_idx)
                st.plotly_chart(horizontal_bar(list(names),list(vals),
                                               "Indexed Output by Type"),
                                use_container_width=True)

    # ── DEPARTMENTS ───────────────────────────────────────
    with tab_dept:
        depts = fetch_departments()
        dept_data = {}
        for d in depts:
            name = d["department_name"]
            entries = fetch_department_entries(name)
            dept_data[name] = {
                "journals":     sum(1 for e in entries if e["research_type"]=="Journal"),
                "conferences":  sum(1 for e in entries if e["research_type"]=="Conference"),
                "patents":      sum(1 for e in entries if e["research_type"]=="Patent"),
                "proposals":    sum(1 for e in entries if e["research_type"]=="Research Proposal"),
                "total":        len(entries),
            }

        active = dept_data  # Show all departments to match the top metric card count
        if not active:
            st.info("No department data yet.")
        else:
            # Summary table
            section_header("Department Performance Leaderboard","🏆")
            df_dept = pd.DataFrame([
                {"Department": d, "Journals": v["journals"], "Conferences": v["conferences"],
                 "Patents": v["patents"], "Proposals": v["proposals"], "Total": v["total"]}
                for d,v in sorted(active.items(), key=lambda x:x[1]["total"], reverse=True)
            ])
            st.dataframe(df_dept, use_container_width=True, hide_index=True,
                         column_config={
                             "Total": st.column_config.ProgressColumn(
                                 "Total", max_value=int(df_dept["Total"].max() or 1))
                         })

            st.plotly_chart(department_comparison_chart(active,
                            "Department-wise Research Comparison"),
                            use_container_width=True)

            # Stacked bar for dept total by type
            dept_names = [d[:22] for d in df_dept["Department"]]
            st.plotly_chart(stacked_bar(
                dept_names,
                {"Journals": df_dept["Journals"].tolist(),
                 "Conferences": df_dept["Conferences"].tolist(),
                 "Patents":       df_dept["Patents"].tolist(),
                 "Proposals":     df_dept["Proposals"].tolist()},
                "Research Output by Department (Stacked)"), use_container_width=True)

    # ── FACULTY PROFILES ─────────────────────────────────
    with tab_fac:
        section_header("Institutional Faculty Directory", "👥")
        fac1, fac2 = st.columns([1, 2])
        with fac1:
            f_dept_filter = st.selectbox("Filter by Department", ["All"] + [d["department_name"] for d in fetch_departments()], key="rd_fac_dept")
        with fac2:
            f_search = st.text_input("🔍 Search by Name or Email", key="rd_fac_search")
            
        all_profs = fetch_all_profiles()
        
        # Apply filters
        filtered_profs = all_profs
        if f_dept_filter != "All":
            filtered_profs = [p for p in filtered_profs if p.get("department") == f_dept_filter]
        if f_search:
            s_q = f_search.lower()
            filtered_profs = [p for p in filtered_profs if s_q in p.get("full_name", "").lower() or s_q in p.get("email", "").lower()]
            
        st.markdown(f"**Showing {len(filtered_profs)} Faculty Members**")
        
        if not filtered_profs:
            st.info("No faculty match the selected filters.")
        else:
            all_entries = fetch_all_entries()
            for p in filtered_profs:
                if p.get("role") in ["faculty", "hod", "rd_coordinator"]:
                    fid = p["id"]
                    fe  = [e for e in all_entries if e["faculty_id"] == fid]
                    metrics = {
                        "Journals": sum(1 for e in fe if e["research_type"]=="Journal"),
                        "Conferences": sum(1 for e in fe if e["research_type"]=="Conference"),
                        "Patents": sum(1 for e in fe if e["research_type"]=="Patent"),
                        "Proposals": sum(1 for e in fe if e["research_type"]=="Research Proposal")
                    }
                    render_faculty_profile_card(p, metrics)

    # ── ENTRIES ──────────────────────────────────────────
    with tab_entries:
        fc1, fc2, fc3, fc4 = st.columns(4)
        with fc1: f_dept = st.selectbox("Department", ["All"] + [d["department_name"] for d in fetch_departments()], key="rd_f_dept")
        with fc2: f_type = st.selectbox("Type", ["All"] + RESEARCH_TYPES, key="rd_f_type")
        with fc3: f_year = st.selectbox("Year", ["All"] + [str(y) for y in get_years_list()], key="rd_f_year")
        with fc4: f_srch = st.text_input("🔍 Search", key="rd_f_srch")

        filters = {}
        if f_dept != "All": filters["department"] = f_dept
        if f_type != "All": filters["research_type"] = f_type
        if f_year != "All": filters["year"] = int(f_year)
        entries = fetch_all_entries(filters)
        if f_srch:
            entries = [e for e in entries if f_srch.lower() in e.get("title", "").lower()]

        st.markdown(f"**{len(entries)} record(s)**")
        if entries:
            _render_table(entries, show_faculty=True)
    # ── PROPOSALS ─────────────────────────────────────────
    with tab_props:
        section_header("Research Proposal Pipeline","📋")
        props = fetch_all_entries({"research_type":"Research Proposal"})
        if not props:
            st.info("No proposals found.")
        else:
            ps = {}
            for e in props:
                s=e.get("status","Unknown"); ps[s]=ps.get(s,0)+1
            p1, p2 = st.columns([1,2])
            with p1:
                for s,c in sorted(ps.items(), key=lambda x:x[1], reverse=True):
                    metric_card(s,c,"📋")
            with p2:
                st.plotly_chart(pie_chart(list(ps.keys()),list(ps.values()),
                                          "Proposal Status Pipeline"),
                                use_container_width=True)

            funded = [e for e in props if float(e.get("funding_amount") or 0)>0]
            if funded:
                section_header("Funded Projects","💰")
                fr = []
                for e in funded:
                    fac=e.get("profiles",{}); fname=fac.get("full_name","—") if isinstance(fac,dict) else "—"
                    fr.append({"Title":e.get("title",""),"Dept":e.get("department",""),
                               "Faculty":fname,"Agency":e.get("funding_agency","—"),
                               "Amount (₹)":e.get("funding_amount",0),"Status":e.get("status","")})
                st.dataframe(pd.DataFrame(fr), use_container_width=True, hide_index=True)

    # ── EXPORT ───────────────────────────────────────────
    with tab_export:
        section_header("Export Institutional Data","⬇")
        ef1,ef2,ef3 = st.columns(3)
        with ef1: ed = st.selectbox("Dept",["All"]+[d["department_name"] for d in fetch_departments()],key="rd_ed")
        with ef2: et = st.selectbox("Type",["All"]+RESEARCH_TYPES,key="rd_et")
        with ef3: ey = st.selectbox("Year",["All"]+[str(y) for y in get_years_list()],key="rd_ey")

        ef = {}
        if ed!="All": ef["department"]=ed
        if et!="All": ef["research_type"]=et
        if ey!="All": ef["year"]=int(ey)
        ex_e = fetch_all_entries(ef)
        df_ex = entries_to_dataframe(ex_e)
        st.markdown(f"**{len(ex_e)} records selected**")

        # Build filter summary string for PDF header
        filter_parts = []
        if ed != "All": filter_parts.append(f"Dept: {ed}")
        if et != "All": filter_parts.append(f"Type: {et}")
        if ey != "All": filter_parts.append(f"Year: {ey}")
        filters_summary = " | ".join(filter_parts) if filter_parts else "All records"

        ec1, ec2, ec3 = st.columns(3)
        with ec1:
            st.download_button("⬇ CSV", to_csv_bytes(df_ex), "institution_research.csv",
                               "text/csv", use_container_width=True)
        with ec2:
            st.download_button("⬇ Excel", to_excel_bytes(df_ex, "Research Data"),
                               "institution_research.xlsx",
                               "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                               use_container_width=True)
        with ec3:
            pdf_title = f"R&D Research Report"
            st.download_button(
                "📄 PDF Report",
                to_pdf_bytes(df_ex, title=pdf_title, filters_summary=filters_summary),
                "institution_research_report.pdf",
                "application/pdf",
                use_container_width=True,
                help="Download a formatted PDF document of the selected research data"
            )
        with st.expander("📋 Preview"):
            st.dataframe(df_ex.head(20), use_container_width=True, hide_index=True)


# ── TABLE with Download Option ─────────────────────────────────────────
def _render_table(entries, show_faculty=False):
    from datetime import date
    st.markdown("""
    <style>
    .ov-hdr{font-size:.67rem;font-weight:700;color:#64748B;text-transform:uppercase;
            letter-spacing:.07em;padding-bottom:3px;}
    .ov-title{font-size:.88rem;font-weight:600;color:#1E293B;line-height:1.3;}
    .ov-sub{font-size:.76rem;color:#475569;}
    .ov-chip{background:#F1F5F9;border-radius:20px;padding:2px 9px;
             font-size:.76rem;color:#475569;display:inline-block;}
    </style>
    """, unsafe_allow_html=True)

    # Column layout: Title | Type | Venue | Indexing | Status | Date | Doc
    CW = [3.4, 1.2, 1.8, 1.0, 1.3, 1.0, 0.5]
    hdrs = ["Title", "Type", "Journal/Office", "Indexing", "Status", "Date", "Doc"]
    if show_faculty:
        CW = [1.5] + CW
        hdrs = ["Faculty"] + hdrs

    hcols = st.columns(CW)
    for hc, hl in zip(hcols, hdrs):
        hc.markdown(f"<div class='ov-hdr'>{hl}</div>", unsafe_allow_html=True)
    st.markdown("<hr style='margin:2px 0 6px 0;border-color:#E2E8F0;'>", unsafe_allow_html=True)

    for i, e in enumerate(entries):
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
                f"<a href='{doc}' target='_blank' style='font-size:1.1rem;'>&#11015;&#65039;</a>",
                unsafe_allow_html=True)
        else:
            rcols[col_offset+6].markdown("—")

        if i < len(entries) - 1:
            st.markdown("<hr style='margin:4px 0;border-color:#E2E8F0;opacity:1;'>",
                        unsafe_allow_html=True)
