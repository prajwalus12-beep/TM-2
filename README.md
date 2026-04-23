# Timesheet Management System

## Overview
The Timesheet Management System is a comprehensive Streamlit-based application designed for efficient time tracking and project management. It provides a secure platform for employees to log their daily work hours against specific projects and for administrators to oversee operations, manage resources, and generate reports.

### Key Features
- **User Authentication**: Secure login with CAPTCHA and automated account lockout after 5 failed attempts.
- **Time Tracking**: Easy-to-use interface for employees to add, edit, and delete daily timesheet entries.
- **Admin Dashboard**: Full control over employee and project management, including assignment of projects to specific resources.
- **Reporting**: Detailed project-wise and employee-wise reports with export capabilities.
- **Data Security**: Encryption of sensitive project information and secure password hashing (bcrypt).
- **Timezone Aware**: Standardized UTC-based lockout system for consistent cross-region performance.

---

## Getting Started

### Prerequisites
- Python 3.8 or higher
- Pip (Python Package Installer)
- Access to a Supabase database

### Installation

1. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd Timesheet-App-Version-3
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Database Initialization**
   The application uses Supabase for data storage. Ensure your database schema is set up according to the project's requirements.

---

## Configuration

### Secrets Setup
The application requires specific credentials and keys to be configured in a `.streamlit/secrets.toml` file. Create this file in the root of your project:

```toml
[postgres]
SUPABASE_URL = "YOUR_SUPABASE_PROJECT_URL"
SUPABASE_ANON_KEY = "YOUR_SUPABASE_ANON_KEY"
encryption_key = "YOUR_FERNET_ENCRYPTION_KEY"
```

> [!IMPORTANT]
> Never commit your actual `secrets.toml` file to version control.

---

## Running the Application

To start the development server, run:

```bash
streamlit run app.py
```

The application will be accessible at `http://localhost:8501`.

---

## Deployment
This application is designed to be easily deployed on **Streamlit Cloud**. When deploying:
1. Push your code to a GitHub repository.
2. Connect the repository to Streamlit Cloud.
3. Paste the contents of your `secrets.toml` into the **Secrets** section of the Streamlit Cloud app settings.

---

## Project Structure
- `app.py`: Main entry point and routing logic.
- `pages/`: Individual application pages (Login, Timesheet, Reports, Admin).
- `services/`: Core business logic including authentication (`auth_service.py`).
- `database/`: Database connection and query logic (`queries.py`).
- `components/`: Reusable UI components (Sidebar, Dialogs).
- `assets/`: Static assets like CSS and images.
- `utils/`: Utility functions (Captcha generation, data processing).
