from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg_pool import AsyncConnectionPool
from sqlalchemy import text

# Import models and routes
from models import Base
from models.base import default_engine, target_engine, DEFAULT_DATABASE_URL


from routes import thread_router, chat_router, upload_router, legacy_router, async_router, user_router

from workflows.supervisor_workflow import create_supervisor_workflow


def initialize_database():
    with default_engine.connect() as connection:
        with connection.execution_options(isolation_level="AUTOCOMMIT"):
            result = connection.execute(
                text("SELECT 1 FROM pg_database WHERE datname = 'threads_db'")
            ).fetchone()
            if not result:
                connection.execute(text("CREATE DATABASE threads_db"))


def ensure_tables():
    Base.metadata.create_all(bind=target_engine)
    
    # Create uploads directory if it doesn't exist
    uploads_dir = Path("uploads")
    uploads_dir.mkdir(exist_ok=True)


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database()
    ensure_tables()
    conn_string = DEFAULT_DATABASE_URL.replace("postgresql+psycopg", "postgresql")

    async with AsyncConnectionPool(
        conninfo=conn_string,
        kwargs={"autocommit": True},
        max_size=20,
    ) as pool:
        checkpointer = AsyncPostgresSaver(pool)
        await checkpointer.setup()

        # Initialize supervisor workflow with checkpointer
        supervisor_workflow = create_supervisor_workflow()
        # Note: Workflow is already compiled in the SupervisorWorkflow class
        # We'll need to modify the workflow creation to support checkpointer if needed
        # Store workflow in app state for access in routes
        app.state.supervisor_workflow = supervisor_workflow

        yield


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(thread_router)
app.include_router(chat_router)
app.include_router(upload_router)
app.include_router(legacy_router)
app.include_router(async_router)
app.include_router(user_router)

# Mount static files for document serving
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


# All routes and schemas are now in separate files under the routes/ directory