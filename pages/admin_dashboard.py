"""
pages/admin_dashboard.py - Enhanced Admin Control Center
"""
from __future__ import annotations
import streamlit as st
import pandas as pd
from datetime import datetime

from database.queries import (
    fetch_all_profiles, fetch_all_entries, fetch_departments,
    update_profile, delete_user_profile, toggle_user_status,
    add_department, delete_department, get_institution_stats,
    fetch_all_reminders, add_reminder, deactivate_reminder,
)
from services.auth_service import (
    get_current_profile, get_current_user,
    admin_create_user, admin_delete_user,
)
from services.export_service import entries_to_dataframe, to_csv_bytes, to_excel_bytes
from components.ui import metric_card, page_header, section_header, reminder_card
from utils.charts import (
    pie_chart, bar_chart, monthly_trend_chart,
    horizontal_bar, yearly_comparison,
)
from utils.validators import validate_email, validate_password
from config import ROLES, RESEARCH_TYPES
from utils.helpers import get_current_month_num, get_current_year


def render_admin_dashboard():
    page_header("Admin Control Center",
                "Full System Access · Users · Departments · Analytics", "")

    stats = get_institution_stats()
    c1,c2,c3,c4,c5,c6 = st.columns(6)
    with c1: metric_card("Total Entries",    stats["total"],              "📄","#2E86AB")
    with c2: metric_card("Total Faculty",    stats["total_faculty"],      "👥","#3498DB")
    with c3: metric_card("Departments",      stats["total_departments"],  "🏛️","#F18F01")
    with c4: metric_card("Researchers",      stats["active_researchers"], "🔬","#2ECC71")
    with c5: metric_card("Journals",         stats["journals"],           "📓","#9B59B6")
    with c6: metric_card("Conferences",      stats["conferences"],        "🎙️","#E74C3C")

    st.markdown("<br>", unsafe_allow_html=True)
    tab_users, tab_dept, tab_entries, tab_monitor, tab_reminders, tab_analytics = st.tabs([
        "👥 Users", "🏛️ Departments", "📋 Entries",
        "📡 Monitor", "🔔 Reminders", "📊 Analytics"
    ])

    # ── USERS ─────────────────────────────────────────────
    with tab_users:
        sub_view, sub_create = st.tabs(["👁 View & Manage", "➕ Create User"])

        with sub_view:
            profiles = fetch_all_profiles()
            uf1,uf2 = st.columns(2)
            with uf1: rf = st.selectbox("Filter Role",["All"]+list(ROLES.values()),key="adm_rf")
            with uf2: sf = st.text_input("🔍 Search Name/Email",key="adm_sf")

            fp = profiles
            if rf!="All":
                rk=[k for k,v in ROLES.items() if v==rf][0]
                fp=[p for p in fp if p.get("role")==rk]
            if sf:
                q=sf.lower()
                fp=[p for p in fp if q in p.get("full_name","").lower() or q in p.get("email","").lower()]

            st.markdown(f"**{len(fp)} user(s)**")
            for p in fp:
                photo = p.get('photo_url')
                avatar_html = f'<img src="{photo}" style="width:100%;height:100%;object-fit:cover;border-radius:50%;">' if photo else (p.get('full_name', 'U')[0].upper() if p.get('full_name') else 'U')
                
                ucard = f"""
                <div class="user-card" style="border-left: 4px solid {'var(--success)' if p.get('is_active',True) else 'var(--danger)'}; margin-bottom: 0;">
                    <div class="user-avatar" style="background:{'var(--primary-light)' if p.get('is_active',True) else 'var(--danger-light)'}; color:{'var(--primary)' if p.get('is_active',True) else 'var(--danger)'}; padding:0; overflow:hidden;">
                        {avatar_html}
                    </div>
                    <div class="user-info" style="flex:1;">
                        <strong style="font-size:1.05rem;">{p.get('full_name','')}</strong>
                        <span style="color:var(--text-secondary); font-size:0.85rem;">{p.get('email','')}</span>
                    </div>
                    <div class="user-role" style="text-align:right;">
                        <span style="background:var(--bg-color); padding:4px 10px; border-radius:6px; font-size:0.75rem; font-weight:700; color:var(--primary);">{p.get('role','').upper()}</span>
                        <div style="font-size:0.75rem; color:var(--text-muted); margin-top:4px;">{p.get('department','')}</div>
                    </div>
                </div>
                """
                st.markdown(ucard, unsafe_allow_html=True)
                with st.expander("✏️ Edit / Manage User"):
                    ec1,ec2 = st.columns([2,1])
                    with ec1:
                        depts=[d["department_name"] for d in fetch_departments()]
                        with st.form(f"eu_{p['id']}"):
                            nn = st.text_input("Name",value=p.get("full_name",""))
                            nr = st.selectbox("Role",list(ROLES.values()),
                                              index=list(ROLES.keys()).index(p.get("role","faculty")))
                            nd = st.selectbox("Department",depts,
                                              index=depts.index(p["department"]) if p.get("department") in depts else 0)
                            
                            st.markdown("---")
                            c_adm1, c_adm2 = st.columns(2)
                            with c_adm1:
                                n_des = st.text_input("Designation", value=p.get("designation", "") or "", key=f"des_{p['id']}")
                                n_emp = st.text_input("Employee ID", value=p.get("employee_id", "") or "", key=f"emp_{p['id']}")
                            with c_adm2:
                                n_mob = st.text_input("Mobile", value=p.get("mobile_number", "") or "", key=f"mob_{p['id']}")
                                n_orc = st.text_input("ORCID", value=p.get("orcid_id", "") or "", key=f"orc_{p['id']}")
                            
                            na = st.checkbox("Active",value=p.get("is_active",True))
                            if st.form_submit_button("💾 Save Changes"):
                                rk=[k for k,v in ROLES.items() if v==nr][0]
                                update_profile(p["id"], {
                                    "full_name": nn,
                                    "role": rk,
                                    "department": nd,
                                    "designation": n_des,
                                    "employee_id": n_emp,
                                    "mobile_number": n_mob,
                                    "orcid_id": n_orc,
                                    "is_active": na
                                })
                                st.success("Updated.")
                                st.rerun()
                    with ec2:
                        st.markdown("<br>",unsafe_allow_html=True)
                        lbl="🔴 Deactivate" if p.get("is_active",True) else "🟢 Activate"
                        if st.button(lbl,key=f"tog_{p['id']}",use_container_width=True):
                            toggle_user_status(p["id"],not p.get("is_active",True))
                            st.rerun()
                        if st.button("🗑️ Delete",key=f"du_{p['id']}",
                                     use_container_width=True,type="secondary"):
                            st.session_state[f"_cdu_{p['id']}"]=True
                        if st.session_state.get(f"_cdu_{p['id']}"):
                            st.warning("Permanently delete this user?")
                            da,db=st.columns(2)
                            with da:
                                if st.button("✅ Confirm",key=f"cdu_{p['id']}"):
                                    ok,msg=admin_delete_user(p["id"])
                                    if ok: delete_user_profile(p["id"]); st.success(msg)
                                    else:  st.error(msg)
                                    del st.session_state[f"_cdu_{p['id']}"]
                                    st.rerun()
                            with db:
                                if st.button("❌ Cancel",key=f"cdc_{p['id']}"):
                                    del st.session_state[f"_cdu_{p['id']}"]; st.rerun()

        with sub_create:
            section_header("Create New User","➕")
            depts=[d["department_name"] for d in fetch_departments()]
            with st.form("adm_create_user"):
                ca,cb=st.columns(2)
                with ca:
                    cn=st.text_input("Full Name *")
                    ce=st.text_input("Email *")
                    cd=st.selectbox("Department",depts)
                with cb:
                    cr=st.selectbox("Role",list(ROLES.values()))
                    cp=st.text_input("Password *",type="password")
                    cp2=st.text_input("Confirm Password *",type="password")
                if st.form_submit_button("➕ Create User",use_container_width=True):
                    errs=[]
                    if not cn.strip(): errs.append("Name required.")
                    if not validate_email(ce): errs.append("Valid email required.")
                    ok,mp=validate_password(cp)
                    if not ok: errs.append(mp)
                    if cp!=cp2: errs.append("Passwords don't match.")
                    if errs:
                        for e in errs: st.error(e)
                    else:
                        rk=[k for k,v in ROLES.items() if v==cr][0]
                        ok,msg=admin_create_user(ce.strip(),cp,cn.strip(),cd,rk)
                        st.success(msg) if ok else st.error(msg)

    # ── DEPARTMENTS ───────────────────────────────────────
    with tab_dept:
        section_header("Department Management","🏛️")
        depts=fetch_departments()
        with st.expander("➕ Add Department"):
            with st.form("add_dept"):
                da,db=st.columns(2)
                with da: dn=st.text_input("Department Name *")
                with db: dc=st.text_input("Code (e.g. CSE)")
                if st.form_submit_button("Add"):
                    if dn.strip():
                        if add_department(dn.strip(),dc.strip()): st.success("Added."); st.rerun()
                    else: st.error("Name required.")

        if depts:
            df_d=pd.DataFrame([{"Department":d["department_name"],"Code":d.get("code",""),
                                 "Created":d.get("created_at","")[:10],"ID":d["id"]} for d in depts])
            st.dataframe(df_d[["Department","Code","Created"]],use_container_width=True,hide_index=True)
            with st.expander("🗑️ Delete a Department"):
                do={d["department_name"]:d["id"] for d in depts}
                ds=st.selectbox("Select",list(do.keys()),key="del_dept_sel")
                if st.button("Delete",type="secondary",key="del_dept_btn"):
                    st.session_state["_cdd"]=do[ds]
                if st.session_state.get("_cdd")==do.get(ds):
                    st.warning(f"Delete '{ds}'? This may affect existing entries.")
                    dx,dy=st.columns(2)
                    with dx:
                        if st.button("✅ Yes",key="cdd_y"):
                            delete_department(do[ds]); st.success("Deleted.")
                            del st.session_state["_cdd"]; st.rerun()
                    with dy:
                        if st.button("❌ No",key="cdd_n"):
                            del st.session_state["_cdd"]; st.rerun()

    # ── ALL ENTRIES ───────────────────────────────────────
    with tab_entries:
        section_header("All Research Entries","📋")
        ae1,ae2,ae3=st.columns(3)
        with ae1: aed=st.selectbox("Dept",["All"]+[d["department_name"] for d in fetch_departments()],key="ae_d")
        with ae2: aet=st.selectbox("Type",["All"]+RESEARCH_TYPES,key="ae_t")
        with ae3: aes=st.text_input("🔍 Search",key="ae_s")
        aef={}
        if aed!="All": aef["department"]=aed
        if aet!="All": aef["research_type"]=aet
        ae=fetch_all_entries(aef)
        if aes: ae=[e for e in ae if aes.lower() in e.get("title","").lower()]
        df_ae=entries_to_dataframe(ae)
        st.markdown(f"**{len(ae)} entries**")
        exc1,exc2=st.columns(2)
        with exc1:
            st.download_button("⬇ CSV",to_csv_bytes(df_ae),"all_research.csv","text/csv",use_container_width=True)
        with exc2:
            st.download_button("⬇ Excel",to_excel_bytes(df_ae,"All Entries"),"all_research.xlsx",
                               "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",use_container_width=True)
        st.dataframe(
            df_ae.head(100),
            use_container_width=True,
            hide_index=True,
            column_config={
                "Document": st.column_config.LinkColumn("Document", display_text="Download")
            }
        )

    # ── MONITOR ───────────────────────────────────────────
    with tab_monitor:
        section_header("Submission Monitor — Current Month","📡")
        all_profiles=fetch_all_profiles()
        faculty=[p for p in all_profiles if p["role"]=="faculty" and p.get("is_active",True)]
        cm,cy=get_current_month_num(),get_current_year()
        month_entries=fetch_all_entries({"month":cm,"year":cy})
        submitters=set(e["faculty_id"] for e in month_entries)
        submitted=[f for f in faculty if f["id"] in submitters]
        missing=[f for f in faculty if f["id"] not in submitters]

        ma,mb=st.columns(2)
        with ma: metric_card("Submitted",len(submitted),"✅","#2ECC71")
        with mb: metric_card("Not Submitted",len(missing),"⚠️","#E74C3C")

        st.markdown("---")
        section_header("Faculty Who Haven't Submitted This Month","⚠️")
        if missing:
            ms_rows=[{"Name":f.get("full_name",""),"Email":f.get("email",""),
                      "Department":f.get("department",""),"Role":f.get("role","").title()}
                     for f in missing]
            st.dataframe(pd.DataFrame(ms_rows),use_container_width=True,hide_index=True)
            csv_miss=pd.DataFrame(ms_rows).to_csv(index=False).encode()
            st.download_button("⬇ Export Missing List (CSV)",csv_miss,
                               "missing_submissions.csv","text/csv")
        else:
            st.success("✅ All active faculty have submitted for this month!")

    # ── REMINDERS ─────────────────────────────────────────
    with tab_reminders:
        section_header("Reminder Management","🔔")
        user=get_current_user()
        with st.expander("➕ Send New Reminder"):
            with st.form("add_rem"):
                rm,rn=st.columns(2)
                with rm:
                    rmsg=st.text_area("Message *",height=90,
                                      placeholder="e.g. Submit your monthly entries by the 25th.")
                with rn:
                    rr=st.selectbox("Target Role",["all","faculty","hod","rd_coordinator"])
                    rd_=st.text_input("Dept (blank=all)")
                    re_=st.date_input("Expires On",value=None)
                if st.form_submit_button("📤 Send Reminder",use_container_width=True):
                    if not rmsg.strip(): st.error("Message required.")
                    else:
                        ok=add_reminder(rmsg.strip(),rr,rd_.strip() or None,
                                        user["id"] if user else None,
                                        re_.isoformat() if re_ else None)
                        if ok: st.success("Reminder sent!"); st.rerun()

        all_rem=fetch_all_reminders()
        if all_rem:
            for rem in all_rem:
                rc1,rc2=st.columns([5,1])
                with rc1: reminder_card(rem)
                with rc2:
                    st.markdown("<br>",unsafe_allow_html=True)
                    if rem.get("is_active"):
                        if st.button("Deactivate",key=f"da_{rem['id']}",use_container_width=True):
                            deactivate_reminder(rem["id"]); st.rerun()
                    else:
                        st.markdown("<span style='color:var(--text-muted);font-size:0.82rem;font-weight:500;'>Inactive</span>",
                                    unsafe_allow_html=True)
        else:
            st.info("No reminders sent yet.")

    # ── ANALYTICS ─────────────────────────────────────────
    with tab_analytics:
        section_header("Platform Analytics","📊")
        all_e=fetch_all_entries()
        all_p=fetch_all_profiles()
        if not all_e:
            st.info("No data available.")
        else:
            r1,r2=st.columns(2)
            with r1:
                st.plotly_chart(pie_chart(
                    ["Journal","Conference","Patent","Research Proposal"],
                    [stats["journals"],stats["conferences"],stats["patents"],stats["proposals"]],
                    "Research Type Mix"), use_container_width=True)
            with r2:
                role_cnt={ROLES.get(p.get("role","faculty"),"Faculty"):0 for p in all_p}
                for p in all_p:
                    lbl=ROLES.get(p.get("role","faculty"),"Faculty")
                    role_cnt[lbl]=role_cnt.get(lbl,0)+1
                st.plotly_chart(pie_chart(list(role_cnt.keys()),list(role_cnt.values()),
                                          "User Role Distribution"), use_container_width=True)

            # Year-wise research output (single clean chart)
            section_header("Year-wise Research Output", "📅")
            st.plotly_chart(yearly_comparison(all_e, "Year-wise Research Submissions"),
                            use_container_width=True)

            # Dept activity bar
            section_header("Department Activity","🏛️")
            dc={}
            for e in all_e:
                d=e.get("department","Unknown"); dc[d]=dc.get(d,0)+1
            top=sorted(dc.items(),key=lambda x:x[1],reverse=True)[:10]
            if top:
                ns,vs=zip(*top)
                st.plotly_chart(horizontal_bar(list(ns),list(vs),"Top Departments by Submissions"),
                                use_container_width=True)
