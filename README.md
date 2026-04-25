# Timesheet Management System

## Overview
The Timesheet Management System is a comprehensive Streamlit-based application designed for efficient time tracking and project management. It features a modern React-based "Project Update" tool for advanced data editing and reporting.

### Key Features
- **Modern Project Update UI**: Custom React-based interface with inline editing, dirty-state highlighting, and infinite scrolling.
- **User Authentication**: Secure login with CAPTCHA and automated account lockout.
- **Time Tracking**: Easy-to-use interface for employees to log hours.
- **Admin Dashboard**: Comprehensive management of employees and projects.
- **Reporting**: Detailed project and employee reports with native Excel export.
- **Data Security**: Encryption of sensitive information and secure password hashing.

---

## Getting Started

### Prerequisites
- **Python 3.8+**
- **Node.js 16+ & npm** (Required for the React components)
- **Supabase Account** (For database and authentication)

### Installation & Setup

1. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd Timesheet-App-version-2
   ```

2. **Python Environment Setup**
   It is recommended to use a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **React Component Setup**
   The "Project Update" feature uses a React frontend that must be built before use:
   ```bash
   cd components/project_update_react/frontend
   npm install
   npm run build
   cd ../../../
   ```

---

## Configuration

### Secrets Setup
The application requires credentials in `.streamlit/secrets.toml`. Create this file in the root directory:

```toml
[postgres]
SUPABASE_URL = "YOUR_SUPABASE_PROJECT_URL"
SUPABASE_ANON_KEY = "YOUR_SUPABASE_ANON_KEY"
encryption_key = "YOUR_FERNET_ENCRYPTION_KEY"
```

> [!IMPORTANT]
> Ensure your Supabase database schema matches the provided `database.sql` files.

---

## Running the Application

### Production Mode
Once the React component is built, you can run the main application directly:
```bash
streamlit run app.py
```

### Development Mode (React)
If you are making changes to the React component:
1. Start the React dev server:
   ```bash
   cd components/project_update_react/frontend
   npm start
   ```
2. The component will now hot-reload changes. For production deployment, remember to run `npm run build`.

---

## Project Structure
- `app.py`: Main entry point and routing.
- `pages/`: Individual application pages.
  - `project_update_page_v2.py`: Host for the React Project Update tool.
- `components/`: 
  - `project_update_react/`: The React-Streamlit bridge.
    - `frontend/`: React source code (CSS, JSX).
- `database/`: Database connection and Supabase queries.
- `services/`: Business logic (auth, etc).
- `assets/`: Static assets and styling.
- `utils/`: Utility functions.
