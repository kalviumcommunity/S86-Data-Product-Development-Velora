# Velora – Customer Complaint Analytics & Churn Prevention Dashboard

## About the Project

Velora is a customer support analytics platform designed to connect customer complaint data with cancellation behaviour.

Customer support information such as complaints, escalations, ticket status, and resolution time is often stored separately from cancellation data. Velora combines this information into one analytics platform to help organizations identify complaint-related churn patterns and take proactive retention actions.

The project provides an interactive Streamlit dashboard for support managers, retention teams, and business leaders.

---

## Project Features

### 1. Executive Dashboard

Displays important KPIs such as:

* Total Customers
* Total Complaints
* Unresolved Complaints
* Escalated Complaints
* Average Resolution Time
* Cancelled Customers
* Complaint-Linked Churn Rate
* High-Priority Cases

### 2. Complaint Analytics

Helps users:

* Analyze complaints by category
* Identify unresolved complaints
* Detect repeated complaints
* View complaint trends over time

### 3. Escalation Analytics

Allows users to:

* Monitor escalated complaints
* View escalation levels
* Identify frequently escalated categories
* Find unresolved escalated cases

### 4. Resolution Analytics

Provides insights into:

* Average resolution time
* Resolution time by category
* Delayed complaint cases
* Resolved vs unresolved complaints

### 5. Customer Journey

Users can search by Customer ID and view:

* Complaint history
* Ticket categories
* Ticket status
* Escalation history
* Resolution time
* Cancellation status
* Customer priority level

### 6. Churn Analytics

Analyzes:

* Churn by complaint category
* Churn by escalation status
* Churn by resolution time
* Churn among repeated complainants

### 7. Customer Priority Scoring

Customers are assigned a priority level based on factors such as:

* Unresolved complaints
* Multiple complaints
* Escalated cases
* Long resolution times

Priority levels:

* High
* Medium
* Low

### 8. Alerts and Priority Cases

Identifies customers who may require urgent attention because of:

* Unresolved complaints
* Repeated complaints
* Escalated tickets
* Long resolution times
* High priority scores

### 9. Interactive Filters

Users can filter dashboard data by:

* Customer
* Ticket Category
* Ticket Status
* Escalation Status
* Support Channel
* Customer Segment
* Date Range
* Priority Level

### 10. CSV Export

Users can export filtered dashboard data as CSV for further analysis and reporting.

---

## Technology Stack

* Python
* Pandas
* NumPy
* SQLite
* Streamlit
* Plotly
* GitHub
* GitHub Actions

---

## Project Structure

```text id="e96uxc"
velora/
├── data/
│   ├── raw/
│   └── processed/
├── notebooks/
├── scripts/
├── output/
├── app/
├── database/
├── .gitignore
├── requirements.txt
└── README.md
```

### Folder Description

* `data/raw/` — Original datasets
* `data/processed/` — Cleaned and processed datasets
* `notebooks/` — Jupyter notebooks for analysis
* `scripts/` — Python scripts for data processing
* `output/` — Generated reports and exported files
* `app/` — Streamlit dashboard code
* `database/` — SQLite database files

---

## First-Time Setup on Windows

### 1. Clone the Repository

```cmd id="45b6s4"
git clone <your-github-repository-url>
cd velora
```

### 2. Create Virtual Environment

```cmd id="e9hjko"
python -m venv venv
```

### 3. Activate Virtual Environment

```cmd id="32qdmf"
venv\Scripts\activate
```

After activation, `(venv)` should appear in the terminal.

### 4. Install Dependencies

```cmd id="55t0tv"
pip install -r requirements.txt
```

### 5. Run the Streamlit Dashboard

```cmd id="7mmly5"
streamlit run app\app.py
```

If the command does not work, use:

```cmd id="f3jyba"
python -m streamlit run app\app.py
```

---

## Setup for Other Teammates

A new teammate should run the following commands:

```cmd id="8dlk9n"
git clone <your-github-repository-url>
cd velora
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
streamlit run app\app.py
```

Each teammate should create their own virtual environment.

The `venv` folder should never be committed to GitHub.

---

## Running the Project After Many Days

If the project is already set up on your computer, you do not need to create the virtual environment again.

Open Command Prompt and move to the project folder:

```cmd id="k0gufr"
cd C:\path\to\velora
```

Get the latest team changes:

```cmd id="87nn5q"
git pull
```

Activate the existing virtual environment:

```cmd id="cnsu3f"
venv\Scripts\activate
```

Update dependencies if `requirements.txt` has changed:

```cmd id="oxp7qh"
pip install -r requirements.txt
```

Run the dashboard:

```cmd id="4r3ev6"
streamlit run app\app.py
```

---

## Quick Start for Daily Use

If the project is already set up:

```cmd id="vgrfxe"
cd C:\path\to\velora
git pull
venv\Scripts\activate
streamlit run app\app.py
```

Replace `C:\path\to\velora` with the actual location of the project.

---

## Stop the Project

Press:

```text id="2b2s3t"
Ctrl + C
```

---

## Deactivate Virtual Environment

After finishing work:

```cmd id="kq5mc7"
deactivate
```


