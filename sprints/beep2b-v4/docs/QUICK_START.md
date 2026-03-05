# Quick Start Guide — Beep2B v4

This guide will get you up and running with the Beep2B website in under 5 minutes.

## Prerequisites

- **Docker Desktop** installed and running
- **4GB+ RAM** available
- **Ports 3000, 4321, and 27017** available

## 1. Start the Stack

From the project root directory:

```bash
cd sprints/beep2b-v4
docker compose up
```

Wait for all services to start. You'll see:
```
✓ Database ready
✓ CMS ready
✓ Frontend ready
```

## 2. Access the Services

Open these URLs in your browser:

- **Website**: http://localhost:4321
- **CMS Admin**: http://localhost:3000/admin

## 3. Log Into the CMS

Use the default credentials (created automatically on first startup):

- **Email**: `admin@beep2b.com`
- **Password**: `changeme`

⚠️ **Important**: Change this password immediately after first login!

## 4. Explore the Admin Panel

Navigate through the CMS collections:

- **Posts** — Blog articles (3 sample posts included)
- **Categories** — Blog categories (9 pre-seeded)
- **Testimonials** — Client testimonials (3 included)
- **Form Submissions** — Contact form data (empty initially)
- **Media** — Uploaded images and files

## 5. Test the Contact Form

1. Go to http://localhost:4321/contact
2. Fill out the contact form
3. Click "Send Message"
4. Check the **Form Submissions** collection in the CMS admin

## 6. View the Blog

1. Go to http://localhost:4321/blog
2. Browse the 3 sample blog posts
3. Click on a post to see the full article
4. Try filtering by category using the filter bar

## Common Tasks

### Stop the Services

```bash
# Stop services (Ctrl+C if running in foreground)
docker compose down
```

### Restart the Services

```bash
docker compose restart
```

### View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f frontend
docker compose logs -f cms
docker compose logs -f db
```

### Reset the Database

⚠️ **Warning**: This deletes all CMS data!

```bash
docker compose down -v
docker compose up
```

The database will be re-seeded with default content on startup.

### Create a New Blog Post

1. Go to http://localhost:3000/admin
2. Click **Posts** → **Create New**
3. Fill in:
   - Title (required)
   - Author (required)
   - Date (defaults to today)
   - Categories (select one or more)
   - Featured Image (optional — upload from Media)
   - Excerpt (brief summary)
   - Content (rich text editor)
4. Click **Save**
5. The post appears immediately at http://localhost:4321/blog

### Upload Images

1. Go to http://localhost:3000/admin
2. Click **Media** → **Upload**
3. Select image files (JPEG, PNG, WebP)
4. Payload automatically generates responsive sizes:
   - Thumbnail (400px)
   - Card (800px)
   - Feature (1920px)

### Fetch New Background Images

If you want to refresh the Pixabay background images:

```bash
cd frontend
npm run fetch-images
```

This downloads fresh images for:
- Business/office scenes
- Technology abstracts
- Professional networking
- Digital marketing

## Troubleshooting

### Port Already in Use

If you see "port is already allocated" errors:

```bash
# Check what's using the port
# On Windows:
netstat -ano | findstr :4321
netstat -ano | findstr :3000
netstat -ano | findstr :27017

# On macOS/Linux:
lsof -i :4321
lsof -i :3000
lsof -i :27017

# Stop the conflicting service or change ports in docker-compose.yml
```

### CMS Admin Panel Not Loading

1. Check CMS logs: `docker compose logs cms`
2. Verify MongoDB is healthy: `docker compose ps`
3. Restart the CMS service: `docker compose restart cms`

### Frontend Not Showing Blog Posts

1. Check if CMS is running: http://localhost:3000/api/posts
2. Check frontend logs: `docker compose logs frontend`
3. Verify CMS_URL environment variable is set to `http://cms:3000`

### Database Data Not Persisting

Check if the named volume exists:

```bash
docker volume ls | grep beep2b
```

You should see `beep2b-mongodata`. If not, the volume mount may have failed.

### Changes Not Reflecting

Both frontend and CMS support hot module reloading. If changes don't appear:

1. Check file was saved
2. Check terminal for compilation errors
3. Hard refresh browser (Ctrl+Shift+R or Cmd+Shift+R)
4. Restart the specific service: `docker compose restart frontend`

## Next Steps

- Read [README.md](../README.md) for comprehensive project documentation
- Review [ARCHITECTURE.md](ARCHITECTURE.md) to understand the system design
- Browse [docs/adr/](adr/) for architecture decision records
- Customize the design tokens in `frontend/src/styles/tokens.css`
- Add your own blog posts, testimonials, and images

## Production Deployment

For deploying to production, see the README.md section on "Building for Production". Key steps:

1. Build the frontend: `cd frontend && npm run build`
2. Use a managed MongoDB service (MongoDB Atlas)
3. Deploy CMS to Node.js hosting (Railway, Heroku, DigitalOcean)
4. Deploy frontend static files to CDN (Netlify, Vercel, Cloudflare Pages)
5. Set strong `PAYLOAD_SECRET` environment variable
6. Configure CORS for your production domain

## Getting Help

- **Documentation**: Check the `/docs` directory
- **Issues**: Review [KNOWN_ISSUES.md](../KNOWN_ISSUES.md)
- **Logs**: Always check service logs when troubleshooting
- **Reset**: When in doubt, `docker compose down -v && docker compose up`
