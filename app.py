import streamlit as st
import fastf1
import matplotlib.pyplot as plt

st.set_page_config(page_title="Live F1 Telemetry: Head-to-Head", layout="wide")
st.title("Qualifying Head-to-Head: VER vs NOR")

fastf1.Cache.enable_cache('cache')
session = fastf1.get_session(2023, 'Monza', 'Q')
session.load()

# Load telemetry for both drivers
lap_ver = session.laps.pick_driver('VER').pick_fastest()
lap_nor = session.laps.pick_driver('NOR').pick_fastest()
tele_ver = lap_ver.get_telemetry()
tele_nor = lap_nor.get_telemetry()

# Create a 2-part figure (Speed on top, Throttle on bottom)
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6), sharex=True)

# Top Plot: Speed Trace
ax1.plot(tele_ver['Distance'], tele_ver['Speed'], color='blue', label='VER (Red Bull)')
ax1.plot(tele_nor['Distance'], tele_nor['Speed'], color='orange', label='NOR (McLaren)')
ax1.set_ylabel("Speed (km/h)")
ax1.legend(loc="lower right")
ax1.set_title("Speed & Throttle Comparison")

# Bottom Plot: Throttle Trace
ax2.plot(tele_ver['Distance'], tele_ver['Throttle'], color='blue')
ax2.plot(tele_nor['Distance'], tele_nor['Throttle'], color='orange')
ax2.set_ylabel("Throttle (%)")
ax2.set_xlabel("Distance (m)")

plt.tight_layout()
st.pyplot(fig)
