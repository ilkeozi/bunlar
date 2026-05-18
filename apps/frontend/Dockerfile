# syntax=docker/dockerfile:1.7

FROM node:20-alpine AS build
WORKDIR /app
COPY package.json package-lock.json nx.json tsconfig.base.json tsconfig.json ./
COPY apps/frontend ./apps/frontend
RUN npm ci
RUN npx nx sync
RUN npx nx build frontend --skip-nx-cache

FROM nginx:1.27-alpine AS runner
WORKDIR /usr/share/nginx/html
COPY apps/frontend/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/apps/frontend/dist ./

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
