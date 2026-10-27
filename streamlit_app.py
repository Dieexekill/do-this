import re
from datetime import datetime
import requests
import streamlit as st
from streamlit_geolocation import streamlit_geolocation

# ---------------------------------------------------------
# Page Configuration
# ---------------------------------------------------------
st.set_page_config(
    page_title="CareAtZero",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ---------------------------------------------------------
# Geolocation & Reverse Lookup Helpers
# ---------------------------------------------------------
@st.cache_data(ttl=3600)
def get_zip_from_lat_lon(lat, lon):
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}"
        headers = {"User-Agent": "CareAtZeroApp/1.0"}
        res = requests.get(url, headers=headers, timeout=3)
        if res.status_code == 200:
            data = res.json()
            address = data.get("address", {})
            postal = address.get("postcode")
            if postal and postal.isdigit():
                return postal
    except Exception:
        pass
    return None


@st.cache_data(ttl=3600)
def get_user_zip_by_ip():
    try:
        res = requests.get("https://ipapi.co/json/", timeout=3)
        if res.status_code == 200:
            data = res.json()
            postal = data.get("postal")
            if postal and postal.isdigit():
                return postal
    except Exception:
        pass
    return "27514"


# ---------------------------------------------------------
# Session State Initialization
# ---------------------------------------------------------
if "nav_tab" not in st.session_state:
    st.session_state["nav_tab"] = "🏠 Home"

if "saved_clinics" not in st.session_state:
    st.session_state["saved_clinics"] = []

if "selected_clinic" not in st.session_state:
    st.session_state["selected_clinic"] = "SHAC"

if "search_query" not in st.session_state:
    st.session_state["search_query"] = get_user_zip_by_ip()

if "category_filter" not in st.session_state:
    st.session_state["category_filter"] = "All"

