# Provider Rules RAG

A mono-repo application for managing and searching provider rules using RAG (Retrieval-Augmented Generation) capabilities.

## Project Structure

```
provider-rules-rag/
├── docker-compose.yml       # Docker Compose configuration
├── README.md                # This file
├── backend/                 # FastAPI backend
│   ├── requirements.txt     # Python dependencies
│   ├── .env.example         # Environment variables template
│   ├── Dockerfile           # Backend Docker image
│   ├── app/
│   │   ├── __init__.py
│   │   └── main.py          # FastAPI application entry point
│   ├── db/
│   │   └── init.sql         # Database initialization script
│   └── ingest/
│       └── ingest.py        # Script for ingesting rules
└── frontend/                # React + Vite + Tailwind frontend
    ├── src/
    │   ├── components/
    │   │   └── RulesPanel.tsx
    │   ├── App.tsx
    │   ├── main.tsx
    │   └── index.css
    ├── package.json
    ├── vite.config.ts
    ├── tailwind.config.js
    └── Dockerfile           # Frontend Docker image
```

## Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)
- Node.js 20+ (for local development)

## Quick Start with Docker Compose

1. **Clone the repository** (if applicable)

2. **Start all services:**
   ```bash
   docker-compose up --build
   ```

   This will start:
   - PostgreSQL database on port 5432
   - FastAPI backend on port 8000
   - React frontend on port 5173

3. **Access the application:**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

4. **Stop all services:**
   ```bash
   docker-compose down
   ```

## Local Development Setup

### Backend Setup

1. **Navigate to the backend directory:**
   ```bash
   cd backend
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Start PostgreSQL** (using Docker Compose or local installation):
   ```bash
   docker-compose up postgres -d
   ```

6. **Run the backend:**
   ```bash
   uvicorn app.main:app --reload
   ```

   The API will be available at http://localhost:8000

### Frontend Setup

1. **Navigate to the frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Start the development server:**
   ```bash
   npm run dev
   ```

   The frontend will be available at http://localhost:5173

## Database Setup

The database is automatically initialized when using Docker Compose. The `init.sql` script creates:

- `rules` table for storing provider rules
- Indexes on `provider` and `category` columns
- Automatic `updated_at` timestamp trigger

To manually run the initialization script:
```bash
psql -U user -d provider_rules -f backend/db/init.sql
```

## Ingesting Rules

Use the ingest script to populate the database with provider rules:

```bash
cd backend
python -m ingest.ingest
```

Or modify `ingest/ingest.py` to ingest your own rules data.

## API Endpoints

- `GET /` - Root endpoint
- `GET /health` - Health check endpoint
- `GET /docs` - Interactive API documentation (Swagger UI)
- `GET /redoc` - Alternative API documentation (ReDoc)

## Technology Stack

### Backend
- **FastAPI** - Modern Python web framework
- **PostgreSQL** - Relational database
- **SQLAlchemy** - ORM (optional, for future database operations)
- **Uvicorn** - ASGI server

### Frontend
- **React** - UI library
- **TypeScript** - Type-safe JavaScript
- **Vite** - Build tool and dev server
- **Tailwind CSS** - Utility-first CSS framework

## Development

### Running Tests

Add your test files and run:
```bash
# Backend tests
pytest

# Frontend tests
npm test
```

### Building for Production

**Backend:**
```bash
docker build -t provider-rules-backend ./backend
```

**Frontend:**
```bash
cd frontend
npm run build
```

## Environment Variables

### Backend (.env)

- `DATABASE_URL` - PostgreSQL connection string
- `DEBUG` - Enable debug mode (True/False)
- `APP_NAME` - Application name
- `CORS_ORIGINS` - Comma-separated list of allowed origins

## Troubleshooting

1. **Port already in use:**
   - Change ports in `docker-compose.yml` or stop conflicting services

2. **Database connection errors:**
   - Ensure PostgreSQL container is running: `docker-compose ps`
   - Check `DATABASE_URL` in your `.env` file

3. **Frontend can't connect to backend:**
   - Verify backend is running on port 8000
   - Check CORS settings in `backend/app/main.py`
   - Ensure `VITE_API_URL` is set correctly in frontend environment

## License

[Add your license here]

## Contributing

[Add contributing guidelines here]

