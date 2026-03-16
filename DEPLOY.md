# Deploy to Heroku (backend + frontend, starts at sign-in)

The app is set up so that visiting your Heroku URL serves the **React app**, which starts at the **sign-in page** (`/` → redirects to `/login`).

## Option A: Build frontend on Heroku (recommended)

1. **Add the Node.js buildpack before the Python buildpack** (so the frontend is built during deploy):

   ```bash
   heroku buildpacks:add --index 1 heroku/nodejs
   heroku buildpacks:add --index 2 heroku/python
   ```

2. **Deploy** (e.g. push to GitHub if connected, or `git push heroku main`).

   Heroku will run `npm run build` from the repo root (which runs `cd frontend && npm install && npm run build`), then run the Python build and `collectstatic`. The same URL will serve both the API and the React app; `/` and `/login` show the sign-in page.

## Option B: Build frontend locally and commit

1. **Build the React app:**

   ```bash
   cd frontend
   npm install
   npm run build
   cd ..
   ```

2. **Allow the build folder to be committed** (remove from `.gitignore`):

   - Delete or comment out the line `frontend/build/` in the root `.gitignore`.

3. **Commit and push:**

   ```bash
   git add frontend/build
   git commit -m "Add frontend build for Heroku"
   git push origin main
   ```

4. **Redeploy** on Heroku (auto-deploys from GitHub, or push to `heroku` remote).

## After deploy

- Open `https://your-app-name.herokuapp.com/` → you should see the **login page**.
- API calls use the same origin, so no extra CORS or API URL config is needed when the frontend is served from the same Heroku app.
