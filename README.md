# Fluke DewK 1620A Thermohygrometer Management System

## Table of Contents
1. [Project Overview](#project-overview)
2. [Features](#features)
3. [Prerequisites](#prerequisites)
4. [Installation](#installation)
5. [Configuration](#configuration)
6. [Usage](#usage)
7. [Project Structure](#project-structure)
8. [Technical Stack](#technical-stack)
9. [Acknowledgments](#acknowledgments)

## Project Overview

The Fluke DewK 1620A Thermohygrometer Management System is a web application designed to manage and monitor Fluke DewK 1620A thermohygrometers. This system provides a user-friendly interface for real-time data display, device management, and data analysis of temperature and humidity readings.

The project uses several technologies, including Python, Django, SQLite, and PyVISA, to create a web application that can interface with the Fluke DewK 1620A device.

## Features

- Real-time data display
- Device management
- Data visualization
- Data export (CSV format)
- User management
- Secure login
- Alarm management
- Calibration tracking

## Prerequisites

Before setting up and installing the Fluke DewK 1620A Thermohygrometer Management System, ensure that you have the following:

- A compatible operating system (Windows, macOS, or Linux)
- Python 3.7 or later installed on your system
- A code editor or IDE of your choice (e.g., Visual Studio Code, PyCharm)
- The Fluke DewK 1620A Thermohygrometer device connected to your system

## Installation

1. Clone the project repository:
   ```
   git clone https://github.com/your-repo/fluke-dewk-1620a-management.git
   cd fluke-dewk-1620a-management
   ```

2. Set up a virtual environment:
   ```
   python -m venv fluke-dewk-env
   ```

3. Activate the virtual environment:   
   For Windows, use the following command:
   ```
   ./fluke-dewk-env/Scripts/activate
   ```
   
   For Linux, use the following command:
   ```
   source ./fluke-dewk-env/bin/activate
   ```

4. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Configuration

1. Set up the Django database:
   ```
   python manage.py migrate
   ```

2. Create a superuser account:
   ```
   python manage.py createsuperuser
   ```

## Usage

1. Start the Django development server:
   ```
   python manage.py runserver
   ```

2. Access the web application at `http://localhost:8000`

3. Log in with your credentials:
   - For managers: Use manager credentials to add or remove thermohygrometers, manage user accounts, and view real-time data on the dashboard.
   - For regular users: Use provided credentials to view data visualizations by selecting devices and date ranges, and export data to CSV format.

## Project Structure

The project is organized as follows:

- `fluke_data/`: Contains core functionality files (views.py, visa_communication.py, models.py, etc.)
- `fluke_dewk_1620A_project/`: Contains project configuration files (settings.py, urls.py, wsgi.py)
- `staticfiles/`: Contains static assets (CSS, JavaScript, images)
- `thermohygrometer/`: Contains files for interacting with the Fluke DewK 1620A device

## Technical Stack

- Python: Primary programming language
- PyVISA: Ethernet communication with the Fluke DewK 1620A device
- SQLite: Local data storage
- Django: Web application framework