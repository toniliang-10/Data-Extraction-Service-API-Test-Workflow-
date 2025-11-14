#!/bin/bash
# Setup script for Django Data Extraction Service

echo "🚀 Setting up Django Data Extraction Service..."
echo

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing production dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "📥 Installing test dependencies..."
pip install -r requirements-test.txt

# Run migrations
echo "🗄️  Running database migrations..."
python manage.py migrate

# Create superuser (optional)
echo
echo "👤 Create Django superuser? (y/n)"
read -r create_superuser
if [ "$create_superuser" = "y" ]; then
    python manage.py createsuperuser
fi

echo
echo "✅ Setup complete!"
echo
echo "📚 Next steps:"
echo "  1. Activate virtual environment: source venv/bin/activate"
echo "  2. Run server: python manage.py runserver"
echo "  3. Visit: http://127.0.0.1:8000/"
echo "  4. API Docs: http://127.0.0.1:8000/api/docs/"
echo "  5. Admin: http://127.0.0.1:8000/admin/"
echo "  6. Run tests: pytest"
echo

