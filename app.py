import os
import streamlit as st
import fastf1
import fastf1.plotting
import pandas as pd
import matplotlib.pyplot as plt

os.makedirs("cache", exist_ok=True)
fastf1.Cache.enable_cache("cache")

st.set_page_config(page_title="AutodromeF1 Control Room", layout="wide")
qp = st.query_params
if qp.get("hide") == "1":
    st.markdown("<style>[data-testid='stSidebar'], [data-testid='stSidebarCollapsedControl'] {display:none;}</style>", unsafe_allow_html=True)

st.markdown("""
<style>
header, footer, #MainMenu {visibility: hidden;}
.stApp {background-color: #0b0b10;}
.block-container {padding-top: 1rem; max-width: 100%;}
</style>
""", unsafe_allow_html=True)


@st.cache_resource(show_spinner="Loading session data...")
def load_session(year, gp, ses):
    s = fastf1.get_session(year, gp, ses)
    s.load(telemetry=True, weather=False, messages=False)
    return s


def fmt(td):
    if pd.isna(td):
        return "-"
    t = td.total_seconds()
    return f"{int(t // 60)}:{t % 60:06.3f}"


# ---------- Sidebar ----------
st.sidebar.title("Broadcast Feed Controls")
year = st.sidebar.number_input("Year", 2018, 2026, int(qp.get("year", 2023)))
gp = st.sidebar.text_input("Grand Prix", qp.get("gp", "Italy"))
ses = st.sidebar.selectbox("Session", ["FP1", "FP2", "FP3", "Q", "SQ", "S", "R"], index=["FP1", "FP2", "FP3", "Q", "SQ", "S", "R"].index(qp.get("ses", "Q")) if qp.get("ses", "Q") in ["FP1", "FP2", "FP3", "Q", "SQ", "S", "R"] else 3)

try:
    session = load_session(int(year), gp, ses)
except Exception as e:
    st.error(f"Could not load session: {e}")
    st.stop()

drivers = sorted(session.laps["Driver"].unique())
mode = st.sidebar.radio("View", ["Head to Head", "Multi-Driver Hub"])

if mode == "Head to Head":
    d1 = st.sidebar.selectbox("Primary Driver", drivers, index=drivers.index(qp.get("d1")) if qp.get("d1") in drivers else (drivers.index("VER") if "VER" in drivers else 0))
    d2 = st.sidebar.selectbox("Comparison Driver", drivers, index=drivers.index(qp.get("d2")) if qp.get("d2") in drivers else (drivers.index("NOR") if "NOR" in drivers else 1))
    chosen = [d1, d2]
else:
    defaults = [d for d in ["VER", "NOR", "HAM", "LEC"] if d in drivers]
    chosen = st.sidebar.multiselect("Drivers (max 4)", drivers, default=defaults, max_selections=4)

st.title(f"AutodromeF1 | {session.event['EventName']} {year} - {ses}")
st.caption("Replay of official timing data - not live")

left, right = st.columns([1.3, 2.3])

# ---------- Timing tower ----------
with left:
    st.subheader("Timing Tower")
    res = session.results[["Position", "Abbreviation", "TeamName"]].copy()
    res.columns = ["Pos", "Driver", "Team"]
    res["Pos"] = res["Pos"].astype("Int64")
    best = session.laps.groupby("Driver")["LapTime"].min()
    res["Best Lap"] = res["Driver"].map(best).map(fmt)
    st.dataframe(res, width="stretch", hide_index=True, height=620)

# ---------- Telemetry ----------
with right:
    st.subheader("Fastest Lap Telemetry: " + " vs ".join(chosen))
    if not chosen:
        st.warning("Please select at least one driver.")
    else:
        plt.style.use("dark_background")
        fig, axes = plt.subplots(4, 1, figsize=(11, 7), sharex=True,
                                 gridspec_kw={"height_ratios": [3, 1.5, 1, 1.5]})
        fig.patch.set_facecolor("#0b0b10")
        for drv in chosen:
            try:
                lap = session.laps.pick_drivers(drv).pick_fastest()
                tel = lap.get_car_data().add_distance()
                try:
                    color = fastf1.plotting.get_driver_color(drv, session)
                except Exception:
                    color = None
                if color:
                    import matplotlib.colors as mc
                    color = tuple(c + (1 - c) * 0.45 for c in mc.to_rgb(color))
                label = f"{drv} {fmt(lap['LapTime'])}"
                axes[0].plot(tel["Distance"], tel["Speed"], label=label, color=color, lw=1.6)
                axes[1].plot(tel["Distance"], tel["Throttle"], color=color, lw=1.2)
                axes[2].plot(tel["Distance"], tel["Brake"].astype(int), color=color, lw=1.2)
                axes[3].plot(tel["Distance"], tel["nGear"], color=color, lw=1.2)
            except Exception as e:
                st.warning(f"No telemetry for {drv}: {e}")
        for ax, name in zip(axes, ["Speed (km/h)", "Throttle (%)", "Brake", "Gear"]):
            ax.set_ylabel(name)
            ax.set_facecolor("#0b0b10")
            ax.grid(alpha=0.15)
        axes[3].set_xlabel("Distance (m)")
        axes[0].legend(loc="lower right", ncol=len(chosen))
        plt.tight_layout()
        st.pyplot(fig)
