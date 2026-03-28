# ServiceHub Backend API

A production-ready FastAPI backend for a service marketplace application. This project provides a clean, scalable structure for building marketplace services with **Supabase** as the backend.

## Features

✅ **FastAPI** - Modern, fast web framework  
✅ **Supabase** - PostgreSQL with REST API and real-time capabilities  
✅ **Supabase Client** - Type-safe database operations  
✅ **JWT Authentication** - Secure user authentication  
✅ **Role-based Access Control** - Provider and customer roles  
✅ **CRUD Operations** - Complete API for users, services, and bookings  
✅ **Pagination & Search** - Efficient data retrieval  
✅ **Input Validation** - Pydantic schemas  
✅ **CORS Support** - Cross-origin requests  
✅ **Error Handling** - Comprehensive exception handling  
✅ **API Documentation** - Auto-generated Swagger and ReDoc docs  

## Project Structure

```
app/
├── main.py                 # Application entry point
├── __init__.py            # Package initialization
├── api/
│   ├── __init__.py
│   ├── dependencies.py    # Shared dependencies (auth, db)
│   └── routes/
│       ├── __init__.py
│       ├── auth.py        # Authentication endpoints
│       ├── users.py       # User endpoints
│       ├── services.py    # Service marketplace endpoints
│       ├── bookings.py    # Booking endpoints
│       └── health.py      # Health check endpoint
├── models/
│   ├── __init__.py
│   ├── user.py           # User model
│   ├── service.py        # Service model
│   └── booking.py        # Booking model
├── schemas/
│   ├── __init__.py
│   ├── user.py           # User Pydantic schemas
│   ├── service.py        # Service schemas
│   └── booking.py        # Booking schemas
├── services/
│   ├── __init__.py
│   ├── user_service.py   # User business logic
│   ├── service_service.py # Service business logic
│   └── booking_service.py # Booking business logic
├── core/
│   ├── __init__.py
│   ├── config.py         # Configuration & settings
│   └── security.py       # JWT & password hashing
└── db/
    ├── __init__.py
    ├── base.py           # Base model with timestamps
    ├── session.py        # Database session & engine
    └── init_db.py        # Database initialization
```

## Getting Started

### Prerequisites

- Python 3.8+
- PostgreSQL database (or Supabase)
- Virtual environment (recommended)

### Installation

1. **Clone the repository**
   ```bash
   cd Backend_serviceHUb
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env .env.local
   # Edit .env.local with your Supabase credentials:
   # SUPABASE_URL=https://your-project.supabase.co
   # SUPABASE_KEY=your-anon-key
   # SECRET_KEY=your-jwt-secret
   ```

5. **Run development server**
   ```bash
   python -m uvicorn app.main:app --reload
   ```

   The API will be available at `http://localhost:8000`
   ```bash
   python -m uvicorn app.main:app --reload
   ```

   The API will be available at `http://localhost:8000`

### API Documentation

Once the server is running:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## Environment Configuration

Edit `.env` file to configure Supabase and application settings:

```env
# Supabase Configuration (Required)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-role-key

# Application Settings
APP_NAME=ServiceHub
DEBUG=True
ENV=development

# JWT Configuration
SECRET_KEY=your-super-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS Configuration
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8000"]
```

### Setting up Supabase

1. Create a Supabase account at https://supabase.com
2. Create a new project
3. In Project Settings → API, copy your:
   - **Project URL** → `SUPABASE_URL`
   - **Anon Public Key** → `SUPABASE_KEY`
4. Create tables using Supabase SQL Editor (see SQL scripts below)

### Database Tables SQL

Create these tables in your Supabase project:

