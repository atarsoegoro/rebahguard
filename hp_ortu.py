"""NODE 2: HP Orang Tua (edge2) — Shake-to-Scold + Penerima Notifikasi Alert Mata.

Di HP Android (Termux):  python hp_ortu.py
Simulasi di laptop:      python hp_ortu.py --source simulator --scenario ortu_shake
"""

from shared.alarm import handle_parent_alert
from shared.edge_runner import run_edge

if __name__ == "__main__":
    run_edge("edge2", on_alert=handle_parent_alert, alert_topic_suffix="alerts/parent")

