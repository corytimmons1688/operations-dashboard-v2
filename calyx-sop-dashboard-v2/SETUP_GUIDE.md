# Complete Setup Guide: NC Dashboard

## A Step-by-Step Guide for First-Time Users

This guide assumes you have never used GitHub or Streamlit before. Follow each step carefully.

---

## Table of Contents

1. [Prerequisites - What You Need First](#part-1-prerequisites)
2. [Setting Up GitHub](#part-2-setting-up-github)
3. [Setting Up Google Cloud Credentials](#part-3-setting-up-google-cloud-credentials)
4. [Running the Dashboard Locally (Optional)](#part-4-running-locally-optional)
5. [Deploying to Streamlit Cloud (Recommended)](#part-5-deploying-to-streamlit-cloud)
6. [Troubleshooting Common Issues](#part-6-troubleshooting)

---

## Part 1: Prerequisites

### What You'll Need:
- A computer with internet access
- A Google account (you already have this - it's how you access Google Sheets)
- About 30-45 minutes to complete the setup

### Download the Project Files
1. Download the `nc-dashboard.zip` file I provided
2. Extract/unzip the file to a folder on your computer (e.g., `C:\Users\Xander\Documents\nc-dashboard`)
3. Remember this location - you'll need it later

---

## Part 2: Setting Up GitHub

### Step 2.1: Create a GitHub Account

1. Go to [https://github.com](https://github.com)
2. Click **"Sign up"** in the top right corner
3. Enter your email address
4. Create a password
5. Choose a username (e.g., `xander-calyx`)
6. Complete the verification puzzle
7. Check your email and verify your account

### Step 2.2: Create a New Repository

1. Once logged into GitHub, click the **"+"** icon in the top right corner
2. Select **"New repository"**
3. Fill in the details:
   - **Repository name**: `nc-dashboard`
   - **Description**: `Non-Conformance Analysis Dashboard for Calyx Containers`
   - **Visibility**: Select **Private** (keeps your code private)
   - **DO NOT** check "Add a README file" (we already have one)
4. Click **"Create repository"**

### Step 2.3: Upload Your Files to GitHub

**Option A: Using GitHub's Web Interface (Easiest)**

1. On your new repository page, you'll see "Quick setup" instructions
2. Click **"uploading an existing file"** link
3. Open the extracted `nc-dashboard` folder on your computer
4. Select ALL files and folders inside:
   - `.gitignore`
   - `.streamlit` (folder)
   - `README.md`
   - `app.py`
   - `pyproject.toml`
   - `requirements.txt`
   - `src` (folder)
   - `tests` (folder)
5. Drag and drop them into the GitHub upload area
6. Scroll down, add commit message: `Initial upload of NC Dashboard`
7. Click **"Commit changes"**

**Option B: Using GitHub Desktop (More Professional)**

1. Download GitHub Desktop: [https://desktop.github.com](https://desktop.github.com)
2. Install and sign in with your GitHub account
3. Click **"Clone a repository"** → Select your `nc-dashboard` repo
4. Choose where to save it locally
5. Copy all the extracted files into that folder
6. In GitHub Desktop, you'll see all the changes
7. Type a summary: `Initial upload`
8. Click **"Commit to main"**
9. Click **"Push origin"** to upload to GitHub

### Step 2.4: Verify Your Upload

1. Go to your repository on GitHub: `https://github.com/YOUR-USERNAME/nc-dashboard`
2. You should see all your files listed:
   ```
   .streamlit/
   src/
   tests/
   .gitignore
   README.md
   app.py
   pyproject.toml
   requirements.txt
   ```

---

## Part 3: Setting Up Google Cloud Credentials

This is the most complex part, but I'll walk you through it step by step.

### Step 3.1: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Sign in with your Google account
3. You may see a "Terms of Service" popup - accept it
4. At the top of the page, click the project dropdown (might say "Select a project")
5. Click **"NEW PROJECT"** in the popup window
6. Enter project details:
   - **Project name**: `calyx-nc-dashboard`
   - **Organization**: Leave as is (or select your organization if applicable)
7. Click **"CREATE"**
8. Wait 30 seconds for the project to be created
9. Make sure your new project is selected in the dropdown at the top

### Step 3.2: Enable the Google Sheets API

1. In the left sidebar, click **"APIs & Services"** → **"Library"**
2. In the search box, type `Google Sheets API`
3. Click on **"Google Sheets API"** in the results
4. Click the blue **"ENABLE"** button
5. Wait for it to enable

6. Go back to the API Library (click "APIs & Services" → "Library" again)
7. Search for `Google Drive API`
8. Click on **"Google Drive API"**
9. Click **"ENABLE"**

### Step 3.3: Create a Service Account

1. In the left sidebar, click **"APIs & Services"** → **"Credentials"**
2. Click **"+ CREATE CREDENTIALS"** at the top
3. Select **"Service account"**
4. Fill in the details:
   - **Service account name**: `nc-dashboard-reader`
   - **Service account ID**: (auto-fills, leave it)
   - **Description**: `Reads NC data from Google Sheets`
5. Click **"CREATE AND CONTINUE"**
6. For "Grant this service account access" - click **"CONTINUE"** (skip this)
7. For "Grant users access" - click **"DONE"** (skip this)

### Step 3.4: Create and Download the JSON Key

1. You should now see your service account in the list
2. Click on the service account email (e.g., `nc-dashboard-reader@calyx-nc-dashboard.iam.gserviceaccount.com`)
3. Click the **"KEYS"** tab at the top
4. Click **"ADD KEY"** → **"Create new key"**
5. Select **"JSON"** format
6. Click **"CREATE"**
7. **A JSON file will automatically download** - this is your credentials file!
8. **IMPORTANT**: Save this file somewhere safe. You'll need it in the next steps.
9. **NEVER share this file or commit it to GitHub**

### Step 3.5: Copy the Service Account Email

1. Go back to the service account details page
2. Find and copy the **email address** that looks like:
   ```
   nc-dashboard-reader@calyx-nc-dashboard.iam.gserviceaccount.com
   ```
3. Save this email - you'll need it next

### Step 3.6: Share Your Google Sheet with the Service Account

1. Open your Google Sheet with the NC data:
   ```
   https://docs.google.com/spreadsheets/d/15JhBZ_7aHHZA1W1qsoC2163borL6RYjk0xTDWPmWPfA
   ```
2. Click the **"Share"** button (top right, green button)
3. In the "Add people and groups" field, paste the service account email:
   ```
   nc-dashboard-reader@calyx-nc-dashboard.iam.gserviceaccount.com
   ```
4. Make sure it says **"Viewer"** (not Editor)
5. **Uncheck** "Notify people" (service accounts can't receive emails)
6. Click **"Share"**
7. If it asks to share anyway, click **"Share anyway"**

---

## Part 4: Running Locally (Optional)

Skip to Part 5 if you just want to deploy to the cloud.

### Step 4.1: Install Python

1. Go to [https://www.python.org/downloads/](https://www.python.org/downloads/)
2. Download Python 3.11 or newer
3. Run the installer
4. **IMPORTANT**: Check the box that says **"Add Python to PATH"**
5. Click "Install Now"

### Step 4.2: Open Command Prompt/Terminal

**Windows:**
1. Press `Windows key + R`
2. Type `cmd` and press Enter

**Mac:**
1. Press `Cmd + Space`
2. Type `Terminal` and press Enter

### Step 4.3: Navigate to Your Project Folder

```bash
# Windows example:
cd C:\Users\Xander\Documents\nc-dashboard

# Mac example:
cd ~/Documents/nc-dashboard
```

### Step 4.4: Create a Virtual Environment

```bash
# Create the virtual environment
python -m venv venv

# Activate it (Windows)
venv\Scripts\activate

# Activate it (Mac/Linux)
source venv/bin/activate
```

You should see `(venv)` at the start of your command line.

### Step 4.5: Install Dependencies

```bash
pip install -r requirements.txt
```

Wait for all packages to install (may take a few minutes).

### Step 4.6: Set Up Local Secrets

1. Navigate to the `.streamlit` folder in your project
2. Copy `secrets.toml.template` and rename the copy to `secrets.toml`
3. Open `secrets.toml` in a text editor (Notepad, VS Code, etc.)
4. Open the JSON file you downloaded from Google Cloud
5. Copy the values from the JSON into the secrets.toml file:

**Your JSON file looks like this:**
```json
{
  "type": "service_account",
  "project_id": "calyx-nc-dashboard",
  "private_key_id": "abc123...",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIE...\n-----END PRIVATE KEY-----\n",
  "client_email": "nc-dashboard-reader@calyx-nc-dashboard.iam.gserviceaccount.com",
  "client_id": "123456789",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/..."
}
```

**Your secrets.toml should look like this:**
```toml
[google_sheets]
spreadsheet_id = "15JhBZ_7aHHZA1W1qsoC2163borL6RYjk0xTDWPmWPfA"
sheet_name = "Non-Conformance Details"

[gcp_service_account]
type = "service_account"
project_id = "calyx-nc-dashboard"
private_key_id = "abc123..."
private_key = "-----BEGIN PRIVATE KEY-----\nMIIE...\n-----END PRIVATE KEY-----\n"
client_email = "nc-dashboard-reader@calyx-nc-dashboard.iam.gserviceaccount.com"
client_id = "123456789"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/..."
```

### Step 4.7: Run the Dashboard

```bash
streamlit run app.py
```

Your browser should automatically open to `http://localhost:8501` with your dashboard!

---

## Part 5: Deploying to Streamlit Cloud (Recommended)

This is the easiest way to run your dashboard - no installation needed!

### Step 5.1: Create a Streamlit Cloud Account

1. Go to [https://share.streamlit.io](https://share.streamlit.io)
2. Click **"Sign in with GitHub"**
3. Authorize Streamlit to access your GitHub account
4. Complete any additional signup steps

### Step 5.2: Deploy Your App

1. Once logged in, click **"New app"** button
2. Fill in the deployment settings:

   **Repository**: 
   - Select your GitHub account
   - Find and select `nc-dashboard`
   
   **Branch**: `main`
   
   **Main file path**: `app.py`

3. Click **"Advanced settings"** to expand

### Step 5.3: Add Your Secrets

1. In the Advanced settings, find the **"Secrets"** section
2. You need to paste your secrets here. Open the JSON file you downloaded from Google Cloud.
3. Copy and paste the following into the Secrets box, replacing the values with your actual credentials:

```toml
[google_sheets]
spreadsheet_id = "15JhBZ_7aHHZA1W1qsoC2163borL6RYjk0xTDWPmWPfA"
sheet_name = "Non-Conformance Details"

[gcp_service_account]
type = "service_account"
project_id = "YOUR_PROJECT_ID"
private_key_id = "YOUR_PRIVATE_KEY_ID"
private_key = "-----BEGIN PRIVATE KEY-----\nYOUR_ENTIRE_PRIVATE_KEY_HERE\n-----END PRIVATE KEY-----\n"
client_email = "YOUR_SERVICE_ACCOUNT_EMAIL"
client_id = "YOUR_CLIENT_ID"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "YOUR_CERT_URL"
```

**IMPORTANT for the private_key:**
- The private key in your JSON file has `\n` characters for line breaks
- You need to keep these `\n` characters - don't convert them to actual line breaks
- Copy the entire private_key value exactly as it appears in the JSON

### Step 5.4: Deploy

1. Click **"Deploy!"**
2. Wait 2-5 minutes for the app to build and deploy
3. You'll see a log showing the build progress
4. Once complete, you'll get a URL like: `https://your-app-name.streamlit.app`

### Step 5.5: Access Your Dashboard

1. Your dashboard is now live at the URL provided!
2. Bookmark this URL for easy access
3. Share the URL with colleagues who need access

---

## Part 6: Troubleshooting

### Problem: "Spreadsheet not found" Error

**Cause**: The service account doesn't have access to the sheet.

**Solution**:
1. Go to your Google Sheet
2. Click Share
3. Verify the service account email is listed
4. If not, add it again with Viewer access

### Problem: "Invalid credentials" Error

**Cause**: The secrets aren't configured correctly.

**Solution**:
1. Double-check that all values from the JSON are copied correctly
2. Make sure the private_key includes the `\n` characters
3. Verify there are no extra spaces or quotes

### Problem: "No data available" Warning

**Cause**: The sheet name doesn't match.

**Solution**:
1. Check your Google Sheet tab name
2. It should be exactly: `Non-Conformance Details`
3. Update the `sheet_name` in secrets if different

### Problem: Build Fails on Streamlit Cloud

**Cause**: Usually a missing file or syntax error.

**Solution**:
1. Check the build logs for specific errors
2. Verify all files were uploaded to GitHub
3. Make sure `requirements.txt` is in the root folder

### Problem: "Module not found" Error

**Cause**: Dependencies aren't installed correctly.

**Solution**:
1. Verify `requirements.txt` exists and contains all packages
2. Try redeploying the app

---

## Getting Help

If you run into issues:

1. **Check the Streamlit logs**: In Streamlit Cloud, click "Manage app" → "Logs"
2. **Google the error message**: Most errors have solutions online
3. **Ask Claude**: Describe the error and I'll help you fix it

---

## Quick Reference Card

| Task | Where to Do It |
|------|----------------|
| View your code | GitHub.com → Your repository |
| Update code | GitHub.com → Click file → Edit |
| Add secrets | Streamlit Cloud → App settings → Secrets |
| View app logs | Streamlit Cloud → Manage app → Logs |
| Redeploy | Streamlit Cloud → Manage app → Reboot |
| Share access | Share the Streamlit app URL |

---

## Security Reminders

⚠️ **NEVER do these things:**
- Never commit `secrets.toml` to GitHub
- Never share your JSON credentials file
- Never post your private key anywhere public
- Never give the service account Editor access (Viewer is enough)

✅ **ALWAYS do these things:**
- Keep your JSON credentials file in a safe place
- Use Streamlit's secrets management for deployment
- Regularly review who has access to your Google Sheet

---

Congratulations! You now have a fully deployed NC Dashboard! 🎉
