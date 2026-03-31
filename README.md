PackItUpOnly Team Project: 

Team members
The members of the team are:
Amey Tripathi
Hafsa Bhudye
Pasquale Benjamin Fuccio
Jasmeen Sethi
Tejas Raj
Khushi Alam
Ved Patel
Nitin Anantharaju

Project structure
The project is called KCL Ticketing System. 
It is a full-stack web application featuring a Django backend and a React.js frontend designed for student ticket submissions, staff management and an AI-powered chatbot.

Deployed version of the application
The deployed version of the application can be found at:

Installation instructions
To set up the ticketing system, the following commands should be followed:
nix run .#init
nix run .#tests
nix run .#run
nix run .#seed 
nix run .#unseed

These commands allow the system to run using the Nix environment. If the Nix setup fails, use the manual setup instructions below.
First-Time Setup
This script checks for prerequisites (Python 3.8+ and Node.js 14+), installs all dependencies for both backend and frontend, and runs database migrations.

For Mac/Linux:

Bash
chmod +x setup-all.sh start-all.sh
./setup-all.sh
For Windows:

Bash
.\setup-all.bat

Launch the Application
Once the setup is complete, use the startup script to launch both the Django development server and the React frontend simultaneously.

For Mac/Linux:

Bash
./start-all.sh
For Windows:

Bash
.\start-all.bat
Backend URL: http://localhost:8000

Frontend URL: http://localhost:3000

Manual Setup (Optional)
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

Troubleshooting
Port Conflicts: If port 8000 (Backend) or 3000 (Frontend) is occupied, the systems will prompt you to use an alternative or stop the conflicting service.

AI Chatbot Issues: Ensure your GEMINI_API_KEY is set in your local environment or .env file. The rest of the app runs without this key.

Dependencies: If setup fails, ensure you are using Node.js 18.x as specified in the project configuration.

Sources
The packages used by this application are specified in requirements.txt

Login Details for Ticketing System:

Student: 
Username: johndoe
Password: Password123

Staff:
Username: janedee
Password: Password123

Admin:
Username: alexadmin
Password: Password123

AI Usage Disclosure
Generative AI tools were used in the development of the following file:

Path to file: PackItUpOnly/flake.nix (in the root)
Affected function/ method/ class: flake.nix 
number of lines of code generated : 165/167
Percentage use : 98%

IMPORTANT DISCLOSURE:
If the AI chatbot does not work when using the Nix interface, please check its functionality in the deployed version. This may occur because the Gemini API key cannot be shared in the repository due to security restrictions and Google may have blocked that key. The Deployed version has it's own key.
