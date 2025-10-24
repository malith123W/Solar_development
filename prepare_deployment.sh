#!/bin/bash

# Script to prepare repositories for separate Vercel deployment
# Run this script from the root of your Solar_development project

echo "🚀 Preparing Solar Development for separate Vercel deployment..."

# Create backend repository structure
echo "📁 Creating backend repository structure..."
mkdir -p ../solar-development-backend
cp -r backend/* ../solar-development-backend/
echo "✅ Backend files copied to ../solar-development-backend/"

# Create frontend repository structure
echo "📁 Creating frontend repository structure..."
mkdir -p ../solar-development-frontend
cp -r frontend/* ../solar-development-frontend/
echo "✅ Frontend files copied to ../solar-development-frontend/"

# Create README files for each repository
echo "📝 Creating README files..."

cat > ../solar-development-backend/README.md << 'EOF'
# Solar Development - Backend

This is the backend API for the Solar Development application.

## Features
- Data processing and analysis
- NMD analysis
- Power quality analysis
- Load balancing and forecasting
- PDF generation
- GridLAB-D integration

## Deployment
This backend is deployed on Vercel as a serverless function.

## API Endpoints
- `/api/health` - Health check
- `/api/upload` - File upload
- `/api/nmd_upload` - NMD file upload
- `/api/pq_upload_feeder_nmd` - Power quality feeder upload
- And many more...

## Environment Variables
- `PYTHONPATH`: Set to "."
- Add any other required environment variables in Vercel dashboard
EOF

cat > ../solar-development-frontend/README.md << 'EOF'
# Solar Development - Frontend

This is the React frontend for the Solar Development application.

## Features
- Interactive dashboard
- File upload and processing
- Data visualization with charts
- NMD analysis interface
- Power quality analysis
- Network graph visualization

## Deployment
This frontend is deployed on Vercel as a static site.

## Environment Variables
- `REACT_APP_API_URL`: Backend API URL (set to your backend Vercel URL)

## Development
```bash
npm install
npm start
```

## Build
```bash
npm run build
```
EOF

echo "✅ README files created"

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Initialize git repositories in both folders:"
echo "   cd ../solar-development-backend && git init && git add . && git commit -m 'Initial backend commit'"
echo "   cd ../solar-development-frontend && git init && git add . && git commit -m 'Initial frontend commit'"
echo ""
echo "2. Create repositories on GitHub/GitLab/Bitbucket"
echo ""
echo "3. Push code to repositories"
echo ""
echo "4. Follow the deployment instructions in DEPLOYMENT_INSTRUCTIONS.md"
echo ""
echo "📁 Backend files: ../solar-development-backend/"
echo "📁 Frontend files: ../solar-development-frontend/"
