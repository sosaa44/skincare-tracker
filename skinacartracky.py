import streamlit as st
import sqlite3
import calendar
from datetime import date, timedelta

st.set_page_config(page_title="Tracker", layout="centered")
st.title("Skincare Tracker")

# --- database ---
conn = sqlite3.connect("data.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS products (
    name TEXT PRIMARY KEY,
    pause_days INTEGER,
    start_date TEXT,
    phase_change_after INTEGER,
    new_pause_days INTEGER
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product TEXT,
    used_on TEXT
)
""")
conn.commit()

# --- logic ---
def get_current_pause(p):
    days_since_start = (date.today() - p["start_date"]).days
    if days_since_start >= p["phase_change_after"]:
        return p["new_pause_days"]
    return p["pause_days"]

def get_usage(name):
    rows = c.execute("SELECT used_on FROM usage WHERE product=?", (name,)).fetchall()
    return [date.fromisoformat(r[0]) for r in rows]

def add_usage(name):
    c.execute("INSERT INTO usage (product, used_on) VALUES (?, ?)", (name, date.today().isoformat()))
    conn.commit()

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
        c.execute(
            "INSERT OR REPLACE INTO products VALUES (?, ?, ?, ?, ?)",
            (name, pause, date.today().isoformat(), phase, new_pause)
        )
        conn.commit()
        st.success("Saved")

# --- load products ---
products = c.execute("SELECT * FROM products").fetchall()

if products:
    names = [p[0] for p in products]
    selected = st.selectbox("Select product", names)

    row = next(p for p in products if p[0] == selected)

    p = {
        "name": row[0],
        "pause_days": row[1],
        "start_date": date.fromisoformat(row[2]),
        "phase_change_after": row[3],
        "new_pause_days": row[4]
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