# Vision: TaskPad — Minimal Task Tracker

## The Problem

A developer wants a dead-simple task tracker they can run locally — just add
tasks, mark them done, and see what's left. No frameworks, no databases, just
a single HTML file served by a tiny Node server.

## The User

**Dev** uses the browser to manage a short list of tasks.

## The Solution

**TaskPad** is a Node.js + JSON-file app with two pages: a task list and a
simple stats page.

## What Success Looks Like

Dev opens `http://localhost:3000` and can:
- See all tasks in a list
- Add a new task with a title
- Mark a task as done (checkbox toggle)
- Switch to a stats page showing total/done/remaining counts

## Complexity

This is a **multi-epic** project with 2 epics:

### Epic 1: Task CRUD
Server, JSON persistence, task list UI with add/toggle/delete.

### Epic 2: Stats Page
Stats route returning counts, stats view with total/done/remaining.
