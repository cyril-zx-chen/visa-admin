from flask import Blueprint, render_template
import models
import utils

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
def index():
    data, unassigned = models.get_dashboard_data()

    total_students = sum(len(v["students"]) for v in data.values()) + len(unassigned)
    total_packages = len(data)

    all_subs = [s for v in data.values() for student in v["students"]
                for s in [v["submissions"].get((student["id"], sl["id"]))
                          for sl in v["slots"] if sl["is_required"]]
                if s is not None]

    required_received = sum(1 for s in all_subs if s["status"] == "received")
    required_pending  = sum(1 for s in all_subs if s["status"] == "pending")

    stats = {
        "students": total_students,
        "packages": total_packages,
        "received": required_received,
        "pending":  required_pending,
    }

    # Suggest restore if DB is empty but a backup file exists
    backup_prompt = (
        total_students == 0 and total_packages == 0
        and utils.backup_file_info()["exists"]
    )
    backup_info = utils.backup_file_info() if backup_prompt else None

    return render_template(
        "dashboard.html",
        data=data,
        unassigned=unassigned,
        stats=stats,
        backup_prompt=backup_prompt,
        backup_info=backup_info,
    )
