# AI-Powered Student Grading Assistant

## Overview

This is a Flask-based web application that serves as an AI-powered grading assistant for educational institutions. The system allows students to upload assignments in various formats (PDF, DOCX, TXT) and enables teachers to generate automated feedback using Google's Gemini AI model. The application provides role-based access control with separate dashboards for students and teachers, comprehensive assignment management, and feedback tracking capabilities.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Architecture
- **Framework**: Flask web framework with Python
- **Database**: SQLite with SQLAlchemy ORM for data persistence
- **Authentication**: Flask-Login with session management and password hashing via Werkzeug
- **Security**: CSRF protection using Flask-WTF
- **File Processing**: Custom utilities for extracting text from PDF, DOCX, and TXT files

### Database Design
The application uses three main entities with clear relationships:
- **User Model**: Stores user information with role-based access (student/teacher)
- **Assignment Model**: Manages uploaded files with extracted text content
- **Feedback Model**: Tracks AI-generated and manual feedback with scoring

### AI Integration
- **Primary AI Provider**: Google Gemini API (gemini-2.5-flash model)
- **Fallback Mechanism**: Mock responses when API key is unavailable
- **AI Client Pattern**: Dedicated AIGradingClient class handles all AI interactions
- **Prompt Engineering**: Structured prompts for consistent feedback format with scores

### File Management
- **Upload Handling**: Secure file upload with size limits (16MB max)
- **Text Extraction**: Multi-format support with dedicated parsers for each file type
- **Storage Strategy**: Local file system storage with database metadata tracking

### Frontend Architecture
- **Template Engine**: Jinja2 with Bootstrap 5 for responsive design
- **Role-Based UI**: Separate dashboard views for students and teachers
- **Component Structure**: Modular templates with shared base layout

### Security Measures
- **Authentication**: Session-based login with password hashing
- **CSRF Protection**: Token-based protection for all forms
- **File Validation**: Extension and size validation for uploads
- **Input Sanitization**: Secure filename handling and text processing

## External Dependencies

### AI Services
- **Google Gemini API**: Primary AI model for generating assignment feedback
- **API Key Management**: Environment variable configuration (GEMINI_API_KEY)

### Python Libraries
- **Flask Ecosystem**: Flask, Flask-Login, Flask-SQLAlchemy, Flask-WTF
- **Document Processing**: pdfplumber (PDF), python-docx (DOCX)
- **Security**: Werkzeug for password hashing and file utilities
- **Environment**: python-dotenv for configuration management

### Frontend Dependencies
- **Bootstrap 5**: CSS framework for responsive design
- **Bootstrap Icons**: Icon library for UI elements

### Database
- **SQLite**: Embedded database for development and small-scale deployment
- **SQLAlchemy**: ORM for database operations and relationship management

### Development Tools
- **Environment Variables**: SESSION_SECRET, GEMINI_API_KEY
- **File System**: Local uploads directory for assignment storage