"""NODE 1: HP Anak (edge1) — Deteksi Postur Rebahan + Aktuator Peringatan & Teguran Ortu.

Di HP Android (Termux):  python hp_anak.py
Simulasi di laptop:      python hp_anak.py --source simulator --scenario rebahan_main
"""

from shared.alarm import handle_child_alert
from shared.edge_runner import run_edge

if __name__ == "__main__":
    run_edge("edge1", on_alert=handle_child_alert, alert_topic_suffix="alerts/child")

