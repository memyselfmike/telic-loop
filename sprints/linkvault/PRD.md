# PRD: LinkVault

## 1. Overview
A personal bookmark manager: Node.js server + JSON file storage + two-page UI
(collection + dashboard).

## 2. Technical Stack
- Node.js with Express
- JSON file storage (data/links.json)
- Vanilla HTML/CSS/JS frontend
- Port 3000

## 3. Data Model

### 3.1 Link
```json
{
  "id": "uuid",
  "title": "string",
  "url": "string",
  "tags": ["string"],
  "timestamp": "ISO8601"
}
```

## 4. API Endpoints

### 4.1 Links API
- `GET /api/links` — list all links (returns `{links: [...]}`)
- `POST /api/links` — create link (body: `{title, url, tags}`, returns 201)
- `DELETE /api/links/:id` — delete link (returns 204)

### 4.2 Stats API
- `GET /api/stats` — returns `{totalLinks, totalTags, mostUsedTag, tagCounts: [{tag, count}], recentLinks: [...]}`

## 5. Frontend

### 5.1 Collection Page (/)
- Form: title input, URL input, tags input (comma-separated), Add button
- Responsive card grid (3 cols desktop, 1 col mobile)
- Each card: title (bold), URL (truncated), colored tag pills, delete button
- Tag pills above grid for filtering (click to filter, click again to clear)

### 5.2 Dashboard Page (/dashboard)
- Three stats cards: Total Links, Total Tags, Most Used Tag
- Horizontal bar chart showing tag distribution
- Recent links list (5 most recent)
- Navigation link back to collection

### 5.3 Navigation
- Nav bar on both pages with links to / and /dashboard

## 6. File Structure
```
server.js
storage.js
package.json
data/links.json
public/index.html
public/dashboard.html
public/styles.css
public/app.js
public/dashboard.js
```