```sql
-- Users table
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email TEXT UNIQUE NOT NULL,
  username TEXT UNIQUE NOT NULL,
  hashed_password TEXT NOT NULL,
  first_name TEXT,
  last_name TEXT,
  bio TEXT,
  profile_picture_url TEXT,
  is_active BOOLEAN DEFAULT TRUE,
  is_verified BOOLEAN DEFAULT FALSE,
  rating INTEGER,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Services table
CREATE TABLE services (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  provider_id UUID NOT NULL REFERENCES users(id),
  title TEXT NOT NULL,
  description TEXT NOT NULL,
  category TEXT NOT NULL,
  price_per_hour FLOAT NOT NULL,
  rating FLOAT,
  number_of_reviews INTEGER,
  is_available BOOLEAN DEFAULT TRUE,
  location TEXT,
  tags TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Bookings table
CREATE TABLE bookings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  service_id UUID NOT NULL REFERENCES services(id),
  customer_id UUID NOT NULL REFERENCES users(id),
  provider_id UUID NOT NULL REFERENCES users(id),
  status TEXT DEFAULT 'pending',
  scheduled_date TIMESTAMP NOT NULL,
  duration_hours INTEGER NOT NULL,
  total_price FLOAT NOT NULL,
  notes TEXT,
  rating FLOAT,
  review TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_services_provider_id ON services(provider_id);
CREATE INDEX idx_services_category ON services(category);
CREATE INDEX idx_bookings_customer_id ON bookings(customer_id);
CREATE INDEX idx_bookings_provider_id ON bookings(provider_id);
CREATE INDEX idx_bookings_status ON bookings(status);
```

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login user
- `POST /api/v1/auth/refresh` - Refresh access token

### Users
- `GET /api/v1/users/me` - Get current user profile
- `PUT /api/v1/users/me` - Update user profile
- `GET /api/v1/users/{user_id}` - Get user profile
- `GET /api/v1/users/` - List all users

### Services
- `POST /api/v1/services/` - Create service (provider)
- `GET /api/v1/services/` - List services with filters
- `GET /api/v1/services/{service_id}` - Get service details
- `PUT /api/v1/services/{service_id}` - Update service (provider)
- `DELETE /api/v1/services/{service_id}` - Delete service (provider)
- `GET /api/v1/services/provider/{provider_id}` - Get provider services

### Bookings
- `POST /api/v1/bookings/` - Create booking
- `GET /api/v1/bookings/` - List user bookings
- `GET /api/v1/bookings/{booking_id}` - Get booking details
- `PUT /api/v1/bookings/{booking_id}` - Update booking status (provider)
- `POST /api/v1/bookings/{booking_id}/review` - Add review (customer)
- `POST /api/v1/bookings/{booking_id}/cancel` - Cancel booking (customer)

## Database Schema

### Users Table
- `id` (UUID) - Primary key
- `email` (String) - Unique email
- `username` (String) - Unique username
- `hashed_password` (String) - Bcrypt hash
- `first_name`, `last_name` (String)
- `bio` (Text)
- `profile_picture_url` (String)
- `is_active` (Boolean)
- `is_verified` (Boolean)
- `rating` (Integer)
- `created_at`, `updated_at` (DateTime)

### Services Table
- `id` (UUID) - Primary key
- `provider_id` (UUID) - FK to users
- `title` (String) - Service title
- `description` (Text) - Service description
- `category` (String) - Service category
- `price_per_hour` (Float) - Hourly rate
- `rating` (Float) - Average rating
- `number_of_reviews` (Integer)
- `is_available` (Boolean)
- `location` (String)
- `tags` (Text) - JSON array
- `created_at`, `updated_at` (DateTime)

### Bookings Table
- `id` (UUID) - Primary key
- `service_id` (UUID) - FK to services
- `customer_id` (UUID) - FK to users
- `provider_id` (UUID) - FK to users
- `status` (String) - pending, confirmed, in_progress, completed, cancelled
- `scheduled_date` (DateTime)
- `duration_hours` (Integer)
- `total_price` (Float)
- `notes` (Text)
- `rating` (Float) - Customer rating
- `review` (Text) - Customer review
- `created_at`, `updated_at` (DateTime)

## Development

### Code Style
- Follow PEP 8
- Use type hints for all functions
- Use async/await for database operations
- Add docstrings to all functions

### Testing
```bash
pytest tests/ -v
```

### Format Code
```bash
black app/
```

### Lint Code
```bash
flake8 app/
```

## Deployment

### Production Environment
1. Set `DEBUG=False` in `.env`
2. Use strong `SECRET_KEY`
3. Configure proper `CORS_ORIGINS`
4. Use environment-specific database URLs
5. Enable HTTPS
6. Use production WSGI server (Gunicorn, etc.)

### Docker Deployment
Create `Dockerfile` and `docker-compose.yml` for containerized deployment.

### Example Gunicorn Command
```bash
gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## Security Best Practices

- ✅ JWT authentication with expiration
- ✅ Password hashing with bcrypt
- ✅ CORS configuration
- ✅ SQL injection prevention (SQLAlchemy ORM)
- ✅ Rate limiting (can be added)
- ✅ Input validation (Pydantic)
- ✅ Role-based access control

## License

MIT License

## Support

For issues and questions, please create an issue in the repository.

