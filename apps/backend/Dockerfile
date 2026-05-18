# syntax=docker/dockerfile:1.7

FROM node:20-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --omit=dev

FROM node:20-alpine AS build
WORKDIR /app
COPY package.json package-lock.json nx.json tsconfig.base.json tsconfig.json eslint.config.mjs ./
COPY apps/backend ./apps/backend
RUN npm ci
RUN npx nx sync
RUN npx nx build backend --skip-nx-cache

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production

# Keep runtime image small while preserving all required runtime deps.
COPY --from=deps /app/node_modules ./node_modules
COPY --from=build /app/apps/backend/dist ./apps/backend/dist
COPY apps/backend/.env.example ./apps/backend/.env.example

EXPOSE 3000

CMD ["node", "apps/backend/dist/main.js"]
