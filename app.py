import streamlit as st
import psycopg2
import os
import pandas as pd
from datetime import datetime, timedelta

from streamlit_autorefresh import st_autorefresh
count = st_autorefresh(interval=3000, limit=None, key="datarefresh")

# Page Configuration
st.set_page_config(page_title="Transcription Analytics Dashboard", layout="wide")

# Inject CSS for RTL alignment, excluding chart components to prevent text distortion
st.markdown("""
    <style>
    body, .stApp, .main, header, footer {
        direction: rtl !important;
        text-align: right !important;
    }
    [data-testid="stSidebar"] {
        direction: rtl !important;
        text-align: right !important;
    }
    .stButton, .stDownloadButton, .stTextInput, .stSelectbox, .stRadio, .stCheckbox {
        direction: rtl !important;
        text-align: right !important;
    }
    h1, h2, h3, h4, h5, h6, p, label, .stMarkdown {
        text-align: right !important;
    }
    /* Exclude Vega/Altair SVG chart text elements from forced CSS rotation */
    .stChart, div[data-testid="stVegaLiteChart"] {
        direction: ltr !important;
    }
    /* Metric Card Styling */
    div[data-testid="stMetric"] {
        background-color: #1e293b;
        border: 1px solid #334155;
        padding: 12px 16px;
        border-radius: 8px;
        text-align: right !important;
    }
    </style>
""", unsafe_allow_html=True)

DB_CONFIG = {
    "dbname": os.getenv("POSTGRES_DB", "timlul_db"),
    "user": os.getenv("POSTGRES_USER", "timlul_user"),
    "password": os.getenv("POSTGRES_PASSWORD", "timlul_password"),
    "host": os.getenv("DB_HOST", "postgres"),
    "port": os.getenv("DB_PORT", "5432")
}

@st.cache_data(ttl=2)
def load_data():
    # Connect to PostgreSQL database and retrieve all transcription jobs
    conn = psycopg2.connect(**DB_CONFIG)
    query = "SELECT * FROM transcription_jobs ORDER BY started_at DESC;"
    df = pd.read_sql(query, conn)
    conn.close()
    if not df.empty:
        df['started_at'] = pd.to_datetime(df['started_at'])
        df['job_date'] = df['started_at'].dt.date
    return df

df_raw = load_data()

# --- Sidebar Controls ---
st.sidebar.header("מסננים ופרמטרים")

if not df_raw.empty:
    filter_mode = st.sidebar.radio(
        "אופן הסינון:",
        ["טווח מוגדר", "תאריך ספציפי", "טווח תאריכים מותאם"]
    )

    df = df_raw.copy()

    # Apply date filters according to user selection
    if filter_mode == "טווח מוגדר":
        time_filter = st.sidebar.selectbox(
            "טווח זמן:",
            ["כל הזמן", "24 שעות אחרונות", "7 ימים אחרונים", "30 ימים אחרונים"]
        )
        max_date = df_raw['started_at'].max()
        if time_filter == "24 שעות אחרונות":
            df = df[df['started_at'] >= (max_date - timedelta(days=1))]
        elif time_filter == "7 ימים אחרונים":
            df = df[df['started_at'] >= (max_date - timedelta(days=7))]
        elif time_filter == "30 ימים אחרונים":
            df = df[df['started_at'] >= (max_date - timedelta(days=30))]

    elif filter_mode == "תאריך ספציפי":
        selected_date = st.sidebar.date_input(
            "בחר תאריך:",
            value=df_raw['job_date'].max(),
            min_value=df_raw['job_date'].min(),
            max_value=df_raw['job_date'].max()
        )
        df = df[df['job_date'] == selected_date]

    elif filter_mode == "טווח תאריכים מותאם":
        date_range = st.sidebar.date_input(
            "בחר טווח תאריכים:",
            value=(df_raw['job_date'].min(), df_raw['job_date'].max()),
            min_value=df_raw['job_date'].min(),
            max_value=df_raw['job_date'].max()
        )
        if isinstance(date_range, tuple) and len(date_range) == 2:
            start_date, end_date = date_range
            df = df[(df['job_date'] >= start_date) & (df['job_date'] <= end_date)]

    # Filter by user principal
    users = ["כל המשתמשים"] + list(df_raw['user_principal'].dropna().unique())
    selected_user = st.sidebar.selectbox("משתמש:", users)
    if selected_user != "כל המשתמשים":
        df = df[df['user_principal'] == selected_user]

else:
    df = df_raw.copy()

# --- Main Dashboard Title ---
st.title("מערכת ניטור ותמלול - דשבורד ניהולי")
st.caption("מעקב ביצועים, עלויות, וזיהוי מידע רגיש (PII)")
st.markdown("<br>", unsafe_allow_html=True)

