========================================
  VISA ADMIN — Setup & Usage Guide
========================================

FIRST-TIME SETUP
----------------
1. Make sure you have an internet connection for the initial setup.

2. Double-click: install.bat
   - This will automatically install everything needed.
   - Wait until you see "Installation complete!" before closing.
   - You only need to do this ONCE.

STARTING THE APP (every time)
------------------------------
3. Double-click: run.bat
   - Your browser will open automatically at http://localhost:5000
   - If the browser doesn't open, type this in your browser: http://localhost:5000
   - Close the black terminal window to stop the app.

HOW TO USE
----------
1. Go to Packages → Create your visa package templates (e.g. "UK Visa Package")
2. Add document slots to each package (e.g. "Passport Copy", "Bank Statement")
3. Go to Students → Import from CSV to add your students
4. Use the Dashboard to see who has/hasn't submitted each document
5. Click a student's name to go to their detail page and upload documents

CSV FORMAT FOR IMPORTING STUDENTS
-----------------------------------
Your CSV file must have these column headers (first row):
  name, email, package_name

Example:
  name,email,package_name
  Jane Smith,jane@example.com,UK Visa Package
  Ahmed Ali,ahmed@example.com,AU Visa Package

The package_name must exactly match a package you've already created.

YOUR DATA
---------
All data is stored LOCALLY on this computer only. Nothing is sent online.

  Database file:  visa_admin.db
  Uploaded files: documents\ folder

BACKUP
------
To back up everything, copy the entire visa-admin folder to another location
or an external drive. That's it.

TROUBLESHOOTING
---------------
- Browser doesn't open? → Type http://localhost:5000 in your browser manually.
- "uv not found" error? → Run install.bat again.
- App won't start? → Make sure you ran install.bat successfully first.

========================================
