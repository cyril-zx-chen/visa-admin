import sqlite3
from flask import Blueprint, render_template, request, redirect, url_for, flash
import models

packages_bp = Blueprint("packages", __name__, url_prefix="/packages")


@packages_bp.route("/")
def list_packages():
    pkgs = models.get_all_packages()
    counts = {}
    for pkg in pkgs:
        students = models.get_students_for_package(pkg["id"])
        slots = models.get_slots_for_package(pkg["id"])
        counts[pkg["id"]] = {"students": len(students), "slots": len(slots)}
    return render_template("packages/list.html", packages=pkgs, counts=counts)


@packages_bp.route("/new", methods=["GET"])
def new_package_form():
    return render_template("packages/new.html")


@packages_bp.route("/new", methods=["POST"])
def create_package():
    name = request.form.get("name", "").strip()
    if not name:
        flash("Package name cannot be empty.", "danger")
        return redirect(url_for("packages.new_package_form"))
    try:
        pkg_id = models.create_package(name)
        flash(f'Package "{name}" created.', "success")
        return redirect(url_for("packages.package_detail", pkg_id=pkg_id))
    except sqlite3.IntegrityError:
        flash(f'A package named "{name}" already exists.', "danger")
        return redirect(url_for("packages.new_package_form"))


@packages_bp.route("/<int:pkg_id>")
def package_detail(pkg_id):
    pkg, slots = models.get_package_with_slots(pkg_id)
    if pkg is None:
        flash("Package not found.", "danger")
        return redirect(url_for("packages.list_packages"))
    students = models.get_students_for_package(pkg_id)
    return render_template("packages/detail.html", package=pkg, slots=slots, students=students)


@packages_bp.route("/<int:pkg_id>/slots/add", methods=["POST"])
def add_slot(pkg_id):
    name = request.form.get("name", "").strip()
    is_required = request.form.get("is_required") == "1"
    if not name:
        flash("Slot name cannot be empty.", "danger")
        return redirect(url_for("packages.package_detail", pkg_id=pkg_id))
    try:
        models.add_slot(pkg_id, name, is_required)
        flash(f'Slot "{name}" added.', "success")
    except sqlite3.IntegrityError:
        flash(f'A slot named "{name}" already exists in this package.', "danger")
    return redirect(url_for("packages.package_detail", pkg_id=pkg_id))


@packages_bp.route("/<int:pkg_id>/slots/<int:slot_id>/delete", methods=["POST"])
def delete_slot(pkg_id, slot_id):
    models.delete_slot(slot_id)
    flash("Slot deleted.", "success")
    return redirect(url_for("packages.package_detail", pkg_id=pkg_id))


@packages_bp.route("/<int:pkg_id>/slots/<int:slot_id>/toggle-required", methods=["POST"])
def toggle_slot_required(pkg_id, slot_id):
    models.toggle_slot_required(slot_id)
    return redirect(url_for("packages.package_detail", pkg_id=pkg_id))


@packages_bp.route("/<int:pkg_id>/delete", methods=["POST"])
def delete_package(pkg_id):
    students = models.get_students_for_package(pkg_id)
    if students:
        flash("Cannot delete package: students are still enrolled. Reassign or delete them first.", "danger")
        return redirect(url_for("packages.package_detail", pkg_id=pkg_id))
    pkg = models.get_package(pkg_id)
    models.delete_package(pkg_id)
    flash(f'Package "{pkg["name"]}" deleted.', "success")
    return redirect(url_for("packages.list_packages"))
