# Flask Todo Application

A modern, responsive, full-stack Todo application built with Flask. This project focuses on a seamless user experience, featuring a dynamic masonry grid layout and optimistic UI updates for instant feedback.

## ✨ Features

* **Frictionless Onboarding:** Automatic "Guest User" shadow account creation so users can try the app instantly without registering.
* **Smart Layout:** A fully responsive, Google Keep-style masonry grid that automatically centers and adjusts based on the number of active lists.
* **Optimistic UI:** Tasks and lists update instantly in the browser before the server responds, providing a lightning-fast native app feel.
* **In-Place Editing:** Click-to-edit list titles with seamless transitions.
* **Dark/Light Mode:** Full theme toggling built with Tailwind CSS.

## 🛠️ Tech Stack

* **Backend:** Python, Flask, SQLAlchemy (PostgreSQL)
* **Frontend:** HTML5, Jinja2 Templates, Vanilla JavaScript (Fetch API)
* **Styling:** Tailwind CSS 
* **Architecture:** Decoupled Service Layer for clean database interactions.

## 🚀 Local Development Setup

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd <your-repo-name>
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up the Database:**
   * Ensure PostgreSQL is running locally.
   * Create a local database (e.g., `todo_app_db`).
   * Set your environment variables (e.g., `DATABASE_URL`, `FLASK_SECRET_KEY`).

5. **Run the application:**
   ```bash
   flask run
   ```
   *The app will be available at http://127.0.0.1:5000*