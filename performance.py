import math
import numpy as np
import matplotlib.pyplot as plt

DEFAULTS = {
    "S": 47, "AR": 6.5, "e": 0.87, "C_D0": 0.032, "W": 103047,
    "n_engines": 2, "T_per_engine": 40298, "W_fuel": 1900, "Ct": 1/3600,
    "CL_max": 0.8, "CL_max_deployed_flap": 2.8, "CL_max_pitch_down": 1.5,
    "u": 0.02, "n_Lu": 5, "n_Ld": -3
}
DENSITY = {0: 1.225, 1: 1.112, 2: 1.006, 3: 0.909, 4: 0.819, 5: 0.736}


def calculate_performance(p, altitudes):
    S, AR, e, C_D0, W = p["S"], p["AR"], p["e"], p["C_D0"], p["W"]
    n_engines, T_per_engine = int(p["n_engines"]), p["T_per_engine"]
    CL_max, CL_max_pitch_down = p["CL_max"], p["CL_max_pitch_down"]
    n_Lu, n_Ld = p["n_Lu"], p["n_Ld"]
    results = {}
    altitude_comparison_figure = None

    for h in altitudes:
        density = DENSITY[h]
        V = np.arange(25, 500)
        k = 1 / (math.pi * AR * e)

        # Original thrust-required equation
        TR = (0.5 * density * V**2 * S * C_D0) + (
            0.5 * density * V**2 * S * k
            * (W / (0.5 * density * V**2 * S))**2
        )
        TR_min_graph = min(TR)
        TR_min = W * (4 * C_D0 * k)**0.5
        error = abs(TR_min - TR_min_graph) / TR_min * 100
        V_TR_min = ((2/density) * (W/S) * (k/C_D0)**0.5)**0.5

        # Original thrust-available model
        T_A0 = T_per_engine * n_engines
        T_Ah = T_A0 * (density / DENSITY[0])
        T_Ah_arr = np.ones_like(TR) * T_Ah

        V_intersection = 0
        difference = TR - T_Ah_arr
        idx = np.where(np.diff(np.sign(difference)) != 0)[0]
        for i in idx:
            V_intersection = V[i] - (difference[i] * (
                (V[i+1] - V[i]) / (difference[i+1] - difference[i])
            ))

        # Original power and rate-of-climb calculations
        PR = TR * V
        PA = T_Ah_arr * V
        ROC = (PA - PR) / W
        max_roc = max(ROC)
        V_rc_max = V[np.argmax(ROC)]

        # Original V-n diagram calculations
        V_vn = np.arange(0, 500)
        n_pitchup = 0.5 * density * V_vn**2 * S * CL_max / W
        n_pitchdown = -0.5 * density * V_vn**2 * S * CL_max_pitch_down / W
        V_a_positive = np.sqrt(2 * W * n_Lu / (density * S * CL_max))
        V_a_negative = np.sqrt(2 * W * abs(n_Ld) / (density * S * CL_max_pitch_down))
        V_positive = V_vn[V_vn < V_a_positive]
        V_positive = np.append(V_positive, V_a_positive)
        n_positive = 0.5 * density * V_positive**2 * S * CL_max / W
        V_negative = V_vn[V_vn < V_a_negative]
        V_negative = np.append(V_negative, V_a_negative)
        n_negative = -0.5 * density * V_negative**2 * S * CL_max_pitch_down / W

        fig_thrust, ax = plt.subplots()
        ax.plot(V, TR, color="blue", label="TR vs V")
        ax.plot(V, T_Ah_arr, color="red", label="TA vs V")
        ax.grid()
        ax.set_xlabel("Free Stream Velocity (m/s)")
        ax.set_ylabel("Thrust (N)")
        ax.legend()
        ax.set_title(f"Thrust vs Velocity Curve (h = {h} km)")

        fig_power, ax = plt.subplots()
        ax.plot(V, PR, label="PR vs V")
        ax.plot(V, PA, label="PA vs V")
        ax.grid()
        ax.set_xlabel("Free Stream Velocity (m/s)")
        ax.set_ylabel("Power")
        ax.legend()
        ax.set_title(f"Power vs Velocity Curve (h = {h} km)")

        fig_roc, ax = plt.subplots()
        ax.plot(V, ROC, label="ROC vs V")
        ax.grid()
        ax.set_xlabel("Free Stream Velocity (m/s)")
        ax.set_ylabel("Rate of Climb (m/s)")
        ax.set_title(f"Rate of Climb vs Velocity (h = {h} km)")
        ax.legend()

        fig_vn, ax = plt.subplots()
        ax.plot(V_positive, n_positive, color="blue", label="Aerodynamic Limit (PU)")
        ax.plot(V_negative, n_negative, color="red", label="Aerodynamic Limit (PD)")
        ax.plot([V_a_positive, V_intersection], [n_Lu, n_Lu], color="orange", label="Structural Limit (PU)")
        ax.plot([V_a_negative, V_intersection], [n_Ld, n_Ld], color="purple", label="Structural Limit (PD)")
        ax.plot([V_intersection, V_intersection], [n_Ld, n_Lu], color="green", label="Propulsive Limit")
        ax.set_xlim(0, 310)
        ax.set_ylim(-5, 6)
        ax.grid()
        ax.set_xlabel("Velocity (m/s)")
        ax.set_ylabel("Load Factor n")
        ax.set_title(f"V-n Diagram (h = {h} km)")
        ax.legend()

        # Original take-off calculations and assumptions
        CL_ground = 0.8
        Sg = 1.21 * (W / S) / (9.81 * density * CL_ground * (T_Ah / W))
        V_stall = np.sqrt(2 * W / (density * S * CL_ground))
        Vx = 1.2 * V_stall
        n_takeoff = 1 + Vx**2 / (9.81 * 1356.64)
        R = Vx**2 / (9.81 * (n_takeoff - 1))
        obstacle_height = 50
        theta_max = np.arccos(1 - obstacle_height / R)
        theta = np.linspace(0, theta_max, 200)
        x_air = Sg + R * np.sin(theta)
        y_air = R * (1 - np.cos(theta))
        x_ground = np.linspace(0, Sg, 100)
        y_ground = np.zeros_like(x_ground)
        Sa = R * np.sin(theta_max)
        Sto = Sg + Sa

        fig_takeoff, ax = plt.subplots()
        ax.plot(x_ground, y_ground, label="Ground Roll")
        ax.plot(x_air, y_air, label="Airborne Trajectory")
        ax.axhline(y=obstacle_height, color="gray", linestyle="--", label="50 m Obstacle")
        ax.scatter(Sto, obstacle_height, color="red", zorder=5, label="Obstacle Cleared")
        ax.annotate("Obstacle Cleared", (Sto, obstacle_height), xytext=(-10, 10),
                    textcoords="offset points", ha="right")
        ax.set_xlabel("Distance (m)")
        ax.set_ylabel("Height (m)")
        ax.set_title(f"Take-off Trajectory (h = {h} km)")
        ax.grid()
        ax.legend()

        # Original hodograph calculations
        V_stall_hodo = np.sqrt(2 * W / (density * S * CL_max))
        mask = (V >= V_stall_hodo) & (V <= V_intersection)
        Vh = V[mask]
        Vv = ROC[mask]
        idx_max_roc = np.argmax(Vv)
        Vh_max_roc = Vh[idx_max_roc]
        Vv_max_roc = Vv[idx_max_roc]
        Vh = np.append(Vh, V_intersection)
        Vv = np.append(Vv, 0.0)

        fig_hodo, ax = plt.subplots(figsize=(10, 7))
        ax.plot(Vh, Vv, label="Hodograph curve")
        ax.scatter(Vh_max_roc, Vv_max_roc, color="blue", zorder=5)
        ax.annotate("Max RoC", (Vh_max_roc, Vv_max_roc), xytext=(10, 15),
                    textcoords="offset points", arrowprops=dict(arrowstyle="->"))
        ax.scatter(V_intersection, 0, color="blue", zorder=5)
        ax.annotate("Vmax (Level flight)", (V_intersection, 0), xytext=(10, 15),
                    textcoords="offset points", arrowprops=dict(arrowstyle="->"))
        ax.scatter(Vh[0], Vv[0], color="blue", zorder=5)
        ax.annotate("RoC at minimum speed", (Vh[0], Vv[0]), xytext=(10, 10),
                    textcoords="offset points", arrowprops=dict(arrowstyle="->"))
        ax.set_xlabel("Horizontal Speed Vh (m/s)")
        ax.set_ylabel("Vertical Speed Vv (m/s)")
        ax.set_title(f"Hodograph Diagram (h = {h} km)")
        ax.grid()
        ax.legend()

        results[h] = {
            "TR_min_graph": TR_min_graph, "TR_min": TR_min, "error": error,
            "V_TR_min": V_TR_min, "T_Ah": T_Ah, "V_intersection": V_intersection,
            "max_roc": max_roc, "V_rc_max": V_rc_max, "Vx": Vx, "Sg": Sg,
            "Sa": Sa, "Sto": Sto,
            "figures": {
                "Thrust required and available": fig_thrust,
                "Power required and available": fig_power,
                "Rate of climb": fig_roc,
                "V-n diagram": fig_vn,
                "Take-off trajectory": fig_takeoff,
                "Hodograph diagram": fig_hodo,
            }
        }

    # Original altitude comparison graph, shown once
    V_compare = np.arange(25, 500)
    k = 1 / (math.pi * AR * e)
    rho_1, rho_4 = DENSITY[1], DENSITY[4]
    TR_1 = 0.5 * rho_1 * V_compare**2 * S * C_D0 + (
        0.5 * rho_1 * V_compare**2 * S * k
        * (W / (0.5 * rho_1 * V_compare**2 * S))**2
    )
    TR_4 = 0.5 * rho_4 * V_compare**2 * S * C_D0 + (
        0.5 * rho_4 * V_compare**2 * S * k
        * (W / (0.5 * rho_4 * V_compare**2 * S))**2
    )
    altitude_comparison_figure, ax = plt.subplots(figsize=(10, 6))
    ax.plot(V_compare, TR_1, label="TR vs V for h=1 km (rho = 1.112)")
    ax.plot(V_compare, TR_4, label="TR vs V for h=4 km (rho = 0.819)")
    ax.set_xlabel("Velocity (m/s)")
    ax.set_ylabel("Thrust Required (N)")
    ax.set_title("Effect of Altitude (Density) on Thrust Required")
    ax.grid()
    ax.legend()

    for r in results.values():
        r["altitude_comparison_figure"] = altitude_comparison_figure
    return results
