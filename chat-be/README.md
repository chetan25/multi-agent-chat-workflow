# Backend Setup Guide

This guide explains how to set up the backend environment using `uv` (a fast Python package installer and resolver).

## Prerequisites

- Python 3.8 or higher
- `uv` package manager installed

### Installing uv

If you don't have `uv` installed, you can install it using one of the following methods:

**Using pip:**

```bash
pip install uv
```

**Using curl (Linux/macOS):**

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Using PowerShell (Windows):**

```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

## Setup Instructions

### 1. Navigate to the Backend Directory

```bash
cd backend
```

### 2. Create a Virtual Environment with uv

```bash
uv venv
```

This creates a virtual environment in the `.venv` directory.

### 3. Activate the Virtual Environment

**On Windows:**

```bash
.venv\Scripts\activate
```

**On Linux/macOS:**

```bash
source .venv/bin/activate
```

### 4. Install Dependencies

```bash
uv pip install -r requirements.txt
```

Alternatively, you can use uv's sync command which automatically creates and manages the virtual environment:

```bash
uv sync
```

## Project Dependencies

The following packages are installed from `requirements.txt`:

- **fastapi** - Modern, fast web framework for building APIs
- **uvicorn** - ASGI server for running FastAPI applications
- **sqlalchemy** - SQL toolkit and Object-Relational Mapping (ORM) library
- **sqlalchemy-utils** - Utility functions for SQLAlchemy
- **langgraph** - Framework for building stateful, multi-actor applications with LLMs
- **langchain** - Framework for developing applications powered by language models
- **langgraph-checkpoint-postgres** - PostgreSQL checkpointing for LangGraph
- **langchain-openai** - OpenAI integration for LangChain
- **python-dotenv** - Load environment variables from .env files

## Running the Application

### 1. Set Up Environment Variables

Create a `.env` file in the backend directory with your configuration:

```bash
# Example .env file
OPENAI_API_KEY=your_openai_api_key_here
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/threads_db
```

### 2. Start the Development Server

```bash
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

### 3. View API Documentation

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## Docker Setup (Alternative)

If you prefer using Docker, you can use the provided Dockerfile:

```bash
# Build the Docker image
docker build -t backend-app .

# Run the container
docker run -p 8000:8000 backend-app
```

Or use docker-compose from the project root:

```bash
docker-compose up
```

## API Endpoints

The backend provides the following endpoints:

- `POST /start_thread` - Create a new conversation thread
- `POST /ask_question/{thread_id}` - Ask a question in a thread
- `PATCH /edit_state/{thread_id}` - Edit the state of a thread
- `POST /confirm/{thread_id}` - Confirm a thread
- `DELETE /delete_thread/{thread_id}` - Delete a thread
- `GET /sessions` - List all sessions

## Database Setup

The application uses PostgreSQL and will automatically:

- Create the `threads_db` database if it doesn't exist
- Create the necessary tables on startup

Make sure PostgreSQL is running and accessible at the configured connection string.

## Development Tips

- Use `uv pip list` to see installed packages
- Use `uv pip freeze > requirements.txt` to update requirements.txt
- The virtual environment is automatically activated when using `uv run` commands
- For faster dependency resolution, uv caches packages globally

## Troubleshooting

### Common Issues

1. **Permission errors on Windows**: Run your terminal as Administrator
2. **Database connection issues**: Ensure PostgreSQL is running and the connection string is correct
3. **Missing dependencies**: Run `uv pip install -r requirements.txt` again

### Getting Help

- Check the [uv documentation](https://docs.astral.sh/uv/)
- Review the FastAPI documentation for API-related issues
- Check the application logs for detailed error messages
