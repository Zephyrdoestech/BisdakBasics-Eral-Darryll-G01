# Bisdak Basics

Bisdak Basics is a Django web application for learning practical Cebuano/Bisaya. It will support learner and administrator accounts, situational lessons, a searchable phrasebook, assessments, and progress monitoring.

## Current checkpoint

This repository contains the initial Django project setup. Account registration, authentication pages, role dashboards, and profile management are planned for a later checkpoint.

## Requirements

- Python 3.10 or newer
- PostgreSQL 14 or newer

SQLite is not configured. The project requires a PostgreSQL `DATABASE_URL`.

## Local setup

1. Create and activate a virtual environment:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

2. Install dependencies:

   ```powershell
   python -m pip install -r requirements.txt
   ```

3. Create a PostgreSQL database named `bisdak_basics` (or choose another name).

4. Copy `.env.example` to `.env` and set `SECRET_KEY` and `DATABASE_URL` to your local values.

5. Apply Django's initial migrations and start the development server:

   ```powershell
   python manage.py migrate
   python manage.py runserver
   ```

The site will be available at <http://127.0.0.1:8000/>.

## Repository naming

The requested repository naming pattern is `SystemName-Lastname-Firstname-Section`. The local folder is currently named `BisdakBasics`; rename the GitHub repository to the required pattern when the section value is known. Keep `.env`, virtual environments, and Python cache files out of commits.
