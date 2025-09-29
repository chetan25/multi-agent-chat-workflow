# Docker Setup for Chat-BE

This guide explains how to run the chat-be service with PostgreSQL using Docker Compose.

## Prerequisites

1. **Docker and Docker Compose** installed on your system
2. **OpenAI API Key** for the chat functionality

## Quick Start

### 1. Set up Environment Variables

Create a `.env` file in the root directory:

```bash
# Copy the example file
cp env.example .env

# Edit the .env file and add your OpenAI API key
OPENAI_API_KEY=your-actual-openai-api-key-here
```

### 2. Start the Services

```bash
# Start all services
docker-compose up -d

# Or start with logs visible
docker-compose up
```

### 3. Verify Services are Running

```bash
# Check service status
docker-compose ps

# Check logs
docker-compose logs chat-be
docker-compose logs postgres
```

## Services Overview

| Service    | Port | Description         |
| ---------- | ---- | ------------------- |
| `postgres` | 5432 | PostgreSQL database |
| `chat-be`  | 8000 | Chat-BE API service |
| `frontend` | 5555 | Angular frontend    |

## Testing the Setup

### 1. Health Check

```bash
# Check if chat-be is responding
curl http://localhost:8000/docs

# Check if PostgreSQL is accessible
docker-compose exec postgres pg_isready -U postgres
```

### 2. Test API Endpoints

```bash
# Create a thread
curl -X POST "http://localhost:8000/api/threads" \
  -H "Content-Type: application/json" \
  -d '{"title": "Test Thread"}'

# Send a chat message (replace THREAD_ID with actual ID)
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "thread_id": "YOUR_THREAD_ID",
    "content": "Hello, how are you?",
    "message_type": "text"
  }'
```

## Configuration Details

### Environment Variables

- `OPENAI_API_KEY`: Required for AI functionality
- `POSTGRES_USER`: Database username (default: postgres)
- `POSTGRES_PASSWORD`: Database password (default: postgres)
- `POSTGRES_DB`: Database name (default: postgres)

### Volumes

- `postgres_data`: Persistent storage for PostgreSQL data
- `chat_uploads`: Persistent storage for uploaded files

### Health Checks

- **PostgreSQL**: Checks if database is ready to accept connections
- **Chat-BE**: Checks if the API documentation endpoint is accessible

## Troubleshooting

### Common Issues

1. **OpenAI API Key Missing**:

   ```
   Error: OpenAI API key not found
   ```

   - Ensure you've set `OPENAI_API_KEY` in your `.env` file
   - Verify the API key is valid and has sufficient credits

2. **Database Connection Failed**:

   ```
   Error: could not connect to server
   ```

   - Wait for PostgreSQL to fully start (check health status)
   - Verify database credentials in environment variables

3. **Port Conflicts**:

   ```
   Error: port is already in use
   ```

   - Check if ports 8000, 5432, or 5555 are already in use
   - Modify port mappings in docker-compose.yaml if needed

4. **Service Won't Start**:
   ```
   Error: service failed to start
   ```
   - Check logs: `docker-compose logs [service-name]`
   - Ensure all dependencies are properly installed

### Debug Commands

```bash
# View all logs
docker-compose logs

# View specific service logs
docker-compose logs chat-be
docker-compose logs postgres

# Restart a specific service
docker-compose restart chat-be

# Rebuild and restart
docker-compose up --build chat-be

# Access container shell
docker-compose exec chat-be bash
docker-compose exec postgres psql -U postgres
```

### Reset Everything

```bash
# Stop and remove all containers, networks, and volumes
docker-compose down -v

# Remove all images (optional)
docker-compose down --rmi all

# Start fresh
docker-compose up --build
```

## Development Mode

For development with auto-reload:

```bash
# The chat-be service is already configured with --reload
# Just start the services
docker-compose up

# Or run only chat-be for development
docker-compose up postgres chat-be
```

## Production Considerations

1. **Security**:

   - Change default database passwords
   - Use environment-specific API keys
   - Enable SSL/TLS for database connections

2. **Performance**:

   - Adjust PostgreSQL memory settings
   - Configure connection pooling
   - Set up proper logging levels

3. **Monitoring**:
   - Add monitoring services (Prometheus, Grafana)
   - Set up log aggregation
   - Configure alerting

## API Documentation

Once the services are running, you can access:

- **Chat-BE API Docs**: http://localhost:8000/docs
- **Frontend**: http://localhost:5555
- **Database**: localhost:5432 (postgres/postgres)

## File Structure

```
.
├── docker-compose.yaml      # Main Docker Compose configuration
├── env.example             # Environment variables template
├── .env                    # Your environment variables (create this)
├── chat-be/
│   ├── Dockerfile          # Chat-BE service Dockerfile
│   ├── app.py             # FastAPI application
│   ├── requirements.txt   # Python dependencies
│   └── ...
├── frontend/
│   ├── Dockerfile         # Frontend Dockerfile
│   └── ...
└── DOCKER_SETUP.md        # This file
```
