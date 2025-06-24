# Replit.md - Old Snapshot 2.0

## Overview

Old Snapshot 2.0 is a Flask-based web application designed to process employee seniority-based line assignments for airline scheduling. The system takes bid data from employees and processes their preferences to award lines based on seniority order. The application provides a simple web interface for data input and displays results in a user-friendly format.

## System Architecture

The application follows a simple Flask web application architecture:

- **Frontend**: HTML templates with Bootstrap CSS framework and vanilla JavaScript for interactivity
- **Backend**: Flask web framework with Python 3.11
- **Data Processing**: In-memory processing using Python dataclasses and CSV parsing
- **Deployment**: Gunicorn WSGI server with autoscale deployment target
- **Development Environment**: Replit with Nix package management

## Key Components

### Backend Components

1. **Flask Application (`app.py`)**
   - Main application logic for bid processing
   - RESTful API endpoints for data submission
   - CSV parsing and data validation
   - Seniority-based line assignment algorithm

2. **Application Entry Point (`main.py`)**
   - Simple Flask application runner
   - Development server configuration

3. **Data Models**
   - `BidItem`: Represents employee bid with seniority position, ID, and preferences
   - `BidResult`: Contains assignment results with awarded lines and choice positions

### Frontend Components

1. **HTML Templates (`templates/index.html`)**
   - Bootstrap-based responsive design with dark theme
   - Mobile-optimized interface
   - Form for bid data input with detailed instructions
   - Results display area with download functionality

2. **JavaScript (`static/js/script.js`)**
   - Form submission handling with async/await
   - Mobile touch optimizations
   - Loading states and error handling
   - Results processing and CSV download functionality

3. **CSS (`static/css/style.css`)**
   - Mobile-first responsive design
   - Touch-friendly interface elements
   - Custom styling for bid data textarea and buttons

## Data Flow

1. **Input Processing**
   - Users paste bid data from airline scheduling systems
   - System supports two formats: "Schedule Bid Summary" and "View Bid Summary"
   - Data is parsed to extract employee information and preferences

2. **Bid Processing**
   - Employees are sorted by seniority (bid position)
   - Each employee is assigned their highest available preference
   - Results include awarded line, choice position, and status messages

3. **Output Generation**
   - Results displayed in responsive table format
   - CSV download functionality for further processing
   - Error handling for invalid data formats

## External Dependencies

### Python Packages
- **Flask 3.1.0**: Web framework for application structure
- **Gunicorn 23.0.0**: WSGI HTTP server for production deployment
- **Jinja2 3.1.6**: Templating engine (Flask dependency)
- **Email-validator**: Input validation utilities
- **Psycopg2-binary**: PostgreSQL adapter (available but not currently used)

### Frontend Dependencies
- **Bootstrap**: CSS framework via CDN (dark theme optimized)
- **Custom CSS**: Mobile-first responsive design

### System Dependencies
- **Python 3.11**: Runtime environment
- **PostgreSQL**: Database system (configured but not actively used)
- **OpenSSL**: Security and encryption support

## Deployment Strategy

The application is configured for deployment on Replit's platform:

1. **Development Mode**
   - Local Flask development server with debug enabled
   - Hot reload for code changes
   - Port 5000 for local development

2. **Production Deployment**
   - Gunicorn WSGI server with autoscale deployment target
   - Bind to 0.0.0.0:5000 with external port 80
   - Process management handled by Replit infrastructure

3. **Package Management**
   - UV lock file for dependency management
   - Nix package system for system-level dependencies
   - Automatic package installation via workflow tasks

## Changelog

```
Changelog:
- June 24, 2025. Initial setup
```

## User Preferences

```
Preferred communication style: Simple, everyday language.
```