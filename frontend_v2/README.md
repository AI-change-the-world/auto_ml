# AutoML Workbench Frontend

Frontend workbench for AutoML Studio. It covers dataset browsing, annotation project management, image/text/multimodal annotation workbenches, DPO preference labeling, task tracking, deployment views, AI pipeline management, and the batch annotation tool workflow in a single React workspace.

## Scope

- Dataset list and detail pages for image, text, and multimodal datasets
- Annotation project management and full-screen workbenches for detection, classification, segmentation, pose, LLM conversation, MLLM conversation, and DPO preference workflows
- Task list and task detail tracking
- Deployment overview and deployment detail pages
- AI pipeline template, provider, and binding management
- Batch annotation tool management, run list, run detail, result preview, retry, and incremental execution
- Basic platform settings and bilingual UI support

## Stack

- React 19
- TypeScript 6
- Vite 8
- Ant Design 6
- Tailwind CSS 4
- Zustand
- Axios
- React Router 7

## Requirements

- Node.js `^20.19.0 || >=22.12.0`
- pnpm `>=10`

## Local development

Install dependencies:

```bash
pnpm install
```

Start the dev server:

```bash
pnpm dev
```

The app runs on `http://localhost:3000`.

By default, Vite proxies `/api` requests to `http://localhost:45678`. The frontend base URL is controlled by `VITE_API_BASE_URL`.

## Environment variables

Create a local env file when needed:

```bash
cp .env.example .env.local
```

Available variables:

- `VITE_API_BASE_URL`: API base path or absolute backend URL. Default: `/api`

Examples:

- `VITE_API_BASE_URL=/api`
- `VITE_API_BASE_URL=http://localhost:45678`

## Scripts

- `pnpm dev`: start the Vite development server
- `pnpm build`: run TypeScript build checks and create a production bundle
- `pnpm lint`: run ESLint
- `pnpm preview`: preview the production build locally

## Project structure

```text
src/
  api/          HTTP clients and request wrappers
  components/   Shared UI components
  hooks/        Reusable React hooks
  i18n/         Locale initialization and translation resources
  layouts/      Page layouts
  pages/        Route-level pages
  router/       History and route helpers
  stores/       Zustand stores
  types/        Shared TypeScript types
  utils/        Local utility functions
```

## Build and deploy

Create a production build:

```bash
pnpm build
```

Build the container image:

```bash
docker build -t automl-workbench-frontend .
```

Run the image locally:

```bash
docker run --rm -p 8080:80 automl-workbench-frontend
```

The container serves the static frontend and SPA routes. In the root `docker-compose.yml`, `/api` is proxied to `automl-server:45678`.
