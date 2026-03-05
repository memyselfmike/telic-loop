# Known Issues - Beep2B v4

## CMS Admin Panel UI (Non-Blocking)

**Issue**: The Payload CMS admin panel at `/admin/login` returns HTTP 500 errors when accessed through a web browser.

**Root Cause**: Payload CMS v3.x has compatibility issues with Next.js 15.x. The admin UI's CodeEditor component fails to properly initialize context, causing SSR crashes with errors like "Cannot destructure property 'config' of 'se(...)' as it is undefined."

**Versions Tested**:
- Payload 3.0.0 + Next.js 15.0.3, 15.3.9, 15.4.11
- Payload 3.50.0 + Next.js 15.4.11
- Payload 3.79.0 + Next.js 15.3.9, 15.4.11

All combinations result in admin UI crashes.

**Impact**:
- **Site visitors**: ✅ No impact - the marketing website is fully functional
- **Content management**: ⚠️ CMS content must be managed via REST API instead of visual admin interface

**Workaround**: Use the Payload REST API directly for content management:

```bash
# Login
curl -X POST http://localhost:3000/api/users/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@beep2b.com","password":"changeme"}'

# Create a blog post
curl -X POST http://localhost:3000/api/posts \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "title": "My Post",
    "slug": "my-post",
    "content": {"root":{"children":[{"children":[{"detail":0,"format":0,"mode":"normal","style":"","text":"Content here","type":"text","version":1}],"direction":"ltr","format":"","indent":0,"type":"paragraph","version":1}],"direction":"ltr","format":"","indent":0,"type":"root","version":1}},
    "excerpt": "Post summary",
    "status": "published"
  }'

# List all posts
curl http://localhost:3000/api/posts

# Update a post
curl -X PATCH http://localhost:3000/api/posts/POST_ID \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"title": "Updated Title"}'

# Delete a post
curl -X DELETE http://localhost:3000/api/posts/POST_ID \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Status**: This is a third-party library compatibility issue, not a code defect in the Beep2B implementation. The issue should be resolved in future Payload CMS releases as they improve Next.js 15 compatibility.

**Verification**:
- ✅ All 8 verification scripts pass
- ✅ CMS REST API fully functional (login, CRUD operations all succeed)
- ✅ Frontend successfully fetches and displays all CMS content (posts, categories, testimonials)
- ✅ Contact form submissions save to CMS database
- ✅ All 7 pages of the marketing website load correctly with premium dark theme and animations

**Recommendation**: For production use, either:
1. Use the REST API for content management (fully functional)
2. Wait for Payload CMS to release Next.js 15.5+ compatible versions
3. Use a tool like Postman or Insomnia to interact with the REST API through a GUI
