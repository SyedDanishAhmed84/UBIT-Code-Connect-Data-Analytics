<div align="center">

# NexusMart Data Analytics

**From raw business data to clean, reliable, decision-ready reporting**

CODE//CONNECT '26 · Data Analytics Module

![Python](https://img.shields.io/badge/Python-Data%20Cleaning-3776AB?logo=python&logoColor=white)
![SQL](https://img.shields.io/badge/SQL-Database-4479A1?logo=databricks&logoColor=white)
![Power BI](https://img.shields.io/badge/Power%20BI-Dashboard-F2C811?logo=powerbi&logoColor=black)

</div>

---

## Table of Contents

1. [Overview](#overview)
2. [Team](#team)
3. [Solution Architecture](#solution-architecture)
4. [Datasets](#datasets)
5. [Repository Structure](#repository-structure)
6. [Technologies](#technologies)
7. [Getting Started](#getting-started)
8. [Data Handling Notes](#data-handling-notes)
9. [Security](#security)
10. [Acknowledgements](#acknowledgements)

---

## Overview

NexusMart is a fast-growing Pakistani online marketplace with more than 400 sellers, 12 product categories and operations across 40 cities. As the business has grown, data from different systems has become inconsistent and difficult to manage.

This project addresses that challenge by turning nine raw source files into a clean, structured and query-ready dataset, storing it in a SQL database, and connecting it to Power BI for business reporting.

**Period covered:** January 2024 to June 2025 · **Currency:** Pakistani Rupees (PKR)

---

## Team

| Team Member | Role | Responsibility |
|---|---|---|
| **Syed Danish Ahmed** | Database | Database design, SQL scripts and data storage |
| **Shahzaib** | Data Cleaning | Data profiling, cleaning, standardization and transformation |
| **Sameer** | Power BI | Dashboard development and business reporting |

**University:** _Your University_

---

## Solution Architecture

```
┌──────────────┐     ┌───────────────────┐     ┌──────────────┐     ┌───────────────┐
│  Raw source  │ ──▶ │  Python cleaning  │ ──▶ │ SQL database │ ──▶ │ Power BI      │
│  datasets    │     │  (Jupyter)        │     │              │     │ dashboard     │
└──────────────┘     └───────────────────┘     └──────────────┘     └───────────────┘
```

| Stage | Description |
|---|---|
| **1. Data cleaning** | Raw datasets are profiled, cleaned and standardized in a Python notebook |
| **2. Database** | Cleaned data is organized in a relational SQL database |
| **3. Reporting** | Power BI connects to the database and presents the business insights |

---

## Datasets

| Dataset | Description |
|---|---|
| `customers` | Customer information |
| `products` | Product catalog |
| `sellers` | Seller information |
| `locations` | City, province and region lookup |
| `orders` | Order headers |
| `order_items` | Individual product lines within orders |
| `payments` | Payment records |
| `shipping` | Courier and delivery records |
| `returns` | Return and refund requests |

---

## Repository Structure

| File | Description |
|---|---|
| `Data_Cleaning_Script.ipynb` | Python notebook for profiling, cleaning and standardizing the datasets |
| `nexus_mart.sql` | SQL script for the NexusMart database |
| `Power BI_data source.jpeg` | Screenshot of the Power BI data source configuration |
| `README.md` | Project documentation |

---

## Technologies

| Technology | Purpose |
|---|---|
| **Python** (pandas, Jupyter) | Data profiling, cleaning and transformation |
| **SQL** | Database design, storage and querying |
| **Power BI** | Interactive dashboards and business reporting |

---

## Getting Started

### Prerequisites

- Python 3.10 or later
- Jupyter Notebook, JupyterLab or Google Colab
- A SQL database server and a client capable of running `.sql` files
- Power BI Desktop

### Step 1: Clean the data

```bash
pip install pandas jupyter
jupyter notebook Data_Cleaning_Script.ipynb
```

Place the raw datasets in the location referenced at the start of the notebook, then run all cells from top to bottom. The notebook outputs the cleaned datasets.

### Step 2: Create the database

Run `nexus_mart.sql` in your SQL database to create the database objects, then load the cleaned data.

### Step 3: Connect Power BI

1. Open Power BI Desktop and select **Get Data → Database**.
2. Choose your database type and enter the server and database name.
3. Select **Import** mode and sign in with your database credentials.
4. Select the required tables and click **Load**.

Data source configuration used in this project:

![Power BI data source](Power%20BI_data%20source.jpeg)

---

## Data Handling Notes

- Dates written with slashes are interpreted as day/month/year.
- Valid order dates fall between 1 January 2024 and 30 June 2025.
- Returns with status *Rejected* are not treated as valid returns.
- Shipping fees are recorded once per order, not per order line.

---

## Security

Database credentials are never stored in this repository. Use environment variables or local configuration files that are excluded from version control.

---

## Acknowledgements

Developed for the **CODE//CONNECT '26** Data Analytics competition. The datasets belong to the competition organizers and are used for this competition only.