if not df.empty:
    tab1, tab2, tab3 = st.tabs([
        "מבט על כולל", 
        "דוחות יומיים", 
        "כלל המשימות "
    ])

    # ---------------------------------------------------------
    # TAB 1: Global Macro Overview
    # ---------------------------------------------------------
    with tab1:
        st.subheader("מדדי מאקרו מצטברים")
        c1, c2, c3, c4, c5, c6 = st.columns(6)
        
        c1.metric("סה\"כ עבודות", len(df))
        c2.metric("עלות משוערת", f"${df['estimated_total_cost_usd'].sum():.3f}")
        c3.metric("מידע רגיש שהותמם", int(df['sensitive_data_total'].sum()))
        
        audio_mins = df['audio_duration_seconds'].sum() / 60
        c4.metric("משך הקלטות (דקות)", f"{audio_mins:.1f}")
        
        total_audio = df['audio_duration_seconds'].sum()
        total_proc = df['total_processing_seconds'].sum()
        speed_ratio = (total_proc / total_audio) if total_audio > 0 else 0
        c5.metric("יחס מהירות עיבוד", f"{speed_ratio:.2f}x")
        
        success_rate = (len(df[df['status'] == 'success']) / len(df)) * 100
        c6.metric("אחוז הצלחה", f"{success_rate:.0f}%")

        st.markdown("---")

        col_left, col_right = st.columns(2)

        with col_left:
            st.subheader("התפלגות מידע רגיש שהותמם")
            pii_data = {
                "ת.ז.": df['israeli_id_count'].sum(),
                "אשראי": df['card_number_count'].sum(),
                "טלפון": df['phone_number_count'].sum(),
                "רכב": df['vehicle_number_count'].sum(),
                "דוא\"ל": df['email_count'].sum(),
                "שם משפחה": df['last_name_count'].sum(),
                "דרכון": df['passport_count'].sum(),
                "כתובת": df['address_count'].sum()
            }
            st.bar_chart(pd.DataFrame(list(pii_data.items()), columns=["סוג מידע רגיש", "כמות"]).set_index("סוג מידע רגיש"))

        with col_right:
            st.subheader("זמני עיבוד (משך הקלטה מול זמן עיבוד כולל)")
            df_chart = df.copy()
            df_chart['time_label'] = df_chart['started_at'].dt.strftime('%d/%m %H:%M')
            st.line_chart(df_chart.set_index('time_label')[['audio_duration_seconds', 'total_processing_seconds']])

    # ---------------------------------------------------------
    # TAB 2: Visual Daily Reports
    # ---------------------------------------------------------
    with tab2:
        st.subheader("דוח יומי - סיכום מאקרו ויזואלי")
        
        available_dates = sorted(df_raw['job_date'].unique(), reverse=True)
        
        selected_report_date = st.selectbox(
            "בחר תאריך לצפייה בדוח היומי:",
            available_dates,
            format_func=lambda d: f"דוח יומי - {d.strftime('%Y-%m-%d')}"
        )
        
        df_daily = df_raw[df_raw['job_date'] == selected_report_date]

        if not df_daily.empty:
            st.markdown(f"### סיכום יומי – {selected_report_date.strftime('%Y-%m-%d')}")
            st.markdown("<br>", unsafe_allow_html=True)

            m1, m2, m3, m4 = st.columns(4)
            success_count = len(df_daily[df_daily['status'] == 'success'])
            fail_count = len(df_daily) - success_count
            
            m1.metric("סה\"כ עבודות תמלול", len(df_daily), f"{success_count} בהצלחה / {fail_count} נכשלו")
            m2.metric("משך הקלטות כולל", f"{(df_daily['audio_duration_seconds'].sum()/60):.1f} דקות")
            m3.metric("זמן עיבוד כולל", f"{(df_daily['total_processing_seconds'].sum()/60):.1f} דקות")
            m4.metric("זמן עיבוד Gemini", f"{(df_daily['gemini_processing_seconds'].sum()/60):.1f} דקות")

            st.markdown("<br>", unsafe_allow_html=True)

            col_pii_vis, col_gemini_vis = st.columns([3, 2])

            with col_pii_vis:
                st.markdown("#### התפלגות מידע רגיש שהותמם (PII)")
                daily_pii_map = {
                    "ת.ז.": df_daily['israeli_id_count'].sum(),
                    "אשראי": df_daily['card_number_count'].sum(),
                    "טלפון": df_daily['phone_number_count'].sum(),
                    "רכב": df_daily['vehicle_number_count'].sum(),
                    "דוא\"ל": df_daily['email_count'].sum(),
                    "דרכון": df_daily['passport_count'].sum(),
                    "שם משפחה": df_daily['last_name_count'].sum(),
                    "כתובת": df_daily['address_count'].sum()
                }
                active_pii = {k: v for k, v in daily_pii_map.items() if v > 0}
                if active_pii:
                    st.bar_chart(pd.DataFrame(list(active_pii.items()), columns=["סוג", "כמות"]).set_index("סוג"))
                else:
                    st.info("לא זוהה מידע רגיש ביום זה.")

            with col_gemini_vis:
                st.markdown("#### שימוש ב-Gemini ועלויות")
                gm1, gm2 = st.columns(2)
                gm1.metric("Input Tokens", f"{df_daily['input_tokens'].sum():,}")
                gm2.metric("Output Tokens", f"{df_daily['output_tokens'].sum():,}")
                
                gm3, gm4 = st.columns(2)
                gm3.metric("Thinking Tokens", f"{df_daily['thinking_tokens'].sum():,}")
                gm4.metric("עלות משוערת כוללת", f"${df_daily['estimated_total_cost_usd'].sum():.4f}")

            st.markdown("---")

            st.markdown(f"### פירוט עבודות התמלול ליום זה ({len(df_daily)} עבודות)")
            for idx, (_, job) in enumerate(df_daily.iterrows(), 1):
                with st.expander(f"עבודת תמלול #{idx} - {job['filename']} ({job['user_principal']})", expanded=False):
                    c_j1, c_j2, c_j3 = st.columns(3)
                    
                    c_j1.metric("משך הקלטה", f"{(job['audio_duration_seconds']/60):.1f} דק'")
                    c_j2.metric("זמן עיבוד", f"{(job['total_processing_seconds']/60):.1f} דק'")
                    c_j3.metric("עלות עבודה", f"${job['estimated_total_cost_usd']:.4f}")

                    st.write(f"**מזהה עבודה:** `{job['job_id']}` | **סטטוס:** `{job['status']}` | **PII שהותמם:** `{job['sensitive_data_total']}`")
        else:
            st.info("לא נמצאו עבודות תמלול בתאריך שנבחר.")

    # ---------------------------------------------------------
    # TAB 3: Cards & Management Tools View
    # ---------------------------------------------------------
    with tab3:
        st.subheader("כלי ניהול ותצוגת כרטיסיות")
        
        col_search, col_export, col_view = st.columns([3, 1, 1])
        
        with col_search:
            search_term = st.text_input("חיפוש חופשי (לפי שם קובץ, מזהה או משתמש):", "")
        
        with col_export:
            st.markdown("<br>", unsafe_allow_html=True)
            csv_data = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="הורדת דוח CSV",
                data=csv_data,
                file_name=f"transcription_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )
            
        with col_view:
            st.markdown("<br>", unsafe_allow_html=True)
            toggle_table = st.checkbox("התמקד בתצוגת טבלה מלאה", value=False)

        # Apply search filter
        df_filtered = df.copy()
        if search_term:
            df_filtered = df_filtered[
                df_filtered['filename'].astype(str).str.contains(search_term, case=False, na=False) |
                df_filtered['job_id'].astype(str).str.contains(search_term, case=False, na=False) |
                df_filtered['user_principal'].astype(str).str.contains(search_term, case=False, na=False)
            ]

        st.markdown("---")

        if toggle_table:
            st.dataframe(df_filtered, use_container_width=True, hide_index=True)
        else:
            st.write(f"מציג **{len(df_filtered)}** עבודות תמלול:")
            
            for idx, job in df_filtered.iterrows():
                with st.container():
                    card_title = f"{job['filename']} | משתמש: {job['user_principal']} | תאריך: {job['started_at'].strftime('%Y-%m-%d %H:%M')}"
                    
                    with st.expander(card_title, expanded=False):
                        mc1, mc2, mc3, mc4 = st.columns(4)
                        
                        mc1.metric("אורך הקלטה", f"{(job['audio_duration_seconds']/60):.1f} דק'")
                        mc2.metric("זמן עיבוד כולל", f"{job['total_processing_seconds']} שנ'")
                        mc3.metric("עלות משוערת", f"${job['estimated_total_cost_usd']:.4f}")
                        mc4.metric("פריטי PII שהותממו", int(job['sensitive_data_total']))
                        
                        st.markdown("---")
                        
                        sub_col1, sub_col2 = st.columns(2)
                        with sub_col1:
                            st.write(f"**מזהה עבודה:** `{job['job_id']}`")
                            st.write(f"**זמן תמלול מקומי:** {job['transcription_seconds']} שניות")
                            st.write(f"**זמן עיבוד Gemini:** {job['gemini_processing_seconds']} שניות")
                            st.write(f"**סטטוס:** `{job['status']}`")
                        
                        with sub_col2:
                            st.write(f"**Tokens קלט/פלט:** {job['input_tokens']:,} / {job['output_tokens']:,}")
                            st.write(f"**Thinking Tokens:** {job['thinking_tokens']:,}")
                            st.write(f"**סה\"כ Tokens:** {job['total_tokens']:,}")

else:
    st.info("לא נמצאו נתונים עבור המסננים שנבחרו.")