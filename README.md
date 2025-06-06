# Orchids SWE Intern Challenge Template

This project consists of a backend built with FastAPI and a frontend built with Next.js and TypeScript.

## Backend

The backend uses `uv` for package management.

### Installation

To install the backend dependencies, run the following command in the backend project directory:

```bash
uv sync
```

### Running the Backend

Please set your OpenRouter and HyperBrowserAPI keys in the backend .env: HYPERBROWSER_API_KEY and OPENROUTER_API_KEY

Also feel free to change the model. google/gemini-2.5-pro-preview is the best, but it is fairly slow and expensive. google/gemini-2.5-flash-preview-05-20 is fast and good enough.

To run the backend development server, use the following command:

```bash
uv run fastapi dev
```

## Frontend

The frontend is built with Next.js and TypeScript.

### Installation

To install the frontend dependencies, navigate to the frontend project directory and run:

```bash
npm install
```

### Running the Frontend

To start the frontend development server, run:

```bash
npm run dev
```
