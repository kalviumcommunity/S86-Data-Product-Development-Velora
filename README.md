# Velora – Customer Complaint Analytics & Churn Prevention Dashboard

## Project Overview

Velora is a customer support analytics platform that connects customer complaint data with cancellation behaviour.

The project helps support and retention teams:

* Identify unresolved complaints
* Analyze repeated complaints
* Monitor escalated cases
* Measure resolution time
* Analyze complaint-linked churn
* Identify high-priority customers

## Technology Stack

* Python
* Pandas
* NumPy
* SQLite
* Streamlit
* Plotly
* GitHub
* GitHub Actions

## Project Structure

```text id="a7ktnf"
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

* `data/raw/` — Original datasets
* `data/processed/` — Cleaned datasets
* `notebooks/` — Analysis notebooks
* `scripts/` — Python scripts
* `output/` — Generated reports and files
* `app/` — Streamlit dashboard code
* `database/` — SQLite database

## First-Time Setup on Windows

### 1. Clone the Repository

```cmd id="b7gv3e"
git clone <your-github-repository-url>
cd velora
```

### 2. Create Virtual Environment

```cmd id="7rs6nq"
python -m venv venv
```

### 3. Activate Virtual Environment

```cmd id="bjtw1b"
venv\Scripts\activate
```

After activation, `(venv)` should appear in the terminal.

### 4. Install Dependencies

```cmd id="v4ekhe"
pip install -r requirements.txt
```

### 5. Run the Project

```cmd id="yzn06p"
streamlit run app\app.py
```

If the command does not work, use:

```cmd id="ewg5vg"
python -m streamlit run app\app.py
```

## Setup for Other Teammates

A new teammate should run:

```cmd id="s0kgwk"
git clone <your-github-repository-url>
cd velora
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
streamlit run app\app.py
```

Each teammate creates their own virtual environment. The `venv` folder should not be shared or committed to GitHub.

## Running the Project After Many Days

If the project is already set up on your computer, do not create the virtual environment again.

Open Command Prompt and run:

```cmd id="whxfy9"
cd C:\path\to\velora
git pull
venv\Scripts\activate
pip install -r requirements.txt
streamlit run app\app.py
```

Replace `C:\path\to\velora` with your actual project location.

Example:

```cmd id="fvcjyn"
cd C:\Users\YourName\Documents\velora
```

## Quick Start for Daily Use

If there are no new dependency changes:

```cmd id="sl6pkn"
cd C:\path\to\velora
venv\Scripts\activate
git pull
streamlit run app\app.py
```

## Stop the Project

Press:

```text id="p2wnpe"
Ctrl + C
```

## Deactivate Virtual Environment

```cmd id="v4tmzc"
deactivate
```


