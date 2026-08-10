# Velora

Customer Complaint Analytics & Churn Prevention Dashboard

Velora is a data analytics dashboard designed to help customer support teams proactively identify customers at risk of churn. By integrating complaint tickets, escalation records, resolution times, and cancellation data into a single platform, Velora enables organizations to move from reactive support to proactive customer retention.

---

## Problem Statement

Customer support teams manage ticket categories, escalation records, and resolution times separately, but unresolved complaints are never connected to cancellation behaviour, making churn prevention reactive instead of proactive.

---

## Solution

Velora brings together customer support data into a unified analytics platform that enables teams to:

- Monitor complaint trends
- Track escalated cases
- Analyze ticket resolution performance
- Identify customers at high risk of churn
- Understand customer support patterns
- Make data-driven business decisions

---

## Features

- Interactive multi-page analytics dashboard
- Customer complaint analysis
- Support performance monitoring
- Customer risk identification using priority scoring
- Individual customer journey tracking
- Churn analysis and visualization
- Executive business insights
- Interactive filtering and search
- Downloadable customer risk reports

---

## Dashboard Modules

### Home
Provides an overview of customer support performance through key performance indicators and summary visualizations.

### Support Analytics
Analyzes complaint categories, ticket status, escalation trends, and resolution performance.

### Customer Risk Center
Identifies customers requiring immediate attention using a priority scoring model and recommends proactive actions.

### Customer Journey
Displays the complete complaint history, ticket lifecycle, and support interactions for individual customers.

### Churn Analytics
Explores the relationship between complaints, escalations, resolution delays, and customer cancellations.

### Executive Insights
Summarizes business KPIs, support performance, churn trends, and strategic recommendations for decision-makers.

---

## Data Pipeline

The project follows an end-to-end data processing workflow:

1. Synthetic dataset generation
2. Data cleaning and preprocessing
3. Feature engineering
4. Customer priority scoring
5. Master dataset creation
6. SQLite database integration
7. Interactive dashboard visualization

---

## Tech Stack

| Category | Technologies |
|----------|--------------|
| Programming Language | Python |
| Dashboard | Streamlit |
| Data Processing | Pandas |
| Visualization | Plotly |
| Database | SQLite |
| Dataset Generation | Faker |

---

## Project Structure

```text
Velora/
│
├── assets/
│   └── velora_logo.png
│
├── data/
│   ├── customers.csv
│   ├── tickets.csv
│   ├── escalations.csv
│   ├── cancellations.csv
│   └── master_dataset.csv
│
├── database/
│   ├── create_database.py
│   └── velora.db
│
├── pages/
│   ├── 1_Home.py
│   ├── 2_Support_Analytics.py
│   ├── 3_Customer_Risk_Center.py
│   ├── 4_Customer_Journey.py
│   ├── 5_Churn_Analytics.py
│   └── 6_Executive_Insights.py
│
├── scripts/
│   ├── generate_data.py
│   ├── clean_data.py
│   ├── feature_engineering.py
│   └── load_database.py
│
├── utils/
│   ├── charts.py
│   ├── database.py
│   ├── filters.py
│   └── metrics.py
│
├── app.py
├── requirements.txt
└── README.md
```

---

## Installation

Clone the repository:

```bash
git clone https://github.com/kalviumcommunity/S86-Data-Product-Development-Velora.git
```

Navigate to the project folder:

```bash
cd S86-Data-Product-Development-Velora
```

Install the required packages:

```bash
pip install -r requirements.txt
```

---

## Run the Application

Start the Streamlit dashboard:

```bash
streamlit run app.py
```

The application will open in your default browser.

---

## Dashboard Preview

Add screenshots of the following pages:

- Home
- Support Analytics
- Customer Risk Center
- Customer Journey
- Churn Analytics
- Executive Insights

---

## Future Enhancements

- Machine learning–based churn prediction
- Real-time ticket monitoring
- Role-based authentication
- Email notifications for high-risk customers
- Integration with CRM platforms
- AI-powered recommendation engine

---

## Contributors

- Herald Keerthana Nukabatni
- P V Sonali
- B. Bhanu Sree

---

## License

This project was developed for educational purposes as part of the Kalvium Data Product Development program.
