# GitHub Publishing Checklist

Author: Md Imamuddin

*This repository has 144 files and is about 13MB total, with the largest single file at 2.5MB — well within GitHub's limits (GitHub warns at 50MB per file and blocks anything over 100MB, so no special storage is needed).*

---

## 1. Before You Publish

- [ ] **Remove all `__pycache__` folders and `.pyc` files**
  ```bash
  find . -name "__pycache__" -type d -exec rm -rf {} +
  find . -name "*.pyc" -delete
  ```
- [ ] **Check for accidentally committed secrets.** This project doesn't store any real passwords or keys in code — only `.env.example` with placeholder values. Still, it's good practice to double check:
  ```bash
  grep -r "password\|api_key\|secret" --include="*.py" --include="*.md" . | grep -v ".env.example"
  ```
- [ ] **Confirm `.env` is not tracked** (only `.env.example` should be tracked):
  ```bash
  git status --ignored | grep .env
  ```
- [ ] **Check no file is too large:**
  ```bash
  find . -type f -size +50M
  ```

## 2. Set Up the Repository

- [ ] Create the repo on GitHub, named `customer-churn-intelligence-platform`
- [ ] Set it to Public
- [ ] Don't add a README/license/gitignore from GitHub's side — this project already has all three
- [ ] Add topics: `churn-prediction`, `machine-learning`, `power-bi`, `streamlit`, `sql`, `business-intelligence`, `customer-analytics`, `data-engineering`, `python`
- [ ] Add a short description: *"End-to-end churn intelligence platform built on real telecom data — SQL, Power BI, machine learning, and a live Streamlit app."*

## 3. First Commit

```bash
cd customer-churn-intelligence-platform
git init
git add .
git status
git commit -m "Initial commit: Customer Subscription & Churn Intelligence Platform"
git branch -M main
git remote add origin https://github.com/mdimamuddin/customer-churn-intelligence-platform.git
git push -u origin main
```

- [ ] After pushing, check on GitHub.com that `data/raw/Telco_customer_churn.xlsx` and the database files uploaded correctly (file sizes shown should be non-zero)

## 4. Polish the README Before Sharing

- [ ] Add 2–3 screenshots directly in the README using the images in `docs/portfolio_screenshots/`:
  ```markdown
  ![Churn by Contract Type](docs/portfolio_screenshots/02_churn_by_contract.png)
  ```
- [ ] Add a real `resume.pdf` to `streamlit_app/assets/` so the About page's download button works
- [ ] Optionally add badges near the top of the README:
  ```markdown
  ![Python](https://img.shields.io/badge/python-3.11%2B-blue)
  ![License](https://img.shields.io/badge/license-MIT-green)
  ```

## 5. Deployment Options

### Streamlit Community Cloud (free hosting for a live demo)
- [ ] Push this repo to GitHub first
- [ ] Go to share.streamlit.io → New app → select this repo → set the main file to `streamlit_app/app.py`
- [ ] Use `streamlit_app/requirements.txt` as the requirements file
- [ ] Note: the `shap` library may not always install cleanly on the hosting platform — if that happens, the app automatically switches to its built-in backup method (permutation importance) for the model explainability page, so it won't break
- [ ] Once live, add the demo link to your README and to the About page's links

### Power BI Service (if you have access to a workspace)
- [ ] Build the `.pbix` file locally first, using the guide in `docs/powerbi_build_walkthrough/`
- [ ] File → Publish → choose your workspace
- [ ] Note: the published report will use the imported CSV data, not a live database connection, since this project's SQL is written for PostgreSQL but no public demo server is included

## 6. Nice-to-Haves

- [ ] Pin the repo on your GitHub profile
- [ ] Add a short screen recording of the app or dashboard and link it in the README
- [ ] Create a GitHub Release (v1.0.0) once you're happy with the repo
- [ ] Tag future updates as new releases instead of rewriting the first one

## 7. Final Check

- [ ] Clone the repo fresh into a new folder and run everything from the README, start to finish, exactly as someone new to the project would:
  ```bash
  git clone https://github.com/mdimamuddin/customer-churn-intelligence-platform.git
  cd customer-churn-intelligence-platform
  pip install -r requirements.txt
  python3 -m src.data_engineering.etl_pipeline
  ```
- [ ] Confirm it runs without needing anything outside the repository — everything required, including the real source data, is already included
