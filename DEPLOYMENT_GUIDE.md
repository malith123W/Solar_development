# Solar Development - Separate Vercel Deployments Guide

This guide will help you deploy your Solar Development application with separate backend and frontend deployments on Vercel.

## Prerequisites

1. **Vercel Account**: Sign up at [vercel.com](https://vercel.com)
2. **GitHub Repository**: Your code should be in a GitHub repository
3. **Node.js**: For local development (version 14 or higher)
4. **Python**: For backend development (version 3.8 or higher)

## Deployment Steps

### Step 1: Deploy Backend (API)

1. **Go to Vercel Dashboard**
   - Visit [vercel.com/dashboard](https://vercel.com/dashboard)
   - Click "New Project"

2. **Import Backend Repository**
   - Select your GitHub repository
   - Choose "Import" for the repository

3. **Configure Backend Project**
   - **Project Name**: `solar-development-backend` (or your preferred name)
   - **Root Directory**: Set to `backend`
   - **Framework Preset**: Select "Other" or "Python"
   - **Build Command**: Leave empty (Vercel will auto-detect)
   - **Output Directory**: Leave empty
   - **Install Command**: Leave empty

4. **Environment Variables** (if needed)
   - Add any required environment variables in the Vercel dashboard
   - Common variables might include:
     - `PYTHONPATH`: `.`
     - Any API keys or database URLs

5. **Deploy Backend**
   - Click "Deploy"
   - Wait for deployment to complete
   - **Note the deployment URL** (e.g., `https://solar-development-backend.vercel.app`)

### Step 2: Deploy Frontend

1. **Create New Project in Vercel**
   - Click "New Project" again
   - Select the same GitHub repository

2. **Configure Frontend Project**
   - **Project Name**: `solar-development-frontend` (or your preferred name)
   - **Root Directory**: Set to `frontend`
   - **Framework Preset**: Select "Create React App"
   - **Build Command**: `npm run build`
   - **Output Directory**: `build`
   - **Install Command**: `npm install`

3. **Environment Variables**
   - **REACT_APP_API_URL**: Set this to your backend URL from Step 1
     - Example: `https://solar-development-backend.vercel.app/api`
   - **NODE_ENV**: `production`

4. **Deploy Frontend**
   - Click "Deploy"
   - Wait for deployment to complete
   - **Note the frontend URL** (e.g., `https://solar-development-frontend.vercel.app`)

### Step 3: Configure CORS (if needed)

If you encounter CORS issues, you may need to update your backend to allow requests from your frontend domain:

1. **Update Backend CORS Configuration**
   - In your backend code, ensure CORS is configured to allow your frontend domain
   - The current configuration should work, but you can be more specific if needed

### Step 4: Test Integration

1. **Access Frontend URL**
   - Open your frontend URL in a browser
   - Test the application functionality

2. **Check Network Tab**
   - Open browser developer tools
   - Check if API calls are going to the correct backend URL
   - Verify there are no CORS errors

## Configuration Files Created/Modified

### Backend (`backend/vercel.json`)
```json
{
  "version": 2,
  "name": "solar-development-backend",
  "builds": [
    {
      "src": "api/index.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/api/(.*)",
      "dest": "api/index.py"
    },
    {
      "src": "/(.*)",
      "dest": "api/index.py"
    }
  ],
  "env": {
    "PYTHONPATH": "."
  },
  "functions": {
    "api/index.py": {
      "maxDuration": 30
    }
  }
}
```

### Frontend (`frontend/vercel.json`)
```json
{
  "version": 2,
  "name": "solar-development-frontend",
  "builds": [
    {
      "src": "package.json",
      "use": "@vercel/static-build",
      "config": {
        "distDir": "build"
      }
    }
  ],
  "routes": [
    {
      "src": "/static/(.*)",
      "dest": "/static/$1"
    },
    {
      "src": "/(.*)",
      "dest": "/index.html"
    }
  ],
  "env": {
    "REACT_APP_API_URL": "@react_app_api_url"
  }
}
```

## Troubleshooting

### Common Issues

1. **CORS Errors**
   - Ensure your backend allows requests from your frontend domain
   - Check that the API URL is correctly set in environment variables

2. **Build Failures**
   - Check the build logs in Vercel dashboard
   - Ensure all dependencies are in `requirements.txt` (backend) and `package.json` (frontend)

3. **API Not Found**
   - Verify the backend URL is correct
   - Check that routes are properly configured in `vercel.json`

4. **Environment Variables**
   - Make sure `REACT_APP_API_URL` is set correctly in the frontend project
   - Environment variables must be prefixed with `REACT_APP_` to be available in React

### Local Development

For local development, you can still run both services separately:

1. **Backend**: `cd backend && python app.py`
2. **Frontend**: `cd frontend && npm start`

The frontend will automatically use `http://localhost:5000/api` for API calls in development mode.

## Custom Domains (Optional)

You can set up custom domains for both deployments:

1. **Backend Custom Domain**
   - Go to backend project settings
   - Add your custom domain (e.g., `api.yourdomain.com`)

2. **Frontend Custom Domain**
   - Go to frontend project settings
   - Add your custom domain (e.g., `app.yourdomain.com`)

3. **Update Environment Variables**
   - Update `REACT_APP_API_URL` to use your custom backend domain

## Benefits of Separate Deployments

1. **Independent Scaling**: Backend and frontend can scale independently
2. **Faster Deployments**: Changes to one service don't require redeploying the other
3. **Better Performance**: CDN optimization for frontend, serverless functions for backend
4. **Easier Debugging**: Separate logs and monitoring for each service
5. **Cost Optimization**: Pay only for what you use for each service

## Next Steps

1. Deploy both services following the steps above
2. Test the integration thoroughly
3. Set up monitoring and logging
4. Consider setting up custom domains
5. Configure CI/CD pipelines for automatic deployments

Your Solar Development application should now be running with separate, optimized deployments on Vercel!
