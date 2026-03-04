# ADR-0006: Nginx Frontend with API Reverse Proxy

## Status
Accepted

## Context

The frontend needs to:
- Serve static HTML/CSS/JS files efficiently
- Make API requests to the backend without CORS issues
- Support SPA routing (all paths serve `index.html`)
- Cache static assets for performance
- Run in a Docker container alongside other services

Options considered:

1. **Nginx with reverse proxy** - Production-grade, handles static files and proxying
2. **Frontend calls API directly** - Simple, but requires CORS configuration
3. **Express serves both API and frontend** - Single server, but less efficient for static files
4. **Caddy** - Modern alternative to Nginx with automatic HTTPS

## Decision

We will use Nginx Alpine to serve the frontend with a reverse proxy configuration for API requests.

Configuration:
- Serve static files from `/usr/share/nginx/html`
- Proxy `/api/*` requests to `http://api:3000/api/`
- SPA fallback: all routes serve `index.html`
- Cache static assets (CSS, JS, images) for 1 year
- Listen on port 8080

## Consequences

### What Becomes Easier

- **No CORS issues**: API and frontend appear to be on the same origin
- **Single port for users**: Everything accessible at `http://localhost:8080`
- **Production-ready pattern**: Same config works in production with HTTPS
- **Efficient static serving**: Nginx is optimized for static files
- **Asset caching**: Automatic cache control headers for performance
- **SPA routing**: Nginx handles fallback to `index.html` for client-side routes
- **Load balancing**: Nginx can proxy to multiple API servers if needed

### What Becomes More Difficult

- **Configuration complexity**: Requires understanding Nginx config syntax
- **Debugging**: Proxy errors require checking both Nginx and API logs
- **Local development**: Can't run frontend standalone (tied to Docker setup)

### Configuration Details

```nginx
# Reverse proxy for API (eliminates CORS)
location /api/ {
    proxy_pass http://api:3000/api/;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
}

# SPA fallback
location / {
    try_files $uri $uri/ /index.html;
}

# Cache static assets
location ~* \.(css|js|jpg|jpeg|png|gif|ico|svg|woff|woff2|ttf|eot)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

### Alternatives Considered

**Direct API calls with CORS**: Would require:
- CORS headers in API server
- OPTIONS preflight requests
- More complex security configuration
- Users accessing frontend and API on different ports

**Express serves everything**: Would work but:
- Express is slower than Nginx for static files
- Mixes concerns (API logic + static serving)
- Less efficient use of resources
- Nginx is better tested for production static serving

**Caddy**: Simpler config, automatic HTTPS, but:
- Less familiar to most teams
- Smaller ecosystem
- Nginx is industry standard
- Automatic HTTPS not needed for local development

### Benefits

**Unified Origin**: Frontend makes requests to `/api/books`, which Nginx proxies to `http://api:3000/api/books`. Browser sees same origin, no CORS.

**SPA Support**: Routes like `/stats` or `/book/123` all serve `index.html`, allowing JavaScript to handle routing.

**Performance**: Static files are served directly from disk by Nginx without application logic overhead.

**Production Pattern**: Same Nginx config can be used in production, just:
- Add TLS/HTTPS termination
- Adjust API backend URLs
- Add compression (gzip)
- Add security headers

### Mitigations

- Keep Nginx config simple and well-commented
- Use Docker health checks to ensure Nginx is running
- Document the proxy pattern in architecture docs
- Provide clear logging for debugging proxy issues
