import streamlit as st
import matplotlib.pyplot as plt
import numpy as np

from performance import DEFAULTS, calculate_performance

st.set_page_config(page_title="Aircraft Performance Explorer", page_icon="✈️", layout="wide")
st.title("✈️ Aircraft Performance Explorer - Mohona, 1MS24AS031")
st.caption("Interactive aircraft performance calculations and plots. Equations and assumptions are preserved from the supplied script.")

with st.sidebar:
    st.header("Aircraft specifications")
    st.caption("Edit any value, then click **Run analysis**.")
    with st.form("aircraft_inputs"):
        S = st.number_input("Wing area S (m²)", min_value=0.1, value=float(DEFAULTS["S"]), step=1.0)
        AR = st.number_input("Aspect ratio AR", min_value=0.1, value=float(DEFAULTS["AR"]), step=0.1)
        e = st.number_input("Oswald efficiency factor e", min_value=0.01, max_value=1.0, value=float(DEFAULTS["e"]), step=0.01)
        CD0 = st.number_input("Zero-lift drag coefficient CD₀", min_value=0.001, value=float(DEFAULTS["C_D0"]), step=0.001, format="%.3f")
        W = st.number_input("Gross weight W (N)", min_value=1.0, value=float(DEFAULTS["W"]), step=1000.0)
        n_engines = st.number_input("Number of engines", min_value=1, value=int(DEFAULTS["n_engines"]), step=1)
        thrust = st.number_input("Thrust per engine (N)", min_value=1.0, value=float(DEFAULTS["T_per_engine"]), step=1000.0)
        fuel = st.number_input("Fuel quantity (gallons; currently informational)", min_value=0.0, value=float(DEFAULTS["W_fuel"]), step=50.0)
        ct = st.number_input("TSFC Ct (1/hr)", min_value=0.000001, value=float(DEFAULTS["Ct"]), step=0.00001, format="%.6f")
        cl_max = st.number_input("Maximum lift coefficient CL,max", min_value=0.01, value=float(DEFAULTS["CL_max"]), step=0.1)
        cl_flap = st.number_input("CL,max with fully deployed flap", min_value=0.01, value=float(DEFAULTS["CL_max_deployed_flap"]), step=0.1)
        cl_pitch = st.number_input("CL,max pitch-down", min_value=0.01, value=float(DEFAULTS["CL_max_pitch_down"]), step=0.1)
        mu = st.number_input("Coefficient of friction μ", min_value=0.0, value=float(DEFAULTS["u"]), step=0.01)
        n_lu = st.number_input("Positive structural load limit", min_value=0.1, value=float(DEFAULTS["n_Lu"]), step=0.5)
        n_ld = st.number_input("Negative structural load limit", max_value=-0.1, value=float(DEFAULTS["n_Ld"]), step=0.5)
        altitudes = st.multiselect("Altitudes to analyse (km)", options=[0, 1, 2, 3, 4, 5], default=[1, 4])
        run = st.form_submit_button("Run analysis", type="primary", use_container_width=True)

if "results" not in st.session_state:
    st.session_state.results = None
if run:
    if not altitudes:
        st.error("Select at least one altitude.")
        st.stop()
    params = {
        "S": S, "AR": AR, "e": e, "C_D0": CD0, "W": W,
        "n_engines": n_engines, "T_per_engine": thrust, "W_fuel": fuel,
        "Ct": ct, "CL_max": cl_max, "CL_max_deployed_flap": cl_flap,
        "CL_max_pitch_down": cl_pitch, "u": mu, "n_Lu": n_lu, "n_Ld": n_ld
    }
    try:
        st.session_state.results = calculate_performance(params, altitudes)
    except Exception as exc:
        st.error(f"Could not calculate the selected case: {exc}")
        st.stop()

if st.session_state.results is None:
    st.info("Choose your aircraft specifications in the sidebar and click **Run analysis**.")
    st.markdown("The app includes thrust, power, rate-of-climb, V–n, take-off trajectory, hodograph, and altitude-comparison plots.")
    st.stop()

results = st.session_state.results
st.subheader("Performance summary")
cols = st.columns(min(4, len(results)))
for i, (h, r) in enumerate(results.items()):
    with cols[i % len(cols)]:
        st.markdown(f"**Altitude: {h} km**")
        st.metric("Minimum thrust required", f"{r['TR_min_graph']:.1f} N")
        st.metric("Maximum level-flight speed", f"{r['V_intersection']:.2f} m/s")
        st.metric("Maximum rate of climb", f"{r['max_roc']:.2f} m/s")
        st.metric("Take-off distance to 50 m", f"{r['Sto']:.1f} m")

tabs = st.tabs([f"{h} km" for h in results] + ["Altitude comparison"])
for tab, (h, r) in zip(tabs, results.items()):
    with tab:
        st.markdown(f"### Results at {h} km")
        metrics = st.columns(4)
        metrics[0].metric("Theoretical minimum thrust", f"{r['TR_min']:.1f} N")
        metrics[1].metric("Graph/theory error", f"{r['error']:.3f}%")
        metrics[2].metric("Velocity at minimum thrust", f"{r['V_TR_min']:.2f} m/s")
        metrics[3].metric("Available thrust", f"{r['T_Ah']:.1f} N")
        metrics = st.columns(4)
        metrics[0].metric("Velocity at max ROC", f"{r['V_rc_max']:.2f} m/s")
        metrics[1].metric("Take-off velocity", f"{r['Vx']:.2f} m/s")
        metrics[2].metric("Ground roll", f"{r['Sg']:.2f} m")
        metrics[3].metric("Airborne distance", f"{r['Sa']:.2f} m")

        chart_cols = st.columns(2)
        for idx, (title, fig) in enumerate(r["figures"].items()):
            with chart_cols[idx % 2]:
                st.pyplot(fig, use_container_width=True)
                plt.close(fig)

with tabs[-1]:
    st.markdown("### Effect of altitude on thrust required")
    fig = results[next(iter(results))]["altitude_comparison_figure"]
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)

with st.expander("Calculation notes"):
    st.write("The supplied equations and assumptions have been kept as provided. The fuel input and several specifications are included in the interface even where the original script does not use them in the plotted calculations.")
    st.write("Density values used by the original calculations: 0 km = 1.225, 1 km = 1.112, 2 km = 1.006, 3 km = 0.909, 4 km = 0.819, 5 km = 0.736 kg/m³.")
