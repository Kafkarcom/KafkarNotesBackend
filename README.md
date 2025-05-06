# NoteTaker SaaS Application

A web-based note-taking application built with React, Flask, and PostgreSQL. Users can create, store, and manage notes.

## Features

- User authentication (signup, login)
- Create, read, update, and delete notes
- Responsive UI design
- Secure API endpoints with JWT authentication

## Project Structure

```
notes-app/
├── database/           # Database scripts
└── README.md           # This documentation
```

## Prerequisites

- Node.js (v14+)
- Python (v3.8+)
- PostgreSQL (v12+)

## Installation

### 1. Database Setup

```bash
# Create PostgreSQL database
psql -U postgres -f database/setup.sql
```

### 2. Backend Setup


# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables (optional)
# Windows
set DATABASE_URL=postgresql://postgres:postgres@localhost/notes_db
set SECRET_KEY=your_secret_key_here

# macOS/Linux
export DATABASE_URL=postgresql://postgres:postgres@localhost/notes_db
export SECRET_KEY=your_secret_key_here

# Run the backend server
python app.py
```

The backend server will start on http://localhost:5000.
