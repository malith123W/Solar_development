# Vercel Deployment Instructions

## Overview
This guide will help you deploy your Solar Development application with separate backend and frontend deployments on Vercel.

## Prerequisites
1. Vercel account (sign up at https://vercel.com)
2. Git repository (GitHub, GitLab, or Bitbucket)
3. Your code pushed to the repository

## Step 1: Deploy Backend

### 1.1 Create Backend Repository
1. Create a new repository for your backend
2. Copy only the `backend/` folder contents to the new repository
3. Push the code to your repository

### 1.2 Deploy Backend to Vercel
1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Click "New Project"
3. Import your backend repository
4. Configure the project:
   - **Framework Preset**: Other
   - **Root Directory**: `./` (root of backend repo)
   - **Build Command**: Leave empty (Vercel will auto-detect)
   - **Output Directory**: Leave empty
5. Click "Deploy"
6. Wait for deployment to complete
7. **Important**: Copy the deployment URL (e.g., `https://your-backend-app.vercel.app`)

## Step 2: Deploy Frontend

### 2.1 Create Frontend Repository
1. Create a new repository for your frontend
2. Copy only the `frontend/` folder contents to the new repository
3. Push the code to your repository

### 2.2 Deploy Frontend to Vercel
1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Click "New Project"
3. Import your frontend repository
4. Configure the project:
   - **Framework Preset**: Create React App
   - **Root Directory**: `./` (root of frontend repo)
   - **Build Command**: `npm run build`
   - **Output Directory**: `build`
5. **Environment Variables**:
   - Add `REACT_APP_API_URL` = `https://your-backend-app.vercel.app/api`
   - Replace `your-backend-app` with your actual backend URL
6. Click "Deploy"
7. Wait for deployment to complete

## Step 3: Configure CORS (Backend)

### 3.1 Update Backend CORS Settings
After deploying your backend, you need to update the CORS settings to allow your frontend domain.

1. Go to your backend repository
2. Edit `app.py` and update the CORS configuration:

```python
from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins=[
    "http://localhost:3000",  # For local development
    "https://your-frontend-app.vercel.app"  # Replace with your frontend URL
])
```

3. Commit and push the changes
4. Vercel will automatically redeploy

## Step 4: Test Your Deployment

### 4.1 Test Backend
1. Visit your backend URL: `https://your-backend-app.vercel.app/api/health`
2. You should see a health check response

### 4.2 Test Frontend
1. Visit your frontend URL: `https://your-frontend-app.vercel.app`
2. Try uploading a file or using any feature
3. Check browser console for any CORS errors

## Step 5: Environment Variables

### 5.1 Backend Environment Variables
In your backend Vercel project settings, you can add:
- `PYTHONPATH`: `.`
- Any other environment variables your app needs

### 5.2 Frontend Environment Variables
In your frontend Vercel project settings:
- `REACT_APP_API_URL`: `https://your-backend-app.vercel.app/api`

## Troubleshooting

### Common Issues:

1. **CORS Errors**:
   - Make sure your backend CORS settings include your frontend domain
   - Check that the frontend is calling the correct backend URL

2. **Build Failures**:
   - Check that all dependencies are in `requirements.txt` (backend) and `package.json` (frontend)
   - Ensure Python version compatibility

3. **API Not Found**:
   - Verify the backend URL in frontend environment variables
   - Check that backend routes are properly configured

4. **File Upload Issues**:
   - Vercel has file size limits (50MB for serverless functions)
   - Consider using Vercel Blob or external storage for large files

## File Structure After Deployment

```
Backend Repository:
├── app.py
├── vercel.json
├── requirements.txt
├── data_processing.py
├── gridlabd_integration.py
├── load_balancing.py
├── load_forecasting.py
├── nmd_analysis.py
├── pdf_generation.py
├── power_quality.py
├── voltage_variation.py
├── utils.py
├── visualization.py
└── gridlabd_models/
    └── permanent_test.glm

Frontend Repository:
├── package.json
├── vercel.json
├── public/
├── src/
│   ├── components/
│   ├── services/
│   ├── utils/
│   ├── config.js
│   └── ...
└── README.md
```

## Next Steps

1. Set up custom domains (optional)
2. Configure monitoring and analytics
3. Set up CI/CD for automatic deployments
4. Consider using Vercel's database solutions if needed

## Support

If you encounter issues:
1. Check Vercel deployment logs
2. Verify environment variables
3. Test API endpoints directly
4. Check browser console for errors
