"""
pages/profile_management.py - Comprehensive Profile Management
"""
import streamlit as st
from services.auth_service import get_current_profile, get_current_user
from database.queries import update_profile
from services.storage_service import upload_avatar
from components.ui import page_header, section_header
from utils.validators import sanitize_text

def render_profile_management():
    profile = get_current_profile()
    if not profile:
        st.error("Profile not found.")
        return

    uid = profile["id"]
    
    page_header("My Profile", "Manage your academic identity and professional links", "")

    col_form, col_preview = st.columns([2, 1], gap="large")

    with col_form:
        section_header("General Information", "📄")
        with st.form("profile_general_form"):
            full_name = st.text_input("Full Name", value=profile.get("full_name", ""))
            
            # Email is typically read-only as it's linked to authentication
            st.text_input("Email Address (Primary)", value=profile.get("email", ""), disabled=True, help="Contact admin to change your primary login email.")
            
            c1, c2 = st.columns(2)
            with c1:
                from database.queries import get_department_names
                depts = get_department_names() or []
                cur_dept = profile.get("department", "")
                dept = st.selectbox("Department", depts, index=depts.index(cur_dept) if cur_dept in depts else 0)
            with c2:
                designation = st.text_input("Designation", value=profile.get("designation", "") or "", placeholder="e.g. Assistant Professor")

            emp_id = st.text_input("Employee ID", value=profile.get("employee_id", "") or "")
            mobile = st.text_input("Mobile Number", value=profile.get("mobile_number", "") or "")
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.form_submit_button("Update Basic Info"):
                updates = {
                    "full_name": sanitize_text(full_name),
                    "department": dept,
                    "designation": sanitize_text(designation),
                    "employee_id": sanitize_text(emp_id),
                    "mobile_number": sanitize_text(mobile)
                }
                try:
                    if update_profile(uid, updates):
                        st.success("Basic info updated!")
                        st.rerun()
                except Exception as e:
                    if "column" in str(e).lower():
                        st.error("⚠️ **Database Update Required**")
                        st.info("It looks like your database is missing some new columns. Please run the SQL command provided by the assistant in your Supabase SQL Editor to fix this.")
                        st.code("""ALTER TABLE profiles ADD COLUMN IF NOT EXISTS photo_url TEXT, ADD COLUMN IF NOT EXISTS designation TEXT, ADD COLUMN IF NOT EXISTS employee_id TEXT, ADD COLUMN IF NOT EXISTS mobile_number TEXT, ADD COLUMN IF NOT EXISTS orcid_id TEXT, ADD COLUMN IF NOT EXISTS scopus_id TEXT, ADD COLUMN IF NOT EXISTS vidhwan_id TEXT, ADD COLUMN IF NOT EXISTS google_scholar_link TEXT, ADD COLUMN IF NOT EXISTS research_role TEXT, ADD COLUMN IF NOT EXISTS scholars_data JSONB; NOTIFY pgrst, 'reload schema';""", language="sql")
                    else:
                        st.error(f"Update failed: {e}")

        section_header("Research Supervision", "👨‍🏫")
        
        # We handle this outside st.form so dynamic dropdowns (like Number of Scholars) work instantly
        cur_role = profile.get("research_role", "None") or "None"
        r_role = st.selectbox("Research Role", ["None", "Scholar", "Research Supervisor"], 
                              index=["None", "Scholar", "Research Supervisor"].index(cur_role))
        
        scholars_data = profile.get("scholars_data", []) or []
        new_scholars_data = []

        if r_role == "Research Supervisor":
            num_scholars = st.selectbox("Number of Scholars", list(range(0, 11)), 
                                        index=len(scholars_data) if 0 <= len(scholars_data) <= 10 else 0)
            
            st.markdown("##### Scholar Details")
            for i in range(num_scholars):
                existing_scholar = scholars_data[i] if i < len(scholars_data) else {}
                c_name, c_status = st.columns([3, 2])
                with c_name:
                    s_name = st.text_input(f"Scholar {i+1} Name", value=existing_scholar.get("name", ""), key=f"s_name_{i}")
                with c_status:
                    status_opts = ["Registered", "Coursework Completed", "Comprehensive Viva", 
                                   "Doctoral Committee 1", "Doctoral Committee 2", "Doctoral Committee 3", 
                                   "Thesis submitted", "Final Defence"]
                    cur_stat = existing_scholar.get("status", "Registered")
                    s_status = st.selectbox(f"Status {i+1}", status_opts, 
                                            index=status_opts.index(cur_stat) if cur_stat in status_opts else 0,
                                            key=f"s_status_{i}")
                new_scholars_data.append({"name": s_name, "status": s_status})
        
        if st.button("Update Research Supervision", type="primary"):
            updates = {"research_role": r_role}
            if r_role == "Research Supervisor":
                updates["scholars_data"] = new_scholars_data
            else:
                updates["scholars_data"] = []
                
            try:
                import json
                # Ensure we serialize lists correctly if the DB layer doesn't auto-handle JSON
                # Supabase handles dict/list to JSONB naturally through the python client
                if update_profile(uid, updates):
                    st.success("Research Supervision details updated!")
                    st.rerun()
            except Exception as e:
                st.error("⚠️ **Database Update Required**")
                st.info("Please run the following SQL command in your Supabase SQL Editor:")
                st.code("""ALTER TABLE profiles ADD COLUMN IF NOT EXISTS research_role TEXT, ADD COLUMN IF NOT EXISTS scholars_data JSONB; NOTIFY pgrst, 'reload schema';""", language="sql")


        section_header("Professional IDs & Links", "🔗")
        with st.form("profile_links_form"):
            c1, c2 = st.columns(2)
            with c1:
                orcid = st.text_input("ORCID ID", value=profile.get("orcid_id", "") or "")
                scopus = st.text_input("Scopus ID", value=profile.get("scopus_id", "") or "")
            with c2:
                vidhwan = st.text_input("Vidhwan ID", value=profile.get("vidhwan_id", "") or "")
                scholar = st.text_input("Google Scholar Link", value=profile.get("google_scholar_link", "") or "")
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.form_submit_button("Update Professional Links"):
                updates = {
                    "orcid_id": sanitize_text(orcid),
                    "scopus_id": sanitize_text(scopus),
                    "vidhwan_id": sanitize_text(vidhwan),
                    "google_scholar_link": sanitize_text(scholar)
                }
                if update_profile(uid, updates):
                    st.success("Links updated!")
                    st.rerun()

    with col_preview:
        section_header("Profile Photo", "📸")
        photo_url = profile.get("photo_url")
        if photo_url:
            st.image(photo_url, width=200, use_container_width=False, caption="Current Photo")
        else:
            st.info("No profile photo uploaded.")
        
        uploaded_photo = st.file_uploader("Upload new photo", type=["jpg", "png", "jpeg"], key="avatar_upload")
        if uploaded_photo:
            if st.button("Save New Photo", use_container_width=True):
                with st.spinner("Uploading photo..."):
                    new_url = upload_avatar(uploaded_photo.getvalue(), uploaded_photo.name, uid)
                    if new_url:
                        if update_profile(uid, {"photo_url": new_url}):
                            st.success("Photo updated successfully!")
                            st.rerun()
                        else:
                            st.error("Failed to update profile with new photo URL.")
                    else:
                        st.error("Failed to upload photo to storage.")

        st.markdown("---")
        st.markdown(f"**Department:** {profile.get('department')}")
        st.markdown(f"**Role:** {profile.get('role','').title()}")
        st.markdown(f"**Account Status:** {'✅ Active' if profile.get('is_active') else '⚠️ Pending'}")
