import streamlit as st
import calendar
from datetime import date, timedelta
from supabase import create_client

st.set_page_config(page_title="Tracker", layout="centered")
st.title("Skincare Tracker")

# --- SUPABASE CONNECTION ---
SUPABASE_URL = "https://czydbiqjaljhcakubnrb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImN6eWRiaXFqYWxqaGNha3VibnJiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc3NDMyMTAsImV4cCI6MjA5MzMxOTIxMH0.S25Tq_TclBl1MX_SenTw-QyJbkEFIzU3wBOCqcz5cbs"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- logic ---
def get_current_pause(p):
    days_since_start = (date.today() - p["start_date"]).days
    if days_since_start >= p["phase_change_after"]:
        return p["new_pause_days"]
    return p["pause_days"]

def get_products():
    return supabase.table("products").select("*").execute().data

def add_product(p):
    supabase.table("products").insert(p).execute()

def get_usage(name):
    res = supabase.table("usage").select("*").eq("product", name).execute()
    return [date.fromisoformat(x["used_on"]) for x in res.data]

def add_usage(name):
    supabase.table("usage").insert({
        "product": name,
        "used_on": date.today().isoformat()
    }).execute()

def get_next_allowed(p, usage):
    if not usage:
        return date.today()
    return max(usage) + timedelta(days=get_current_pause(p))

# --- add product ---
with st.expander("Add product"):
    name = st.text_input("Name")
    pause = st.number_input("Pause days", 1, 10, 3)
    phase = st.number_input("Change after days", 0, 365, 90)
    new_pause = st.number_input("New pause days", 1, 10, 2)

    if st.button("Add product"):
        add_product({
            "name": name,
            "pause_days": pause,
            "start_date": date.today().isoformat(),
            "phase_change_after": phase,
            "new_pause_days": new_pause
        })
        st.success("Saved")
        st.rerun()

# --- load products ---
products = get_products()

if products:
    names = [p["name"] for p in products]
    selected = st.selectbox("Select product", names)

    row = next(p for p in products if p["name"] == selected)

    p = {
        "name": row["name"],
        "pause_days": row["pause_days"],
        "start_date": date.fromisoformat(row["start_date"]),
        "phase_change_after": row["phase_change_after"],
        "new_pause_days": row["new_pause_days"]
    }

    usage = get_usage(selected)
    next_day = get_next_allowed(p, usage)

    if st.button("Used today"):
        add_usage(selected)
        st.rerun()

    # display
    weekday = next_day.strftime("%A")
    formatted = next_day.strftime("%d %B %Y")

    st.subheader(selected)
    st.write(f"Next allowed: {weekday}, {formatted}")

    if date.today() >= next_day:
        st.success("You can use it today")
    else:
        st.warning(f"Wait {(next_day - date.today()).days} days")

    st.write("History:", usage)

    # --- calendar ---
    st.subheader("Monthly view")

    today = date.today()
    cal = calendar.monthcalendar(today.year, today.month)

    for week in cal:
        cols = st.columns(7)
        for i, day in enumerate(week):
            if day == 0:
                cols[i].write("")
            else:
                d = date(today.year, today.month, day)

                if d in usage:
                    cols[i].success(str(day))
                elif d == next_day:
                    cols[i].warning(str(day))
                else:
                    cols[i].write(str(day))

    # settings
    with st.expander("Settings"):
        st.write(f"Pause days: {p['pause_days']}")
        st.write(f"Change after: {p['phase_change_after']}")
        st.write(f"New pause: {p['new_pause_days']}")
        st.write(f"Start: {p['start_date']}")

else:
    st.info("Add your first product")