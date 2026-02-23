# Vision: LinkVault — Personal Bookmark Manager

## The Problem

A developer wants a simple way to save, organize, and browse bookmarks
without relying on browser-specific bookmark managers that don't travel
between devices.

## The User

**Dev** uses the browser to manage a collection of bookmarks with tags.

## The Solution

**LinkVault** is a Node.js + JSON-file app with two pages: a bookmark
collection and an analytics dashboard.

## What Success Looks Like

Dev opens `http://localhost:3000` and can:
- Add a bookmark with title, URL, and comma-separated tags
- See bookmarks displayed as cards in a responsive grid
- Filter bookmarks by clicking tag pills
- Delete bookmarks with a button on each card
- Navigate to `/dashboard` to see collection insights (total links, total tags,
  most-used tag, tag distribution bar chart, recent links)

## Complexity

This is a **multi-epic** project with 2 epics:

### Epic 1: Link Collection Interface
Express server, JSON file storage, bookmark CRUD API, responsive card grid UI
with tag filtering and delete.

### Epic 2: Analytics Dashboard
Stats API endpoint, dashboard page with stats cards, horizontal bar chart for
tag distribution, and recent links list.
