KCL Ticketing System
A full-stack web application featuring a Django backend and a React.js frontend designed for student ticket submissions, staff management, and an AI-powered chatbot.

🚀 Quick Start
To get the project running quickly, use the automated scripts provided in the root directory.

1. First-Time Setup
This script checks for prerequisites (Python 3.8+ and Node.js 14+), installs all dependencies for both backend and frontend, and runs database migrations.

For Mac/Linux:

Bash
chmod +x setup-all.sh start-all.sh
./setup-all.sh
For Windows:

Bash
.\setup-all.bat
2. Launch the Application
Once the setup is complete, use the startup script to launch both the Django development server and the React frontend simultaneously.

For Mac/Linux:

Bash
./start-all.sh
For Windows:

Bash
.\start-all.bat
Backend URL: http://localhost:8000

Frontend URL: http://localhost:3000

🛠 Features
Student Ticket Submission
Automated Validation: K-Numbers are validated (numbers only) and automatically generate a King's College London email address (KNumber@kcl.ac.uk).

Dynamic Forms: "Type of Issue" options change dynamically based on the selected Department (Informatics, Engineering, or Medicine).

Input Protection: Names and Surnames are restricted from containing numbers.

Management & AI
Admin Panel: Staff can manage and view all submitted tickets at http://localhost:8000/admin/.

AI Chatbot: Integrates Google Gemini for intelligent assistance. Requires a GEMINI_API_KEY environment variable only if you use chatbot features.

🔧 Manual Setup (Optional)
If you prefer to set up the components individually, follow these steps:

Backend (Django)
Install dependencies: pip install -r requirements.txt.

Migrations: python manage.py migrate.

Superuser: python manage.py createsuperuser (for admin access).

Run: python manage.py runserver.

Frontend (React)
Navigate: cd frontend.

Install: npm install.

Run: npm start.

⚠️ Troubleshooting
Port Conflicts: If port 8000 (Backend) or 3000 (Frontend) is occupied, the systems will prompt you to use an alternative or stop the conflicting service.

AI Chatbot Issues: Ensure your GEMINI_API_KEY is set in your local environment or .env file. The rest of the app runs without this key.

Dependencies: If setup fails, ensure you are using Node.js 18.x as specified in the project configuration.
