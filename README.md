# 🎓 AceTrack: AI-Powered Study Planner & Mock Test Generator

AceTrack is a full-stack web application designed to revolutionize how students prepare for competitive exams like JEE, NEET, and UGC NET. It provides a personalized preparation experience by leveraging the OpenAI API to generate dynamic mock tests and, in the future, intelligent study plans.

![DashboardImage](image.png)

## ✨ Key Features Implemented

The application has been architected as a clean monorepo with a fully functional core feature set.

**Secure User Authentication:** Complete user registration and login system using JWT for secure sessions.

**Personalized Onboarding:** A guided first-time setup to capture the user's target exam and tentative date, which personalizes the dashboard experience.

**AI-Powered Mock Test Generator:** The central feature of the application.
- **Multi-Format Questions:** Users can select from over 10 different question formats (MCQ, Match the Following, Statement-Based, etc.).
- **Customizable Length:** Specify the exact number of questions needed for each type.
- **Syllabus-Aware:** The backend uses a syllabus file to ensure generated questions are relevant to the user's chosen exam.
- **Dynamic File Export:** Generated mock tests are delivered as a clean, downloadable .pdf file.

**Modern & Dynamic UI:**
- A tabbed interface to seamlessly switch between the Mock Test Generator and the Study Plan Calendar.
- A dynamic header that displays the user's exam name and a live countdown of the days remaining.
- Sidebar widgets for visualizing a Study Streak and the exam countdown.

## 🛠️ Technology Stack

The project uses a modern, scalable tech stack with a clear separation of concerns between the frontend and backend.

| Area | Technology |
|------|------------|
| Frontend | React.js, Vite, TypeScript, Tailwind CSS |
| Backend | FastAPI, Python, Docker |
| Database | PostgreSQL (managed by Aiven) with SQLAlchemy ORM |
| AI | OpenAI API (gpt-4-turbo) |

## 📂 Project Structure

The project is organized as a monorepo with two distinct, self-contained directories.

```
/
├── backend/                    # All FastAPI and Python code
│   ├── data/                   # Holds static data like the exam syllabus
│   │   └── Syllabus.xlsx  
│   ├── services/               # Core business logic for AI features
│   │   ├── Generation.py       # Logic for generating test papers
│   │   └── PromptsDict.py      # Manages prompts for the OpenAI API
│   ├── auth.py                 # Handles JWT authentication and user sessions
│   ├── crud.py                 # Functions for database create, read, update, delete
│   ├── database.py             # SQLAlchemy session and database connection setup
│   ├── main.py                 # FastAPI application entry point and API routes
│   ├── models.py               # SQLAlchemy database models (tables)
│   ├── schemas.py              # Pydantic models for data validation and serialization
│   ├── Dockerfile              # Instructions to containerize the backend
│   └── requirements.txt        # Python dependencies
│  
└── frontend/                   # All React and TypeScript code
    ├── src/  
    │   ├── components/         # Reusable React components
    │   │   ├── Dashboard.tsx   # Main dashboard view after login
    │   │   ├── LoginPage.tsx   # User login component
    │   │   └── SignupPage.tsx  # User registration component
    │   ├── App.tsx             # Main application component with routing
    │   └── main.tsx            # Application entry point
    ├── index.html              # Main HTML file for the React app
    ├── tailwind.config.js      # Configuration for Tailwind CSS
    ├── package.json            # Project metadata and npm dependencies
    └── vite.config.ts          # Configuration for the Vite build tool
```

## 🏁 Local Development Setup

Follow these instructions to get the project running on your local machine.

### Prerequisites

- Node.js (v18 or later)
- Python (v3.11 or later) & pip
- Git
- A running PostgreSQL instance

### 1. Clone the Repository

```bash
git clone https://github.com/Adit1414/AceTrack.git
cd AceTrack
```

### 2. Backend Setup

```bash
# Navigate to the backend directory
cd backend

# Create and activate a Python virtual environment
python -m venv venv

# On Windows:
# venv\Scripts\activate
# On macOS/Linux:
# source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create your local environment file
# (You can copy from .env.example if one exists)
touch .env
```

Now, open the `backend/.env` file and add your secret keys:

```env
# backend/.env
DATABASE_URL="postgresql://user:password@host:port/dbname?sslmode=require"
SECRET_KEY="a_very_strong_and_secret_key"
OPENAI_API_KEY="sk-your_openai_api_key_here"
```

### 3. Frontend Setup

```bash
# Navigate to the frontend directory
cd frontend

# Install dependencies
npm install

# Create your local environment file
# (You can copy from .env.example if one exists)
touch .env.local
```

The `frontend/.env.local` file should contain the URL for your local backend server:

```env
# frontend/.env.local
VITE_API_BASE_URL="http://localhost:8000"
```

### 4. Run the Application

You'll need two separate terminals to run both servers simultaneously.

**Terminal 1: Run the Backend**

```bash
cd backend
# Make sure your virtual environment is active
uvicorn main:app --reload
```

**Terminal 2: Run the Frontend**

```bash
cd frontend
npm run dev
```

Your application should now be running, with the frontend available at `http://localhost:5173`.

## 🚀 Future Roadmap

This project has a solid foundation, with an exciting roadmap of features to be implemented next.

- **Full Cloud Deployment:** Host the backend on Render and the frontend on Vercel for public access.

- **Dynamic Study Planner:**
  - Design and implement the core study planner feature.
  - Develop advanced prompt engineering strategies to generate adaptive daily schedules based on user progress, topic weightage, and available study hours.

- **Enhanced Test Generation:**
  - **Chapter-Wise Tests:** Integrate logic to allow users to generate tests for specific chapters, not just the full syllabus.
  - **Advanced Controls:** Add settings to control the cognitive type of generated questions (e.g., factual, analytical, application-based).
  - **Topics based on Weightage:** Choose topics from syllabus based off of their average weightage in the exam.

- **Interactive Test Platform:** Develop an in-app interface for users to take the generated mock tests directly on the website. This will include a live timer to simulate real exam conditions and an automated scoring system to provide instant results upon completion.

- **Deeper Personalization Engine:**
  - Fully utilize all onboarding data (study hours, weak subjects) to customize the study plan and test generation.
  - Replace hardcoded data with dynamic, user-specific information.

- **Resource Hub:** Build a repository to host Past-Year Question Papers (PYQs), weightage distribution of the syllabus, and other essential study materials.

- **Monetization:** Introduce a paywall to offer premium features, such as unlimited test generations, advanced performance analytics, or access to exclusive content.