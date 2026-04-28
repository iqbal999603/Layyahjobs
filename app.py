import streamlit as st
import random
import string
import pandas as pd
from io import StringIO
from supabase import create_client, Client

# ================== سیکرٹس سے کنکشن ==================
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
ADMIN_KEY = st.secrets["ADMIN_KEY"]

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ================== مددگار فنکشنز ==================
def generate_deletion_key(length=8):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

def insert_job(title, company, location, salary, description, contact, job_type, deletion_key):
    data = {
        "title": title,
        "company": company,
        "location": location,
        "salary": salary,
        "description": description,
        "contact": contact,
        "job_type": job_type,
        "deletion_key": deletion_key
    }
    return supabase.table("jobs").insert(data).execute()

def update_job(job_id, updates):
    return supabase.table("jobs").update(updates).eq("id", job_id).execute()

def delete_job(job_id):
    return supabase.table("jobs").delete().eq("id", job_id).execute()

def fetch_all_jobs():
    res = supabase.table("jobs").select("*").order("created_at", desc=True).execute()
    return res.data if res.data else []

# ================== UI ==================
st.set_page_config(page_title="لیّہ جاب پورٹل", layout="wide")
st.title("💼 لیّہ جاب پورٹل")
st.markdown("### مقامی نوکریوں کا مرکز — بغیر لاگ ان")

menu = st.sidebar.radio("نیویگیشن", ["📋 نوکریاں دیکھیں", "✍️ نوکری ڈالیں", "🔐 ایڈمن"])

# --------------------- نوکریاں دیکھیں ---------------------
if menu == "📋 نوکریاں دیکھیں":
    st.header("دستیاب نوکریاں")
    jobs = fetch_all_jobs()
    if not jobs:
        st.info("ابھی کوئی نوکری موجود نہیں۔")
    else:
        for job in jobs:
            with st.expander(f"{job['title']} - {job['company'] or 'نامعلوم'} ({job['location']})"):
                st.write(f"**کمپنی:** {job['company'] or 'نہیں بتائی'}")
                st.write(f"**مقام:** {job['location']}")
                st.write(f"**تنخواہ:** {job['salary'] or 'بات چیت پر'}")
                st.write(f"**نوکری کی قسم:** {job['job_type'] or 'عام'}")
                st.write(f"**تفصیل:** {job['description'] or 'کوئی نہیں'}")
                st.write(f"**رابطہ:** {job['contact']}")
                # ترمیم/حذف کے لیے کلید درج کرنے کا بٹن
                if st.button(f"ترمیم / حذف کریں (ID {job['id']})", key=f"edit_{job['id']}"):
                    st.session_state["edit_job_id"] = job['id']
                if st.session_state.get("edit_job_id") == job['id']:
                    with st.form(key=f"edit_form_{job['id']}"):
                        user_key = st.text_input("اس نوکری کی خفیہ کلید (Deletion Key) ڈالیں", type="password")
                        submitted = st.form_submit_button("تصدیق")
                        if submitted:
                            if user_key == job['deletion_key']:
                                st.session_state["verified_key"] = user_key
                                st.session_state["edit_mode"] = True
                                st.success("کلید درست ہے! اب آپ ترمیم یا حذف کر سکتے ہیں۔")
                                st.rerun()
                            else:
                                st.error("غلط کلید!")
                    if st.session_state.get("edit_mode") and st.session_state.get("edit_job_id") == job['id']:
                        with st.form(key=f"edit_fields_{job['id']}"):
                            new_title = st.text_input("عنوان", value=job['title'])
                            new_company = st.text_input("کمپنی", value=job['company'])
                            new_location = st.text_input("مقام", value=job['location'])
                            new_salary = st.text_input("تنخواہ", value=job['salary'])
                            new_desc = st.text_area("تفصیل", value=job['description'])
                            new_contact = st.text_input("رابطہ", value=job['contact'])
                            # job_type index matching
                            job_types = ["کل وقتی", "پارٹ ٹائم", "آن لائن", "فری لانس", "دیگر"]
                            current_type = job['job_type'] if job['job_type'] in job_types else "کل وقتی"
                            type_index = job_types.index(current_type)
                            new_type = st.selectbox("نوکری کی قسم", job_types, index=type_index)
                            col1, col2 = st.columns(2)
                            with col1:
                                save_btn = st.form_submit_button("محفوظ کریں")
                            with col2:
                                delete_btn = st.form_submit_button("حذف کریں")
                            if save_btn:
                                updates = {"title": new_title, "company": new_company, "location": new_location, "salary": new_salary, "description": new_desc, "contact": new_contact, "job_type": new_type}
                                update_job(job['id'], updates)
                                st.success("نوکری اپ ڈیٹ ہوگئی!")
                                for key in ["edit_job_id", "verified_key", "edit_mode"]:
                                    if key in st.session_state:
                                        del st.session_state[key]
                                st.rerun()
                            if delete_btn:
                                delete_job(job['id'])
                                st.success("نوکری حذف ہوگئی!")
                                for key in ["edit_job_id", "verified_key", "edit_mode"]:
                                    if key in st.session_state:
                                        del st.session_state[key]
                                st.rerun()

