# ADR-0007: Fire-and-Forget Search Synchronization

## Status
Accepted

## Context

When books are created, updated, or deleted via the API, the changes must be reflected in the MeiliSearch index for search functionality to work correctly. The synchronization approach affects:
- API response latency
- Data consistency guarantees
- Error handling complexity
- User experience

Options considered:

1. **Fire-and-forget async** - Send to MeiliSearch, don't wait for response
2. **Synchronous blocking** - Wait for MeiliSearch confirmation before responding
3. **Background job queue** - Use Bull/BullMQ for reliable async processing
4. **Event-driven** - Publish events, separate worker consumes and syncs
5. **Periodic batch sync** - Sync all changes every N seconds

## Decision

We will use a fire-and-forget asynchronous pattern for search synchronization.

Implementation:
- PostgreSQL write completes first (source of truth)
- API fires async request to MeiliSearch to add/update/remove document
- API returns response immediately without waiting for MeiliSearch
- Search sync errors are logged but don't fail the API request

Code pattern:
```javascript
const book = await db.query(/* INSERT */);

// Fire-and-forget
search.addOrUpdate(book).catch(err =>
  console.error('[Search Sync] Error:', err)
);

res.status(201).json(book);
```

## Consequences

### What Becomes Easier

- **Fast API responses**: No blocking on search indexing (saves 20-50ms per request)
- **Fault tolerance**: Search service downtime doesn't break book management
- **Simple error handling**: Log errors, don't propagate to user
- **Better UX**: Users get immediate feedback when adding/editing books
- **Reduced coupling**: API is loosely coupled to search service

### What Becomes More Difficult

- **Eventual consistency**: Brief lag between DB write and searchability (typically < 100ms)
- **Silent failures**: Search sync errors might go unnoticed without log monitoring
- **Debugging**: If search results are stale, must check logs to diagnose
- **Testing**: Must account for async delay in integration tests

### Alternatives Considered

**Synchronous blocking**: Would ensure consistency but:
- Adds 20-50ms latency to every create/update/delete
- Search service downtime breaks all book operations
- Poor user experience (slower responses)

**Background job queue** (Bull/BullMQ): Would provide retry logic but:
- Adds significant complexity (Redis dependency, worker process)
- Overkill for this use case
- More moving parts to maintain and debug

**Event-driven architecture**: Would decouple well but:
- Requires message broker (RabbitMQ, Kafka, etc.)
- Much higher complexity for minimal benefit
- Additional infrastructure to manage

**Periodic batch sync**: Would work but:
- Larger lag between DB and search (seconds instead of milliseconds)
- More complex sync logic (detecting changes, handling deletes)
- Worse user experience

### Trade-offs Accepted

**Eventual Consistency**: We accept that there may be a brief period (typically < 100ms) where a newly added book doesn't appear in search results. This is acceptable because:
- Users typically return to the library view (refreshes from DB), not search
- The lag is imperceptible in normal use
- PostgreSQL remains the source of truth

**Silent Failures**: Search sync failures are logged but not surfaced to users. This is acceptable because:
- Search is a convenience feature, not critical functionality
- Users can still browse books by status filter (uses DB, not search)
- Logs provide visibility for operations/debugging
- MeiliSearch is reliable; failures are rare

### Error Handling Strategy

All search sync operations use this pattern:
```javascript
search.operation(data).catch(err => {
  console.error('[Search Sync] Error in operation:', err);
  // Don't throw - let request succeed
});
```

This ensures:
- User requests succeed even if search is down
- Errors are logged for debugging
- Application remains functional with degraded search

### Monitoring Recommendations

To mitigate silent failure risks:
- Monitor API logs for `[Search Sync]` errors
- Set up alerts for repeated sync failures
- Periodic health checks on MeiliSearch service
- Optional: Admin dashboard showing sync error rate

### Future Improvements

If fire-and-forget proves insufficient:
1. Add retry logic with exponential backoff
2. Implement a dead-letter queue for failed syncs
3. Build a manual re-sync endpoint for operations
4. Add metrics/monitoring for sync success rate
