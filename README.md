# Finzup API

A secure FastAPI application for processing invoices using Google Gemini AI. The API extracts structured data from invoice images and PDFs.

## Features

- Secure RESTful API with JWT authentication
- Role-based access control
- Invoice processing using Google Gemini AI
- Support for PDF and image files
- Audit logging for all operations
- API key management
- Comprehensive test suite

## Prerequisites

- Python 3.12+
- uv for dependency management
- Supabase account and project
- Google Cloud account with Gemini API access

## Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/finzup-api.git
cd finzup-api
```

2. Install uv if you haven't already:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

3. Create and activate a virtual environment:
```bash
uv venv
source .venv/bin/activate  # On Unix/macOS
# or
.venv\Scripts\activate  # On Windows
```

4. Install dependencies:
```bash
uv pip install -e .
```

5. Create a `.env` file in the project root:
```env
# Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Supabase
SUPABASE_URL=your-supabase-url-here
SUPABASE_KEY=your-supabase-key-here

# Google Gemini
GOOGLE_API_KEY=your-google-api-key-here
GEMINI_MODEL=gemini-2.5-flash-preview-04-17

# File Upload
MAX_UPLOAD_SIZE=10485760  # 10MB in bytes
ALLOWED_EXTENSIONS=["pdf", "png", "jpg", "jpeg"]
```

6. Set up the Supabase database tables:

```sql
-- Users table
create table users (
    id uuid default uuid_generate_v4() primary key,
    email text unique not null,
    hashed_password text not null,
    full_name text,
    is_active boolean default true,
    is_superuser boolean default false,
    api_key text unique,
    api_key_created_at timestamp with time zone,
    api_key_last_used timestamp with time zone,
    created_at timestamp with time zone default timezone('utc'::text, now()),
    updated_at timestamp with time zone default timezone('utc'::text, now())
);

-- Audit logs table
create table audit_logs (
    id uuid default uuid_generate_v4() primary key,
    user_id uuid references users(id),
    api_key text,
    file_name text not null,
    file_size integer not null,
    num_pages integer not null,
    tokens_used integer not null,
    status text not null,
    created_at timestamp with time zone default timezone('utc'::text, now()),
    input_data jsonb,
    output_data jsonb,
    error_message text
);
```

## Running the Application

1. Start the development server:
```bash
uvicorn finzup_api.main:app --reload --host 0.0.0.0 --port 8000
```

2. Access the API documentation at `http://localhost:8000/docs`

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register a new user
- `POST /api/v1/auth/login` - Login and get access token
- `POST /api/v1/auth/generate-api-key` - Generate a new API key
- `POST /api/v1/auth/revoke-api-key` - Revoke the current API key

### Invoice Processing
- `POST /api/v1/process-invoice` - Process an invoice file (requires API key)
  - Accepts PDF, PNG, JPG, JPEG files
  - Maximum file size: 10MB
  - Returns structured invoice data

### Audit
- `GET /api/v1/audit-logs` - Get user's audit logs

## Authentication

The API supports two authentication methods:

1. **JWT Authentication**
   - Use the `/auth/login` endpoint to get access and refresh tokens
   - Include the access token in the `Authorization: Bearer <token>` header

2. **API Key Authentication**
   - Generate an API key using the `/auth/generate-api-key` endpoint
   - Include the API key in the `X-API-Key` header

## Security Features

- JWT authentication with refresh tokens
- Password hashing using bcrypt
- API key management with tracking
- Input validation
- File type and size restrictions
- Audit logging
- CORS middleware
- HTTPS/TLS support

## Development

### Running Tests
```bash
pytest
```

### Code Style
The project follows PEP 8 guidelines. Use a formatter like `black` for consistent code style.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.