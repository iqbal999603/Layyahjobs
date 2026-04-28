import streamlit as st
import random
import string
import pandas as pd
from supabase import create_client, Client

# ================== سیکرٹس سے کنکشن ==================
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
ADMIN_KEY = st.secrets["ADMIN_KEY"]

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ================== مددگار فنکشن ==================
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

# ================== Import / Export ==================
def export_jobs():
    res = supabase.table("jobs").select("*").execute()
    jobs = res.data
    if not jobs:
        return None
    return pd.DataFrame(jobs)

def import_jobs(file):
    try:
        df = pd.read_csv(file)

        required_columns = ["title", "company", "location", "salary", "description", "contact", "job_type"]

        for col in required_columns:
            if col not in df.columns:
                return False, f"Column missing: {col}"

        records = []
        for _, row in df.iterrows():
            records.append({
                "title": str(row["title"]),
                "company": str(row["company"]),
                "location": str(row["location"]),
                "salary": str(row["salary"]),
                "description": str(row["description"]),
                "contact": str(row["contact"]),
                "job_type": str(row["job_type"]),
                "deletion_key": generate_deletion_key()
            })

        supabase.table("jobs").insert(records).execute()
        return True, "Import successful"

    except Exception as e:
        return False, str(e)

# ================== UI ==================
st.set_page_config(page_title="لیّہ جاب پورٹل", layout="wide")
st.title("💼 لیّہ جاب پورٹل")
st.markdown("### مقامی نوکریوں کا مرکز — بغیر لاگ ان")

menu = st.sidebar.radio("نیویگیشن", [
    "📋 نوکریاں دیکھیں",
    "✍️ نوکری ڈالیں",
    "📂 Import / Export",
    "🔐 ایڈمن"
])

# --------------------- نوکریاں دیکھیں ---------------------
if menu == "📋 نوکریاں دیکھیں":
    st.header("دستیاب نوکریاں")
    res = supabase.table("jobs").select("*").order("created_at", desc=True).execute()
    jobs = res.data

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

# --------------------- نوکری ڈالیں ---------------------
elif menu == "✍️ نوکری ڈالیں":
    st.header("نئی نوکری شامل کریں")

    with st.form("job_form"):
        title = st.text_input("نوکری کا عنوان *")
        company = st.text_input("کمپنی / ادارہ")
        location = st.text_input("مقام", value="Layyah")
        salary = st.text_input("تنخواہ")
        description = st.text_area("تفصیل")
        contact = st.text_input("رابطہ *")
        job_type = st.selectbox("نوکری کی قسم", ["کل وقتی", "پارٹ ٹائم", "آن لائن", "فری لانس", "دیگر"])

        submitted = st.form_submit_button("شائع کریں")

        if submitted:
            if not title.strip() or not contact.strip():
                st.error("عنوان اور رابطہ لازمی ہیں")
            else:
                del_key = generate_deletion_key()
                insert_job(title, company, location, salary, description, contact, job_type, del_key)

                st.success("نوکری شامل ہوگئی")
                st.code(del_key, language="text")

# --------------------- Import / Export ---------------------
elif menu == "📂 Import / Export":
    st.header("📂 ڈیٹا امپورٹ / ایکسپورٹ")

    # Export
    st.subheader("📤 Export")
    df = export_jobs()

    if df is not None:
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("CSV ڈاؤنلوڈ کریں", csv, "jobs_export.csv", "text/csv")
    else:
        st.info("کوئی ڈیٹا نہیں")

    st.divider()

    # Import
    st.subheader("📥 Import")
    file = st.file_uploader("CSV اپلوڈ کریں", type=["csv"])

    if file:
        success, msg = import_jobs(file)
        if success:
            st.success(msg)
            st.rerun()
        else:
            st.error(msg)

# --------------------- ایڈمن ---------------------
elif menu == "🔐 ایڈمن":
    st.header("ایڈمن پینل")

    admin_pass = st.text_input("پاس ورڈ", type="password")

    if admin_pass == ADMIN_KEY:
        st.success("لاگ ان ہو گیا")

        res = supabase.table("jobs").select("*").execute()
        jobs = res.data

        for job in jobs:
            with st.expander(f"{job['title']} (ID: {job['id']})"):
                st.write(job)

                if st.button(f"حذف کریں {job['id']}"):
                    delete_job(job['id'])
                    st.warning("حذف ہوگئی")
                    st.rerun()

    elif admin_pass:
        st.error("غلط پاس ورڈ")