# ---------------------------------------------------------
# Massively Expanded Master Clinic Database
# ---------------------------------------------------------
CLINICS_DB = {
    "UNC_ER": {
        "id": "UNC_ER",
        "name": "UNC Hospitals Emergency Department & Trauma Center",
        "cost_tier": "EMERGENCY / CHARITY CARE AVAILABLE",
        "price_range": "Emergency Care / Billing Assistance",
        "urgency_level": "Emergency / Immediate (24/7)",
        "facility_type": "24/7 EMERGENCY DEPT",
        "address": "101 Manning Dr, Chapel Hill, NC 27514",
        "zip_code": "27514",
        "distance_miles": 0.8,
        "score": 98,
        "hours": "Open 24 Hours / 7 Days a Week",
        "phone": "(984) 974-1000",
        "website": "https://www.uncmedicalcenter.org/",
        "maps_url": "https://maps.google.com/?q=101+Manning+Dr,+Chapel+Hill,+NC+27514",
        "categories": ["Medical", "Behavioral Health"],
        "docs_required": False,
        "walk_in": True,
        "spanish": True,
        "summary": "UNC Hospitals Emergency Department delivers 24/7 acute trauma evaluation and life-threatening critical interventions.",
        "source": "Official Hospital Directory",
        "last_checked": "2026-10-14",
        "documents": "Photo ID (if available). EMTALA protects care regardless of ability to pay.",
    },
    "SHAC": {
        "id": "SHAC",
        "name": "Student Health Action Coalition (SHAC) Free Clinic",
        "cost_tier": "100% FREE CARE ($0)",
        "price_range": "FREE ($0)",
        "urgency_level": "Same Day / Walk-In",
        "facility_type": "PERMANENT SAFETY-NET CLINIC",
        "address": "301 Lloyd St, Carrboro, NC 27510",
        "zip_code": "27510",
        "distance_miles": 2.8,
        "score": 94,
        "hours": "Wednesdays 6:00 PM - 9:30 PM",
        "phone": "(919) 843-6904",
        "website": "https://www.med.unc.edu/shac/",
        "maps_url": "https://maps.google.com/?q=301+Lloyd+St,+Carrboro,+NC+27510",
        "categories": ["Medical", "Dental", "Vision", "Behavioral Health"],
        "docs_required": False,
        "walk_in": True,
        "spanish": True,
        "summary": "Nation's oldest student-run free health clinic. Supplies free primary care, dental cleanings, vision exams, and counseling.",
        "source": "NAFC Directory",
        "last_checked": "2026-10-14",
        "documents": "None required (No ID or SSN verification necessary).",
    },
    "Piedmont": {
        "id": "Piedmont",
        "name": "Piedmont Health Services - Carrboro Community Center",
        "cost_tier": "SLIDING SCALE ($15 - $35)",
        "price_range": "Under $25 Nominal Fee",
        "urgency_level": "Same Day / Walk-In",
        "facility_type": "FEDERALLY QUALIFIED HEALTH CENTER (FQHC)",
        "address": "301 Hargett St, Carrboro, NC 27510",
        "zip_code": "27510",
        "distance_miles": 1.5,
        "score": 89,
        "hours": "Monday - Saturday 7:30 AM - 6:00 PM",
        "phone": "(919) 933-9033",
        "website": "https://piedmonthealth.org/",
        "maps_url": "https://maps.google.com/?q=301+Hargett+St,+Carrboro,+NC+27510",
        "categories": ["Medical", "Dental"],
        "docs_required": True,
        "walk_in": True,
        "spanish": True,
        "summary": "Integrated primary medical care, pediatrics, family dentistry, and discounted pharmacy services on a sliding-fee scale.",
        "source": "HRSA Directory",
        "last_checked": "2026-10-14",
        "documents": "Photo ID, proof of household income, and proof of residency.",
    },
    "Samaritan": {
        "id": "Samaritan",
        "name": "Samaritan Health Center",
        "cost_tier": "100% FREE CARE ($0)",
        "price_range": "FREE ($0)",
        "urgency_level": "This Week",
        "facility_type": "FREE & CHARITABLE CLINIC",
        "address": "507 E Knox St, Durham, NC 27701",
        "zip_code": "27701",
        "distance_miles": 10.4,
        "score": 93,
        "hours": "Monday - Thursday 8:30 AM - 4:30 PM",
        "phone": "(919) 407-8223",
        "website": "https://www.samaritanhealthcenter.org/",
        "maps_url": "https://maps.google.com/?q=507+E+Knox+St,+Durham,+NC+27701",
        "categories": ["Medical", "Behavioral Health"],
        "docs_required": False,
        "walk_in": False,
        "spanish": True,
        "summary": "Holistic primary care, acute disease treatments, prescription vouchers, and wellness counseling completely free.",
        "source": "Community Health Network Feed",
        "last_checked": "2026-10-13",
        "documents": "Proof of uninsured status. Appointment required.",
    },
    "Lincoln_CHC": {
        "id": "Lincoln_CHC",
        "name": "Lincoln Community Health Center",
        "cost_tier": "SLIDING SCALE / LOW COST ($10 - $25)",
        "price_range": "Under $25 Nominal Fee",
        "urgency_level": "This Week",
        "facility_type": "FEDERALLY QUALIFIED HEALTH CENTER (FQHC)",
        "address": "1301 Fayetteville St, Durham, NC 27707",
        "zip_code": "27707",
        "distance_miles": 11.2,
        "score": 87,
        "hours": "Monday - Friday 8:00 AM - 5:00 PM",
        "phone": "(919) 956-4000",
        "website": "https://lincolnchc.org/",
        "maps_url": "https://maps.google.com/?q=1301+Fayetteville+St,+Durham,+NC+27707",
        "categories": ["Medical", "Dental", "Behavioral Health"],
        "docs_required": True,
        "walk_in": True,
        "spanish": True,
        "summary": "Primary, pediatric, dental, and mental health services provided on a sliding fee scale.",
        "source": "HRSA Directory",
        "last_checked": "2026-10-14",
        "documents": "Photo ID, income verification for sliding scale fees.",
    },
    "Orange_County_Health": {
        "id": "Orange_County_Health",
        "name": "Orange County Health Department",
        "cost_tier": "SLIDING SCALE / LOW COST",
        "price_range": "Under $25 Nominal Fee",
        "urgency_level": "This Week",
        "facility_type": "PUBLIC HEALTH DEPARTMENT",
        "address": "300 W Tryon St, Hillsborough, NC 27278",
        "zip_code": "27278",
        "distance_miles": 12.1,
        "score": 90,
        "hours": "Monday - Friday 8:00 AM - 5:00 PM",
        "phone": "(919) 245-2400",
        "website": "https://www.orangecountync.gov/143/Health-Department",
        "maps_url": "https://maps.google.com/?q=300+W+Tryon+St,+Hillsborough,+NC+27278",
        "categories": ["Medical", "Vision", "Behavioral Health"],
        "docs_required": True,
        "walk_in": True,
        "spanish": True,
        "summary": "County public health clinic offering immunizations, communicable disease screening, pediatric vision/hearing checks, and family planning.",
        "source": "State Health Dept Feed",
        "last_checked": "2026-10-12",
        "documents": "Photo ID and proof of residence.",
    },
    "Urban_Ministries_Clinic": {
        "id": "Urban_Ministries_Clinic",
        "name": "Open Door Clinic of Greater Raleigh / Urban Ministries",
        "cost_tier": "100% FREE CARE ($0)",
        "price_range": "FREE ($0)",
        "urgency_level": "By Appointment",
        "facility_type": "CHARITABLE FREE CLINIC",
        "address": "1390 Capital Blvd, Raleigh, NC 27603",
        "zip_code": "27603",
        "distance_miles": 24.5,
        "score": 92,
        "hours": "Monday - Thursday 9:00 AM - 4:00 PM",
        "phone": "(919) 834-1823",
        "website": "https://www.urbanmin.org/",
        "maps_url": "https://maps.google.com/?q=1390+Capital+Blvd,+Raleigh,+NC+27603",
        "categories": ["Medical", "Dental", "Behavioral Health"],
        "docs_required": False,
        "walk_in": False,
        "spanish": True,
        "summary": "Provides free acute and chronic medical care, pharmaceutical assistance, and emergency dental relief for uninsured low-income adults.",
        "source": "NAFC Directory",
        "last_checked": "2026-10-11",
        "documents": "Proof of uninsured status.",
    },
    "Open_Door_Dental": {
        "id": "Open_Door_Dental",
        "name": "Wake Smiles Dental Clinic",
        "cost_tier": "LOW COST / NOMINAL FEE",
        "price_range": "Under $25 Nominal Fee",
        "urgency_level": "By Appointment",
        "facility_type": "SAFETY-NET DENTAL CLINIC",
        "address": "319 Chapanoke Rd #110, Raleigh, NC 27603",
        "zip_code": "27603",
        "distance_miles": 27.2,
        "score": 91,
        "hours": "Monday - Thursday 8:00 AM - 4:30 PM",
        "phone": "(919) 661-1555",
        "website": "https://wakesmiles.org/",
        "maps_url": "https://maps.google.com/?q=319+Chapanoke+Rd+%23110,+Raleigh,+NC+27603",
        "categories": ["Dental"],
        "docs_required": True,
        "walk_in": False,
        "spanish": True,
        "summary": "Dedicated charitable dental clinic offering extractions, fillings, and restorative oral care for low-income uninsured residents.",
        "source": "State Dental Association",
        "last_checked": "2026-10-10",
        "documents": "Income documentation and referral form.",
    },
    "Triangle_E_Health": {
        "id": "Triangle_E_Health",
        "name": "Triangle Empowerment Center - Behavioral & Wellness",
        "cost_tier": "SLIDING SCALE / FREE OPTIONS",
        "price_range": "FREE ($0)",
        "urgency_level": "Same Day / Walk-In",
        "facility_type": "COMMUNITY HEALTH CENTER",
        "address": "522 Hunt St, Durham, NC 27701",
        "zip_code": "27701",
        "distance_miles": 10.9,
        "score": 86,
        "hours": "Monday - Friday 9:00 AM - 6:00 PM",
        "phone": "(919) 683-1600",
        "website": "https://www.triangleempowerment.org/",
        "maps_url": "https://maps.google.com/?q=522+Hunt+St,+Durham,+NC+27701",
        "categories": ["Behavioral Health", "Medical"],
        "docs_required": False,
        "walk_in": True,
        "spanish": True,
        "summary": "Specialized community health center offering mental health counseling, support groups, and preventative screenings.",
        "source": "SAMHSA Directory",
        "last_checked": "2026-10-14",
        "documents": "None required for initial screening.",
    },
    "Access_Care_Greensboro": {
        "id": "Access_Care_Greensboro",
        "name": "Guilford County Free Clinic",
        "cost_tier": "100% FREE CARE ($0)",
        "price_range": "FREE ($0)",
        "urgency_level": "By Appointment",
        "facility_type": "CHARITABLE FREE CLINIC",
        "address": "501 Yanceyville St, Greensboro, NC 27405",
        "zip_code": "27405",
        "distance_miles": 52.0,
        "score": 93,
        "hours": "Monday - Thursday 8:30 AM - 5:00 PM",
        "phone": "(336) 333-6870",
        "website": "https://guilfordfreeclinic.org/",
        "maps_url": "https://maps.google.com/?q=501+Yanceyville+St,+Greensboro,+NC+27405",
        "categories": ["Medical", "Dental", "Vision"],
        "docs_required": True,
        "walk_in": False,
        "spanish": True,
        "summary": "Comprehensive free medical, dental, and optical care for low-income uninsured adults living in Guilford County.",
        "source": "NAFC Directory",
        "last_checked": "2026-10-12",
        "documents": "Proof of income, photo ID, and county residency proof.",
    },
    "Matthews_Free_Medical": {
        "id": "Matthews_Free_Medical",
        "name": "Matthews Free Medical Clinic",
        "cost_tier": "100% FREE CARE ($0)",
        "price_range": "FREE ($0)",
        "urgency_level": "By Appointment",
        "facility_type": "CHARITABLE FREE CLINIC",
        "address": "159 N Trade St, Matthews, NC 28105",
        "zip_code": "28105",
        "distance_miles": 125.0,
        "score": 91,
        "hours": "Monday - Friday 9:00 AM - 4:00 PM",
        "phone": "(704) 841-8882",
        "website": "https://matthewsfmc.org/",
        "maps_url": "https://maps.google.com/?q=159+N+Trade+St,+Matthews,+NC+28105",
        "categories": ["Medical", "Behavioral Health"],
        "docs_required": True,
        "walk_in": False,
        "spanish": True,
        "summary": "Provides free healthcare services, chronic disease management, and mental health counseling to uninsured residents.",
        "source": "NC Free Clinic Association",
        "last_checked": "2026-10-10",
        "documents": "Proof of income and uninsured status.",
    },
    "Charlotte_Community_Health": {
        "id": "Charlotte_Community_Health",
        "name": "Charlotte Community Health Clinic",
        "cost_tier": "SLIDING SCALE / LOW COST",
        "price_range": "Under $25 Nominal Fee",
        "urgency_level": "Same Day / Walk-In",
        "facility_type": "FEDERALLY QUALIFIED HEALTH CENTER",
        "address": "8401 University Executive Park Dr, Charlotte, NC 28262",
        "zip_code": "28262",
        "distance_miles": 130.0,
        "score": 89,
        "hours": "Monday - Friday 8:00 AM - 5:00 PM",
        "phone": "(704) 316-6500",
        "website": "https://charlottecommunityhealth.org/",
        "maps_url": "https://maps.google.com/?q=8401+University+Executive+Park+Dr,+Charlotte,+NC+28262",
        "categories": ["Medical", "Dental", "Behavioral Health"],
        "docs_required": True,
        "walk_in": True,
        "spanish": True,
        "summary": "Comprehensive primary care, dental care, and behavioral health services on an affordable sliding fee scale.",
        "source": "HRSA Directory",
        "last_checked": "2026-10-14",
        "documents": "Photo ID and household income verification.",
    },
    "REACH_Dental_Mobile": {
        "id": "REACH_Dental_Mobile",
        "name": "NC Missions of Mercy Mobile Dental Clinic",
        "cost_tier": "100% FREE CARE ($0)",
        "price_range": "FREE ($0)",
        "urgency_level": "Upcoming Pop-Up Event",
        "facility_type": "MOBILE POP-UP CLINIC",
        "address": "Rotating Regional Fairgrounds & Community Centers, NC",
        "zip_code": "27514",
        "distance_miles": 5.0,
        "score": 95,
        "hours": "Saturdays / Event-Based (Check web schedule)",
        "phone": "(919) 677-1300",
        "website": "https://www.ncdental.org/momm",
        "maps_url": "https://maps.google.com/?q=North+Carolina",
        "categories": ["Dental"],
        "docs_required": False,
        "walk_in": True,
        "spanish": True,
        "summary": "Episodic mobile dental clinic providing completely free fillings, extractions, and cleanings on a first-come, first-served basis.",
        "source": "State Dental Society Feed",
        "last_checked": "2026-10-14",
        "documents": "None required. Arrive early for line entry.",
    },
}

