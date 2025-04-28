# 🌡️ Fluke DewK 1620A Thermohygrometer Management System

## 📑 Table of Contents
1. [Project Overview](#project-overview)
2. [Features](#features)
3. [Prerequisites](#prerequisites)
4. [Installation](#installation)
5. [Running with Docker Compose](#running-with-docker-compose)
6. [Configuration](#configuration)
7. [Usage](#usage)
8. [Project Structure](#project-structure)
9. [Technical Stack](#technical-stack)
10. [Acknowledgments](#acknowledgments)

## 📌 Project Overview

The **Fluke DewK 1620A Thermohygrometer Management System** is a web application designed to manage and monitor Fluke DewK 1620A thermohygrometers. This system provides a user-friendly interface for real-time data display, device management, and data analysis of temperature and humidity readings.

The project uses several technologies, including **Python, Django, SQLite, and PyVISA**, to create a web application that interfaces with the Fluke DewK 1620A device.

## 🚀 Features

✅ Real-time data display  
✅ Device management  
✅ Data visualization  
✅ Data export (CSV format)  
✅ User management  
✅ Secure login  
✅ Alarm management  
✅ Calibration tracking  

## ⚙️ Prerequisites

Before setting up and installing, ensure you have the following:

- A compatible operating system (**Windows, macOS, or Linux**)
- **Python 3.7+** installed
- **UV package manager** ([GitHub - astral-sh/uv](https://github.com/astral-sh/uv))
   ```sh
   pip install uv
   ```
- A code editor or IDE (**VS Code, PyCharm**)
- **Docker & Docker Compose** installed
- Fluke DewK 1620A Thermohygrometer device connected

## 🛠 Installation (Manual Setup)

1️⃣ Clone the repository:
   ```sh
   git clone https://github.com/your-repo/fluke-dewk-1620a-management.git
   cd fluke-dewk-1620a-management
   ```

2️⃣ Activate the proxy (if needed, for PowerShell):
   ```powershell
   .\ProxyManager.ps1 -on
   ```
   *Replace `"your_proxy_address:port"` with your actual proxy server address and port.*

3️⃣ Create and activate a virtual environment using UV:
   ```sh
   uv venv
   ```

4️⃣ Activate the virtual environment:
   - **Windows:**
     ```sh
     ./.venv/Scripts/activate
     ```
   - **Linux/macOS:**
     ```sh
     source ./.venv/bin/activate
     ```

5️⃣ Install dependencies:
   ```sh
   uv sync
   ```

## 🐳 Running with Docker Compose

For a quick and easy setup, use **Docker Compose**:

1️⃣ Ensure Docker and Docker Compose are installed.

2️⃣ Build and run the containers:
   ```sh
   docker-compose up --build
   ```

3️⃣ The application should now be accessible at:
   ```
   http://localhost:8000
   ```

4️⃣ To stop the containers:
   ```sh
   docker-compose down
   ```

✅ This method automatically sets up all dependencies, database migrations, and starts the application.

## ⚙️ Configuration

1️⃣ Apply database migrations:
   ```sh
   python manage.py migrate
   ```

2️⃣ Create a superuser account:
   ```sh
   python manage.py createsuperuser
   ```

## ▶️ Usage

1️⃣ Start the Django development server:
   ```sh
   # Local development only
   python manage.py runserver
   
   # Allow external connections (accessible from other devices on network)
   python manage.py runserver 0.0.0.0:8000
   ```

2️⃣ Open your browser and visit:
   ```
   http://localhost:8000
   ```

3️⃣ Log in with your credentials.

📌 **API Documentation (Swagger):**
- Swagger UI: `http://localhost:8000/swagger/`

## 📂 Project Structure

```
fluke_data/              # Core functionality files (views, models, visa_communication)
fluke_dewk_1620A_project/ # Project configuration (settings, urls, wsgi)
staticfiles/             # CSS, JavaScript, images
thermohygrometer/        # Fluke DewK 1620A interaction files
```

## 🏗 Technical Stack

- **Python**: Primary programming language
- **PyVISA**: Ethernet communication with the Fluke DewK 1620A device
- **SQLite**: Local data storage
- **Django**: Web application framework
- **Docker & Docker Compose**: Containerization

---

💡 **Now you are all set! Enjoy managing your Fluke DewK 1620A Thermohygrometers effortlessly!** 🚀
