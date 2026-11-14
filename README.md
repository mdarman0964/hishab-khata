# আমার খাতা — Android ও iPhone অ্যাপ

হাজিরা খাতা, ক্যাশবুক ও মিলের হিসাব — তিনটাই এক অ্যাপে। Android ও iPhone সংস্করণ একই `www/` অ্যাপ ইন্টারফেস ও লোকাল ডেটা ব্যবহার করে। হিসাব ফোনেই সেভ থাকে; সাধারণ ব্যবহারে ইন্টারনেট লাগে না।

## Android APK
Android বিল্ডের নির্দেশনা: `.github/workflows/android.yml`। Android-এর কাজ `main` ব্রাঞ্চে থাকে।

## iPhone / iOS
iOS-এর কাজ আলাদা `ios-app` ব্রাঞ্চে। এটি একই `www/` ফাইল ব্যবহার করে Capacitor iOS wrapper তৈরি করে; মূল HTML পেজ বা হিসাবের UI আলাদা করে বদলানো হয়নি।

### iOS বিল্ড
1. GitHub repository-র `ios-app` ব্রাঞ্চ খুলুন।
2. **Actions → Build iOS App → Run workflow** চালান (অথবা ওই ব্রাঞ্চে পরিবর্তন push করুন)।
3. সফল হলে Actions run-এর Artifacts থেকে:
   - `hishab-khata-ios-simulator`: iOS Simulator-এর জন্য `.app`
   - `hishab-khata-ios-archive`: signing-এর জন্য unsigned `.xcarchive`

### iPhone-এ ইনস্টল
বাস্তব iPhone-এ ইনস্টল বা TestFlight/App Store-এ প্রকাশের জন্য Apple Developer signing certificate, provisioning profile এবং সংশ্লিষ্ট GitHub Actions secrets লাগবে। এই workflow unsigned device archive তৈরি করে; এটি সরাসরি iPhone-এ ইনস্টলযোগ্য IPA নয়।

## পুরনো হিসাব (কম্পিউটারের JSON) অ্যাপে আনা
1. `python tools/make_backup.py <যে ফোল্ডারে data.json, cashbook.json, meal.json আছে>`
2. যে লেখাটা ছাপা হবে সেটা কপি করুন → ফোনে অ্যাপের হোম পেজ → **ব্যাকআপ ও ফিরিয়ে আনা** → পেস্ট করে **ফিরিয়ে আনুন**।

## ফোল্ডার
- `www/` — অ্যাপের পেজ (Android ও iOS উভয় বিল্ডে ব্যবহৃত)
- `desktop/` — আগের পাইথন সংস্করণ
- `tools/build_www.py` — `desktop/` বদলালে `www/` আবার বানায়
- `.github/workflows/android.yml` — Android APK build
- `.github/workflows/ios.yml` — iOS build

## ডেটা ও ব্যাকআপ
হিসাব ডিভাইসের লোকাল স্টোরেজে থাকে। অ্যাপ মুছলে বা ডেটা ক্লিয়ার করলে হিসাব হারাতে পারে — নিয়মিত ব্যাকআপ শেয়ার করে রাখুন।
