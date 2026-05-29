"""
pages/auth_page.py - Premium Light-theme Login UI (Split Layout)
"""
import streamlit as st
from services.auth_service import (
    sign_in, sign_up, request_password_reset,
    resend_verification_email, clear_pending_verification,
)
from database.queries import get_department_names
from components.styles import inject_css
from config import APP_NAME, INSTITUTION_NAME, ROLES
from utils.validators import validate_email, validate_password
from utils.helpers import get_image_base64

def render_auth_page():
    inject_css()
    _inject_auth_only_css()

    logo_base64 = get_image_base64("assets/hkbk_official_logo.png")
    logo_html = (f'<img src="data:image/png;base64,{logo_base64}" style="width:120px;margin-bottom:24px;">'
                 if logo_base64 else '<div style="font-size:3.5rem;margin-bottom:12px;">🎓</div>')

    # ── Email verification pending ─────────────────────────
    pending_email = st.session_state.get("pending_verify_email")
    if pending_email:
        _render_verification_pending(pending_email)
        return

    # ── SPLIT LAYOUT ──────────────────────────────────────
    col_left, col_right = st.columns([1.1, 1], gap="large")

    with col_left:
        st.markdown(f"""
        <div class="auth-hero">
            <div class="auth-hero-content">
                {logo_html}
                <h1 style="font-size:2.4rem;font-weight:800;color:var(--primary);margin-bottom:8px;line-height:1.2;">
                    {APP_NAME}
                </h1>
                <h2 style="font-size:1.1rem;color:var(--secondary);font-weight:600;margin-bottom:24px;">
                    {INSTITUTION_NAME}
                </h2>
                <p style="font-size:0.95rem;color:var(--text-secondary);line-height:1.6;margin-bottom:32px;max-width:85%;">
                    A modern, intelligent platform designed to streamline academic research submissions, track patents, and generate NBA/NAAC accreditation reports instantly.
                </p>
                <div class="hero-stats">
                    <div class="stat-item">
                        <strong>AI-Powered</strong>
                        <span>Auto-extraction</span>
                    </div>
                    <div class="stat-item">
                        <strong>Real-time</strong>
                        <span>NBA Analytics</span>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_right:
        tab_login, tab_reg, tab_reset = st.tabs(["🔑 Sign In", "📝 Register", "🔓 Reset Password"])

        # ── SIGN IN ────────────────────────────────────────
        with tab_login:
            st.markdown("<h3 style='margin-top:8px;margin-bottom:24px;font-size:1.4rem;color:var(--secondary);font-weight:700;'>Welcome back</h3>", unsafe_allow_html=True)
            with st.form("login_form"):
                email = st.text_input("Email Address", placeholder="you@hkbk.edu.in")
                password = st.text_input("Password", type="password", placeholder="••••••••")
                
                st.markdown("<br>", unsafe_allow_html=True)
                submitted = st.form_submit_button("Sign In →", use_container_width=True)
                
            if submitted:
                if not email.strip() or not password:
                    st.error("Please enter your email and password.")
                elif not validate_email(email):
                    st.error("Enter a valid email address.")
                else:
                    with st.spinner("Authenticating…"):
                        ok, msg = sign_in(email.strip().lower(), password)
                    if ok:
                        st.success("Successfully authenticated!")
                        st.rerun()
                    elif msg == "EMAIL_NOT_VERIFIED":
                        st.rerun()  # pending_verify_email is now set
                    else:
                        st.error("Invalid email or password.")

        # ── REGISTER ───────────────────────────────────────
        with tab_reg:
            st.markdown("<h3 style='margin-top:8px;margin-bottom:20px;font-size:1.4rem;color:var(--secondary);font-weight:700;'>Create Account</h3>", unsafe_allow_html=True)
            departments = get_department_names() or [
                "Computer Science and Engineering", "Electronics and Communication Engineering",
                "Mechanical Engineering", "Civil Engineering"
            ]

            with st.form("register_form", clear_on_submit=True):
                full_name = st.text_input("Full Name", placeholder="Dr. Jane Smith")
                reg_email = st.text_input("Official Email", placeholder="you@hkbk.edu.in")
                department = st.selectbox("Department", departments)
                role_label = st.selectbox("Role", list(ROLES.values()))
                role_key = [k for k, v in ROLES.items() if v == role_label][0]

                st.markdown("<hr style='margin:16px 0;opacity:0.5;'>", unsafe_allow_html=True)
                cp1, cp2 = st.columns(2)
                with cp1: reg_pass = st.text_input("Password", type="password", placeholder="Min 8 chars")
                with cp2: confirm = st.text_input("Confirm", type="password", placeholder="Repeat password")

                if reg_pass:
                    strength, hint, color = _password_strength(reg_pass)
                    st.markdown(f'<div style="font-size:0.75rem;margin-top:-8px;margin-bottom:12px;color:{color};font-weight:600;">{strength}: <span style="color:var(--text-secondary);font-weight:400;">{hint}</span></div>', unsafe_allow_html=True)

                agreed = st.checkbox("I agree to the institutional data policy")
                st.markdown("<br>", unsafe_allow_html=True)
                reg_btn = st.form_submit_button("Create Account →", use_container_width=True)

            if reg_btn:
                errors = _validate_registration(full_name, reg_email, reg_pass, confirm, agreed)
                if errors:
                    for e in errors: st.error(e)
                else:
                    with st.spinner("Creating account…"):
                        ok, msg = sign_up(reg_email.strip().lower(), reg_pass, full_name.strip(), department, role_key)
                    if ok:
                        if msg == "VERIFY_EMAIL":
                            st.session_state["pending_verify_email"] = reg_email.strip().lower()
                            st.rerun()
                        else:
                            st.success("✅ Account created successfully! You can now sign in.")
                    else:
                        # Show the actual error from Supabase for easier debugging
                        if "already registered" in msg.lower() or "already exists" in msg.lower():
                            st.error("⚠️ An account with this email already exists. Please sign in instead.")
                        elif "email" in msg.lower() and "invalid" in msg.lower():
                            st.error("⚠️ Invalid email address format.")
                        elif "password" in msg.lower():
                            st.error(f"⚠️ Password issue: {msg}")
                        elif "signup" in msg.lower() and "disabled" in msg.lower():
                            st.error("⚠️ New registrations are currently disabled in Supabase. Go to Supabase → Authentication → Providers → Email → Enable 'Allow new users to sign up'.")
                        else:
                            st.error(f"Registration failed: {msg}")

        # ── RESET PASSWORD ─────────────────────────────────
        with tab_reset:
            st.markdown("<h3 style='margin-top:8px;margin-bottom:24px;font-size:1.4rem;color:var(--secondary);font-weight:700;'>Reset Password</h3>", unsafe_allow_html=True)
            with st.form("reset_form", clear_on_submit=True):
                reset_email = st.text_input("Email Address", placeholder="you@hkbk.edu.in")
                st.markdown("<br>", unsafe_allow_html=True)
                if st.form_submit_button("Send Reset Link →", use_container_width=True):
                    if not validate_email(reset_email):
                        st.error("Enter a valid email address.")
                    else:
                        with st.spinner("Sending…"):
                            ok, msg = request_password_reset(reset_email.strip().lower())
                        st.success("If the email exists, a reset link was sent.")



    st.markdown("""
    <p style="text-align:center;color:var(--text-secondary);font-size:0.75rem;margin-top:32px;font-weight:500;">
    🔒 Secured with Supabase Auth · Academic SaaS Edition
    </p>""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
# EMAIL VERIFICATION PENDING PAGE
# ════════════════════════════════════════════════════════════

def _render_verification_pending(email: str):
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.markdown(f"""
        <div style="background:var(--card-bg);border:1px solid var(--border);border-radius:16px;padding:48px 40px;text-align:center;box-shadow:var(--shadow-md);margin-top:60px;">
            <div style="font-size:4rem;margin-bottom:16px;">✉️</div>
            <h2 style="font-size:1.6rem;font-weight:800;color:var(--secondary);margin-bottom:12px;">Verify Your Email</h2>
            <p style="color:var(--text-secondary);font-size:0.95rem;margin-bottom:16px;">We sent a secure verification link to:</p>
            <div style="background:var(--primary-light);border:1px solid #BFDBFE;color:var(--primary);padding:12px 16px;border-radius:8px;font-weight:600;font-size:1rem;margin-bottom:24px;">
                {email}
            </div>
            <p style="color:var(--text-secondary);font-size:0.85rem;line-height:1.6;margin-bottom:32px;">
                Click the link in the email to activate your account.<br>Check your spam folder if you don't see it within 2 minutes.
            </p>
        </div>
        """, unsafe_allow_html=True)

        ca, cb = st.columns(2)
        with ca:
            if st.button("Resend Email", use_container_width=True):
                with st.spinner("Sending…"):
                    ok, msg = resend_verification_email(email)
                st.success("Verification email sent.") if ok else st.error("Failed to send.")
        with cb:
            if st.button("← Back to Sign In", use_container_width=True, type="secondary"):
                clear_pending_verification()
                st.rerun()


# ════════════════════════════════════════════════════════════
# HELPERS
# ════════════════════════════════════════════════════════════

def _password_strength(pwd: str) -> tuple[str, str, str]:
    import re
    score = sum([len(pwd) >= 8, len(pwd) >= 12, bool(re.search(r"[A-Z]", pwd)), bool(re.search(r"[0-9]", pwd)), bool(re.search(r"[^A-Za-z0-9]", pwd))])
    if score <= 2: return "Weak", "Add uppercase/digits/symbols", "var(--danger)"
    elif score == 3: return "Fair", "Getting stronger", "var(--warning)"
    else: return "Strong", "Excellent password", "var(--success)"

def _validate_registration(name, email, pwd, confirm, agreed) -> list[str]:
    errs = []
    if not name.strip(): errs.append("Full name is required.")
    if not validate_email(email): errs.append("Enter a valid email address.")
    ok, msg = validate_password(pwd)
    if not ok: errs.append(msg)
    if pwd != confirm: errs.append("Passwords do not match.")
    if not agreed: errs.append("Please agree to the data policy.")
    return errs

def _inject_auth_only_css():
    st.markdown("""
    <style>
    [data-testid="stSidebar"] { display: none !important; }
    
    .auth-hero {
        padding: 40px;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    .hero-stats {
        display: flex; gap: 24px; margin-top: 16px;
    }
    .stat-item {
        background: var(--card-bg);
        border: 1px solid var(--border);
        padding: 16px 20px;
        border-radius: 12px;
        box-shadow: var(--shadow-sm);
    }
    .stat-item strong { display: block; color: var(--primary); font-size: 1.1rem; font-weight: 800; margin-bottom: 4px; }
    .stat-item span { color: var(--text-secondary); font-size: 0.8rem; font-weight: 500; text-transform: uppercase; letter-spacing: 0.05em; }

    .auth-card-wrapper {
        background: var(--card-bg);
        border: 1px solid var(--border);
        border-radius: 20px;
        padding: 32px 40px 40px;
        box-shadow: var(--shadow-md);
        margin-top: 24px;
    }
    </style>
    """, unsafe_allow_html=True)
