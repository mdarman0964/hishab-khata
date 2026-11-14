#!/usr/bin/env python3
"""
কম্পিউটারের পুরনো হিসাব (data.json, cashbook.json, meal.json) অ্যাপে আনার জন্য এক টেক্সট বানায়।
চালান:  python make_backup.py <ফোল্ডার-যেখানে-JSON-ফাইলগুলো-আছে>
আউটপুটটা কপি করে অ্যাপের হোম পেজ → "ব্যাকআপ ও ফিরিয়ে আনা" → টেক্সট বক্সে পেস্ট করে "ফিরিয়ে আনুন" চাপুন।
"""
import json, os, sys
d = sys.argv[1] if len(sys.argv) > 1 else "."
out = {}
for key, name in (("hajira", "data.json"), ("cashbook", "cashbook.json"), ("meal", "meal.json")):
    p = os.path.join(d, name)
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            out[key] = json.load(f)
print(json.dumps(out, ensure_ascii=False))
