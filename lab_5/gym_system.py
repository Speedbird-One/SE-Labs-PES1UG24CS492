"""Gym class booking system: manages class capacities, rosters and exports."""
import glob
import json
import os

# Global state
class_capacity = {"Yoga": 3, "HIIT": 2, "Spin": 4}
rosters = {}


def book_class(member_id, class_name, attendance_log=None):
    """Book a member into a class.

    Returns True on success, False if the class is full, does not exist
    (capacity 0) or the member is already booked.
    """
    if attendance_log is None:
        attendance_log = []
    roster = rosters.get(class_name, [])
    if len(roster) >= class_capacity.get(class_name, 0):
        print(f"Class full or unavailable: {class_name}")
        return False
    if member_id in roster:
        print(f"{member_id} is already booked in {class_name}")
        return False
    rosters.setdefault(class_name, []).append(member_id)
    attendance_log.append(f"{member_id} -> {class_name}")
    return True


def cancel_booking(member_id, class_name):
    """Remove a member from a class. Returns True if a booking was removed."""
    try:
        rosters[class_name].remove(member_id)
    except (KeyError, ValueError):
        print("Nothing to cancel")
        return False
    return True


def set_capacity(class_name, seats):
    """Set the capacity of a class. Negative values are rejected."""
    if seats < 0:
        print(f"Invalid capacity {seats} for {class_name}")
        return False
    class_capacity[class_name] = seats
    return True


def add_members(class_name, count):
    """Book `count` numbered walk-in guests into a class."""
    existing = sum(
        1 for m in rosters.get(class_name, []) if str(m).startswith("GUEST-")
    )
    for i in range(existing, existing + count):
        book_class(f"GUEST-{i}", class_name)


def export_roster(file="gym_schedule.json"):
    """Write all rosters to a JSON file."""
    with open(file, "w", encoding="utf-8") as handle:
        json.dump(rosters, handle)


def clear_old_exports(prefix="old_"):
    """Delete exported JSON files whose names start with `prefix`."""
    for path in glob.glob(prefix + "*.json"):
        os.remove(path)


def show_rosters():
    """Print every class roster."""
    for class_name, members in rosters.items():
        print(class_name, ":", ", ".join(str(m) for m in members))


def main():
    """Run the demo booking scenario."""
    book_class("M1", "Yoga")
    book_class("M2", "Yoga")
    book_class("M3", "Yoga")
    book_class("M4", "Yoga")
    book_class(55, "HIIT")
    book_class("M5", "Pilates")
    set_capacity("Spin", -2)
    add_members("Spin", 3)
    cancel_booking("M9", "Boxing")
    raw = input("How many walk-in guests for HIIT? (Enter for 1): ") or "1"
    try:
        guests = int(raw)
    except ValueError:
        print(f"'{raw}' is not a number, using 1 guest")
        guests = 1
    add_members("HIIT", guests)
    clear_old_exports()
    export_roster()
    show_rosters()


if __name__ == "__main__":
    main()