# --------------------- نوکری ڈالیں ---------------------
elif menu == "✍️ نوکری ڈالیں":
    st.header("نئی نوکری شامل کریں")
    with st.form("job_form"):
        title = st.text_input("نوکری کا عنوان *")
        company = st.text_input("کمپنی / ادارہ")
        location = st.text_input("مقام", value="Layyah", help="ڈیفالٹ لیّہ ہے، دوسرا شہر لکھ سکتے ہیں")
        salary = st.text_input("تنخواہ (اختیاری)")
        description = st.text_area("تفصیل")
        contact = st.text_input("رابطہ فون / واٹس ایپ *")
        job_type = st.selectbox("نوکری کی قسم", ["کل وقتی", "پارٹ ٹائم", "آن لائن", "فری لانس", "دیگر"])
        submitted = st.form_submit_button("نوکری شائع کریں")
        if submitted:
            if not title.strip() or not contact.strip():
                st.error("عنوان اور رابطہ لازمی ہیں۔")
            else:
                del_key = generate_deletion_key()
                insert_job(title.strip(), company.strip(), location.strip(), salary.strip(), description.strip(), contact.strip(), job_type, del_key)
                st.success("نوکری کامیابی سے شائع ہوگئی!")
                st.markdown(f"### ⚠️ یہ خفیہ کلید نوٹ کر لیں: `{del_key}`")
                st.warning("یہ کلید آپ کی نوکری میں ترمیم یا حذف کرنے کے لیے ضروری ہے۔ اسے محفوظ جگہ رکھیں۔")

# --------------------- ایڈمن ---------------------
elif menu == "🔐 ایڈمن":
    st.header("ایڈمن پینل")
    admin_pass = st.text_input("ایڈمن کلید", type="password")
    if admin_pass == ADMIN_KEY:
        st.success("لاگ ان کامیاب")
        tab1, tab2 = st.tabs(["📋 تمام نوکریاں", "📁 درآمد / برآمد"])

        # ================== TAB 1: نوکریاں دیکھیں / حذف کریں ==================
        with tab1:
            jobs = fetch_all_jobs()
            if not jobs:
                st.info("کوئی نوکری نہیں")
            else:
                for job in jobs:
                    with st.expander(f"{job['title']} - {job['company']} (ID: {job['id']})"):
                        st.write(f"**مقام:** {job['location']}")
                        st.write(f"**رابطہ:** {job['contact']}")
                        st.write(f"**کلید:** {job['deletion_key']}")
                        if st.button(f"حذف کریں (ID {job['id']})", key=f"admin_del_{job['id']}"):
                            delete_job(job['id'])
                            st.warning("نوکری حذف ہوگئی")
                            st.rerun()

        # ================== TAB 2: درآمد / برآمد ==================
        with tab2:
            st.subheader("📥 برآمد (Export to CSV)")
            jobs = fetch_all_jobs()
            if jobs:
                # Convert to DataFrame
                df = pd.DataFrame(jobs)
                # Select and reorder columns for export (exclude deletion_key and id for safety)
                export_cols = ["title", "company", "location", "salary", "description", "contact", "job_type", "created_at"]
                df_export = df[[col for col in export_cols if col in df.columns]]
                csv = df_export.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 ڈاؤن لوڈ CSV",
                    data=csv,
                    file_name="layyah_jobs.csv",
                    mime="text/csv"
                )
            else:
                st.warning("برآمد کرنے کے لیے کوئی نوکری موجود نہیں۔")

            st.divider()
            st.subheader("📤 درآمد (Import from CSV)")
            st.caption("CSV فائل میں کم از کم `title` اور `contact` کالم لازمی ہیں۔ باقی کالم اختیاری ہیں۔")
            uploaded_file = st.file_uploader("CSV فائل منتخب کریں", type=["csv"])
            if uploaded_file is not None:
                try:
                    import_df = pd.read_csv(uploaded_file)
                    # Normalize column names: lower case, strip spaces
                    import_df.columns = [str(col).strip().lower() for col in import_df.columns]
                    # Required columns
                    required = ["title", "contact"]
                    missing = [col for col in required if col not in import_df.columns]
                    if missing:
                        st.error(f"❌ درج ذیل لازمی کالم غائب ہیں: {', '.join(missing)}")
                    else:
                        if st.button("📤 درآمد شروع کریں", type="primary"):
                            skipped = 0
                            imported = 0
                            for _, row in import_df.iterrows():
                                title_val = str(row['title']).strip()
                                contact_val = str(row['contact']).strip()
                                if not title_val or not contact_val:
                                    skipped += 1
                                    continue
                                # Optional fields with defaults
                                company = str(row.get('company', '')).strip()
                                location = str(row.get('location', 'Layyah')).strip()
                                salary = str(row.get('salary', '')).strip()
                                description = str(row.get('description', '')).strip()
                                job_type = str(row.get('job_type', 'کل وقتی')).strip()
                                # Valid job_type list
                                valid_types = ["کل وقتی", "پارٹ ٹائم", "آن لائن", "فری لانس", "دیگر"]
                                if job_type not in valid_types:
                                    job_type = "کل وقتی"
                                deletion_key = generate_deletion_key()
                                try:
                                    insert_job(title_val, company, location, salary, description, contact_val, job_type, deletion_key)
                                    imported += 1
                                except Exception as e:
                                    skipped += 1
                            if imported:
                                st.success(f"✅ {imported} نوکریاں کامیابی سے درآمد ہوگئیں!")
                            if skipped:
                                st.warning(f"⚠️ {skipped} نوکریاں چھوڑ دی گئیں (غلط یا نامکمل ڈیٹا)")
                            st.rerun()
                except Exception as e:
                    st.error(f"فائل پڑھنے میں خرابی: {e}")
    elif admin_pass:
        st.error("غلط ایڈمن کلید!")