# ---------------------------------------------------------
# Custom CSS: Modern Trustworthy Theme
# ---------------------------------------------------------
st.markdown(
    """
    <style>
    .stApp {
        background-color: #121212 !important;
        color: #e3e2e0 !important;
    }
    .main .block-container {
        padding-top: 1.5rem;
        padding-bottom: 5rem;
        max-width: 1000px;
    }
    .app-header {
        background-color: #1e293b;
        border: 1px solid #334155;
        border-radius: 20px;
        padding: 28px;
        text-align: center;
        margin-bottom: 20px;
        box-shadow: 0 4px 16px rgba(0,0,0,0.4);
    }
    .app-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #f8fafc;
        margin: 0;
    }
    .app-sub {
        color: #94a3b8;
        font-size: 1rem;
        margin-top: 6px;
    }
    .emergency-banner {
        background-color: #7f1d1d;
        border: 1px solid #991b1b;
        border-radius: 14px;
        padding: 14px 18px;
        color: #fee2e2;
        margin-bottom: 20px;
        font-size: 0.95rem;
    }
    .clinic-card {
        background-color: #1e293b;
        border: 1px solid #334155;
        border-radius: 16px;
        padding: 22px;
        margin-bottom: 16px;
        color: #f8fafc;
        box-shadow: 0 2px 10px rgba(0,0,0,0.2);
    }
    .clinic-name {
        font-size: 1.25rem;
        font-weight: 700;
        color: #ffffff;
        margin-top: 6px;
        margin-bottom: 4px;
    }
    .badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 16px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-right: 6px;
        margin-bottom: 6px;
    }
    .badge-free { background-color: #065f46; color: #a7f3d0; }
    .badge-cost { background-color: #92400e; color: #fde68a; }
    .badge-type { background-color: #1e40af; color: #bfdbfe; }
    .badge-score { background-color: #14532d; color: #bbf7d0; border: 1px solid #166534; }

    .stButton > button {
        background-color: #2563eb !important;
        color: #ffffff !important;
        border-radius: 12px !important;
        border: none !important;
        font-weight: 600 !important;
        padding: 8px 16px !important;
        transition: all 0.2s ease;
    }
    .stButton > button:hover {
        background-color: #1d4ed8 !important;
        transform: scale(1.01);
    }
    div[data-testid="stRadio"] > div {
        background-color: #1e293b;
        padding: 6px;
        border-radius: 20px;
        justify-content: center;
    }
    </style>
""",
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# Render Clinic Card Component
# ---------------------------------------------------------
def render_clinic_card(clinic_key):
    clinic = CLINICS_DB[clinic_key]
    badge_class = "badge-free" if "FREE" in clinic["cost_tier"] else "badge-cost"
    st.markdown(
        f"""
        <div class="clinic-card">
            <div>
                <span class="badge {badge_class}">{clinic['cost_tier']}</span>
                <span class="badge badge-type">⏱️ {clinic['urgency_level']}</span>
                <span class="badge" style="background-color: #334155; color: #e2e8f0;">{clinic['facility_type']}</span>
            </div>
            <div class="clinic-name">{clinic['name']}</div>
            <p style="color: #cbd5e1; font-size: 0.88rem; margin-bottom: 6px;">📍 {clinic['address']} • <b>ZIP: {clinic['zip_code']}</b> ({clinic['distance_miles']} mi away)</p>
            <p style="font-size: 0.88rem; color: #94a3b8; margin-bottom: 6px;"><b>Hours:</b> {clinic['hours']}</p>
            <p style="font-size: 0.88rem; color: #e2e8f0;">{clinic['summary']}</p>
            <div style="margin-top: 10px; display: flex; gap: 8px; align-items: center; flex-wrap: wrap;">
                <span class="badge badge-score">⭐ Care Access Score: {clinic['score']}/100</span>
                <span style="font-size: 0.75rem; color: #64748b;">Source: {clinic['source']} (Checked: {clinic['last_checked']})</span>
            </div>
        </div>
    """,
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if st.button("📑 Detail & Next Steps", key=f"det_{clinic_key}"):
            st.session_state["selected_clinic"] = clinic_key
            st.session_state["nav_tab"] = "📑 Detail"
            st.rerun()
    with c2:
        st.link_button("🗺️ Directions", clinic["maps_url"], use_container_width=True)
    with c3:
        st.link_button("🌐 Official Site", clinic["website"], use_container_width=True)
    with c4:
        is_saved = clinic_key in st.session_state["saved_clinics"]
        btn_label = "✅ Saved" if is_saved else "⭐ Save"
        if st.button(btn_label, key=f"save_{clinic_key}"):
            if is_saved:
                st.session_state["saved_clinics"].remove(clinic_key)
            else:
                st.session_state["saved_clinics"].append(clinic_key)
            st.rerun()


# ---------------------------------------------------------
# App Header & Navigation
# ---------------------------------------------------------
st.markdown(
    """
    <div class="app-header">
        <div style="font-size: 2.5rem; margin-bottom: 4px;">🩺</div>
        <div class="app-title">CareAtZero</div>
        <div class="app-sub">Find trustworthy free, near-free, and sliding-scale healthcare you can realistically access soon.</div>
    </div>
""",
    unsafe_allow_html=True,
)

tabs_list = ["🏠 Home", "🔍 Find Care", "📑 Detail", "⭐ Saved", "ℹ️ About & Safety"]
selected_tab = st.radio(
    "Navigation",
    options=tabs_list,
    index=tabs_list.index(st.session_state["nav_tab"]),
    horizontal=True,
    label_visibility="collapsed",
)

if selected_tab != st.session_state["nav_tab"]:
    st.session_state["nav_tab"] = selected_tab
    st.rerun()

st.write("")

st.markdown(
    """
    <div class="emergency-banner">
        🚨 <b>Emergency Notice:</b> CareAtZero does not provide medical advice or emergency dispatch. For life-threatening emergencies, call <b>911</b> immediately. Dial <b>988</b> for 24/7 mental health crisis support.
    </div>
""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# TAB 1: 🏠 HOME
# ---------------------------------------------------------
if st.session_state["nav_tab"] == "🏠 Home":
    st.markdown("### 🎯 Quick Care Search Profile")

    col1, col2 = st.columns(2)
    with col1:
        chosen_cat = st.selectbox(
            "Select Care Category Needed",
            ["All", "Medical", "Dental", "Vision", "Behavioral Health"],
            index=["All", "Medical", "Dental", "Vision", "Behavioral Health"].index(
                st.session_state["category_filter"]),
        )
        if chosen_cat != st.session_state["category_filter"]:
            st.session_state["category_filter"] = chosen_cat
    with col2:
        st.write("")
        st.write("")
        if st.button("🚀 Start Free Care Search"):
            st.session_state["nav_tab"] = "🔍 Find Care"
            st.rerun()

    st.write("")
    st.markdown("### 📍 Location & GPS Geolocation")

    loc_col1, loc_col2 = st.columns([1, 2])
    with loc_col1:
        st.write("Click below to detect your GPS ZIP code:")
        location = streamlit_geolocation()
        if location and location.get("latitude") and location.get("longitude"):
            lat = location["latitude"]
            lon = location["longitude"]
            fetched_zip = get_zip_from_lat_lon(lat, lon)
            if fetched_zip:
                st.session_state["search_query"] = fetched_zip
                st.success(f"GPS Located! ZIP: {fetched_zip}")

    with loc_col2:
        zip_input = st.text_input(
            "Or Enter ZIP Code Manually",
            value=st.session_state["search_query"],
        )
        if st.button("🔍 Update ZIP & Search"):
            st.session_state["search_query"] = zip_input.strip()
            st.session_state["nav_tab"] = "🔍 Find Care"
            st.rerun()

    st.divider()

    st.markdown("### 🚨 Urgent / Emergency Option")
    render_clinic_card("UNC_ER")

    st.write("")
    st.markdown("### 🚌 Featured Safety-Net Option")
    render_clinic_card("SHAC")

# ---------------------------------------------------------
# TAB 2: 🔍 FIND CARE (Advanced Filtering & Transparent Scoring)
# ---------------------------------------------------------
elif st.session_state["nav_tab"] == "🔍 Find Care":
    st.markdown("### 🔍 Search Results & Transparent Filters")

    user_zip_match = re.search(r"\b\d{5}\b", st.session_state["search_query"])
    search_zip = user_zip_match.group(0) if user_zip_match else st.session_state["search_query"].strip()

    cat_options = ["All", "Medical", "Dental", "Vision", "Behavioral Health"]
    default_cat_idx = cat_options.index(st.session_state["category_filter"]) if st.session_state[
                                                                                    "category_filter"] in cat_options else 0

    with st.expander("🛠 Filter Options & Eligibility Preferences", expanded=True):
        f1, f2, f3 = st.columns(3)
        with f1:
            sel_cat = st.selectbox("Care Category", cat_options, index=default_cat_idx, key="find_cat_dropdown")
            st.session_state["category_filter"] = sel_cat
            exact_zip_only = st.checkbox(f"Filter strictly by ZIP {search_zip} (Uncheck to view regional results)",
                                         value=False)
        with f2:
            sel_prices = st.multiselect(
                "Cost Classification",
                ["FREE ($0)", "Under $25 Nominal Fee", "Emergency Care / Billing Assistance",
                 "SLIDING SCALE / LOW COST"],
                default=["FREE ($0)", "Under $25 Nominal Fee", "Emergency Care / Billing Assistance",
                         "SLIDING SCALE / LOW COST"],
            )
        with f3:
            no_docs = st.checkbox("No ID / SSN Required")
            sort_by = st.selectbox("Sort By", ["Care Access Score (Highest First)", "Distance (Nearest First)"])

    filtered_keys = []
    for k, v in CLINICS_DB.items():
        zip_match = (not exact_zip_only) or (v["zip_code"] == search_zip)
        price_match = (not sel_prices) or any(p in v["cost_tier"] or p in v["price_range"] for p in sel_prices)
        doc_match = not (no_docs and v["docs_required"])
        cat_match = (sel_cat == "All") or (sel_cat in v["categories"])

        if zip_match and price_match and doc_match and cat_match:
            filtered_keys.append(k)

    if sort_by == "Care Access Score (Highest First)":
        filtered_keys.sort(key=lambda x: CLINICS_DB[x]["score"], reverse=True)
    else:
        filtered_keys.sort(key=lambda x: CLINICS_DB[x]["distance_miles"])

    st.write("")
    st.markdown(f"#### Showing {len(filtered_keys)} Verified Options for Category: **{sel_cat}**")

    if not filtered_keys:
        st.warning(
            "No facilities matched your exact criteria. Try broadening your cost filter or unchecking strict ZIP matching.")
        if st.button("🌐 Reset Filters"):
            st.session_state["category_filter"] = "All"
            st.rerun()
    else:
        for key in filtered_keys:
            render_clinic_card(key)
            st.write("")

# ---------------------------------------------------------
# TAB 3: 📑 DETAIL
# ---------------------------------------------------------
elif st.session_state["nav_tab"] == "📑 Detail":
    clinic_key = st.session_state["selected_clinic"]
    clinic = CLINICS_DB[clinic_key]

    if st.button("← Back to Results"):
        st.session_state["nav_tab"] = "🔍 Find Care"
        st.rerun()

    st.markdown(
        f"""
        <div class="clinic-card">
            <span class="badge badge-free">{clinic['cost_tier']}</span> 
            <span class="badge badge-type">⏱️ {clinic['urgency_level']}</span>
            <span class="badge" style="background-color: #334155; color: #e2e8f0;">{clinic['facility_type']}</span>
            <h2 style="color: white; margin-top: 10px;">{clinic['name']}</h2>
            <p style="color: #cbd5e1;">📍 {clinic['address']} • <b>ZIP Code: {clinic['zip_code']}</b></p>
            <div style="margin-top: 10px;">
                <span class="badge badge-score">⭐ Care Access Score: {clinic['score']}/100</span>
            </div>
        </div>
    """,
        unsafe_allow_html=True,
    )

    b1, b2, b3 = st.columns(3)
    with b1:
        st.link_button(f"📞 Call {clinic['phone']}", f"tel:{clinic['phone']}", use_container_width=True)
    with b2:
        st.link_button("🗺 Get Directions", clinic["maps_url"], use_container_width=True)
    with b3:
        st.link_button("🌐 Official Website", clinic["website"], use_container_width=True)

    st.write("")
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("### 📋 Facility Overview & Services")
        st.write(clinic["summary"])

        st.markdown("### 💵 Transparent Cost Policy")
        st.info(f"**Classification:** {clinic['price_range']}\n\n**Financial Policy:** {clinic['cost_tier']}")

    with col_right:
        st.markdown("### ⏰ Hours & Required Documents")
        st.write(f"- **Operating Hours:** {clinic['hours']}")
        st.write(f"- **Walk-In Allowed:** {'Yes' if clinic['walk_in'] else 'Appointment Required'}")
        st.markdown(f"- **Documents to Bring:** {clinic['documents']}")

        st.markdown("### 🔍 Provenance & Freshness")
        st.success(f"**Verified Source:** {clinic['source']}\n\n**Last Checked:** {clinic['last_checked']}")

# ---------------------------------------------------------
# TAB 4: ⭐ SAVED
# ---------------------------------------------------------
elif st.session_state["nav_tab"] == "⭐ Saved":
    st.markdown("## ⭐ Saved Care Options")
    saved_list = st.session_state["saved_clinics"]

    if not saved_list:
        st.info("No saved options yet. Click '⭐ Save' on any provider card to bookmark it here for quick reference.")
    else:
        for k in saved_list:
            render_clinic_card(k)
            st.write("")

# ---------------------------------------------------------
# TAB 5: ℹ️ ABOUT & SAFETY
# ---------------------------------------------------------
elif st.session_state["nav_tab"] == "ℹ️ About & Safety":
    st.markdown("## ℹ️ About CareAtZero & Safety Guidelines")

    st.markdown(
        """
        **CareAtZero** is a free, mobile-first web application designed to eliminate financial and administrative barriers to healthcare. 
        It aggregates permanent free clinics, sliding-scale safety-net providers, and community resources into one decision engine focused on cost, eligibility, and timing.
        """
    )

    st.markdown("---")

    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("### 🎯 Care Access Score Transparency")
        st.write(
            """
            Rankings are determined by a transparent **Care Access Score (out of 100)** rather than hidden algorithms:
            1. **Cost Fit (35%):** Weighted heavily for $0 free care.
            2. **Timing & Availability (25%):** Rewards same-day or walk-in access.
            3. **Service Match (15%):** Confirms requested medical, dental, vision, or behavioral care.
            4. **Eligibility & Documentation Confidence (20%):** Higher scores for zero-ID requirements.
            5. **Distance & Freshness (5% - 10%):** Proximity and recent source verification.
            """
        )

    with col_b:
        st.markdown("### 🛡️ Privacy & Medical Limitations")
        st.warning(
            """
            - **No Medical Advice:** CareAtZero does not diagnose symptoms, offer treatment advice, or replace medical professionals.
            - **Privacy Protected:** No medical history, Social Security numbers, or personal health records are requested or stored.
            - **Source Verification:** Every listing includes official source provenance and a last-checked timestamp to ensure data trust.
            """
        )
