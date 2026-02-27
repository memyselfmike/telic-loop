# Vision: NoteBox — Tiny Notes App

## The Problem

A user wants a minimal note-taking app they can run locally — create notes,
view them, and track basic stats. No frameworks, no databases, just a Node
server with JSON-file persistence.

## The User

**User** opens the browser to manage short text notes.

## The Solution

**NoteBox** is a Node.js + Express app with JSON-file storage and two pages:
a notes list and a stats dashboard.

## What Success Looks Like

User opens `http://localhost:3000` and can:
- See all notes in a list (title + preview of body)
- Click "New Note" to create a note with a title and body
- Click a note to view its full content
- Delete a note
- Switch to a stats page showing total notes, average body length, and
  newest/oldest note dates

## Complexity

This is a **multi-epic** project with 2 epics:

### Epic 1: Notes CRUD
Express server, JSON persistence, notes list UI with create/view/delete.

### Epic 2: Stats Dashboard
Stats API endpoint returning aggregate data, stats page with total count,
average length, and date range.
