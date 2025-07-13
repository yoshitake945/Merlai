# Merlai Frontend

> ⚠️ **Prototype Notice:**
> This frontend is currently in a prototype stage. Features, UI, and code structure are subject to major changes as development continues.

This directory contains the frontend (React + Vite) application for the Merlai project.

---

## Setup

1. Required Node.js version: **18.x**
2. Install dependencies

```sh
npm install
```

---

## Start Development Server

```sh
npm run dev
```

- Open [http://localhost:5173/](http://localhost:5173/) in your browser to view the app.

---

## Build for Production

```sh
npm run build
```
- The production build will be output to the `dist/` directory.

---

## Production Build & Run with Docker

1. Build the Docker image

```sh
docker build -t merlai-frontend .
```

2. Run the container

```sh
docker run -p 8080:80 merlai-frontend
```
- Access the app at [http://localhost:8080/](http://localhost:8080/)

---

## Main Dependencies

- React 18
- Vite
- @mui/material, @mui/icons-material
- react-router-dom
- @hello-pangea/dnd
- uuid

---

## Troubleshooting

- **Blank screen / React is not defined error**
  - Add `import React from 'react';` at the top of `App.jsx`.
  - Make sure `vite.config.js` is placed directly under `frontend/` and that `@vitejs/plugin-react` is enabled.
- **Invalid hook call / Multiple React copies**
  - Delete `node_modules` and `package-lock.json`, then run `npm install` again.
  - Ensure there are no extra `node_modules` folders in the project root or under `src/`.
- **Adding dependencies**
  - Use `npm install <package-name>` as needed.

---

## Directory Structure

```
frontend/
  ├── Dockerfile
  ├── nginx.conf
  ├── package.json
  ├── README.md  ← This file
  ├── index.html
  └── src/
      ├── App.jsx
      ├── main.jsx
      ├── theme.js
      ├── App.css
      ├── index.css
      └── assets/
          └── react.svg
```

---

## Other

- If you have any questions or issues, please contact a project maintainer or team member. 