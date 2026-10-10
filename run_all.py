# -*- coding: utf-8 -*-
"""
run_all.py — اجراکننده‌ی آپدیت دیتابیس dash2

این فایل هر سه آپدیتر را به‌ترتیب اجرا می‌کند تا جدول‌های دیتابیس bama.db
به‌روزرسانی شوند:

  1. upteter2.py        → به‌روزرسانی جدول tether (قیمت دلار/تتر)
  2. upgold2.py         → به‌روزرسانی جدول gold   (قیمت طلای ۱۸ عیار)
  3. dbbamanewupdater2.py → به‌روزرسانی جدول ads   (آگهی‌های خودرو از bama.ir)

اجرا:
    python run_all.py
"""

import subprocess
import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

UPDATERS = [
    "upteter2.py",            # tether
    "upgold2.py",             # gold
    "dbbamanewupdater2.py",   # ads
]


def run_python(script: str) -> None:
    """یک اسکریپت پایتون را به‌صورت زیرپروسس اجرا می‌کند."""
    path = os.path.join(SCRIPT_DIR, script)
    print("\n" + "=" * 30)
    print(f"▶ شروع: {script}")
    print("=" * 30)
    result = subprocess.run([sys.executable, path])
    if result.returncode != 0:
        print(f"⚠️  {script} با خطا تمام شد (کد {result.returncode})")
    else:
        print(f"✅ {script} با موفقیت تمام شد")
    return result.returncode


def main() -> None:
    print("#" * 30)
    print("#  شروع آپدیت کامل دیتابیس dash2  #")
    print("#" * 30)

    if not os.path.isfile(os.path.join(SCRIPT_DIR, "bama.db")):
        print("❌ فایل bama.db پیدا نشد!")
        sys.exit(1)

    any_failed = False
    for script in UPDATERS:
        rc = run_python(script)
        if rc != 0:
            any_failed = True

    print("\n" + "#" * 30)
    if any_failed:
        print("#  تمام شد — برخی اسکریپت‌ها خطا داشتند  #")
    else:
        print("#  تمام شد — همه‌ی آپدیترها موفق بودند  #")
    print("#" * 30)


if __name__ == "__main__":
    main()