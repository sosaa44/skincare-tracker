import streamlit as st
import calendar
from datetime import date, timedelta

st.set_page_config(page_title="Tracker", layout="centered")
st.title("Skincare Tracker")

# --- init state ---
if "products" not in st.session_state:
    st.session_state.products = {}

# --- logic ---
def get_current_pause(p):
    days_since_start = (date.today() - p["start_date"]).days
    if days_since_start >= p["phase_change_after"]:
        return p["new_pause_days"]
    return p["pause_days"]

def get_next_allowed(p):
    if not p["usage"]:
        return date.today()
    last_used = max(p["usage"])
    return last_used + timedelta(days=get_current_pause(p))

# --- add product ---
with st.expander("Add product"):
    name = st.text_input("Name")
    pause = st.number_input("Pause days", 1, 10, 3)
    phase = st.number_input("Change after days", 0, 365, 90)
    new_pause = st.number_input("New pause days", 1, 10, 2)

    if st.button("Add product"):
        st.session_state.products[name] = {
            "name": name,
            "pause_days": pause,
            "start_date": date.today(),
            "phase_change_after": phase,
            "new_pause_days": new_pause,
            "usage": []
        }

# --- main UI ---
if st.session_state.products:
    selected = st.selectbox("Select product", list(st.session_state.products.keys()))
    p = st.session_state.products[selected]

    next_day = get_next_allowed(p)

    # --- usage button (ONLY ONCE) ---
    if st.button("Used today"):
        today = date.today()
        p["usage"].append(today)

        if today < next_day:
            st.error("Used earlier than planned — schedule adjusted")

        next_day = get_next_allowed(p)  # recompute after update

    # --- display next day nicely ---
    weekday = next_day.strftime("%A")
    formatted = next_day.strftime("%d %B %Y")

    st.subheader(selected)
    st.write(f"Next allowed: {weekday}, {formatted}")

    if date.today() >= next_day:
        st.success("You can use it today")
    else:
        st.warning(f"Wait {(next_day - date.today()).days} days")

    st.write("History:", p["usage"])

    # --- monthly view ---
    st.subheader("Monthly view")

    today = date.today()
    year = today.year
    month = today.month

    cal = calendar.monthcalendar(year, month)

    for week in cal:
        cols = st.columns(7)
        for i, day in enumerate(week):
            if day == 0:
                cols[i].write("")
            else:
                d = date(year, month, day)

                if d in p["usage"]:
                    cols[i].success(str(day))
                elif d == next_day:
                    cols[i].warning(str(day))
                else:
                    cols[i].write(str(day))

    # --- settings ---
    with st.expander("Settings"):
        st.write(f"Pause days: {p['pause_days']}")
        st.write(f"Change after: {p['phase_change_after']} days")
        st.write(f"New pause: {p['new_pause_days']}")
        st.write(f"Start date: {p['start_date']}")

else:
    st.info("Add your first product above")