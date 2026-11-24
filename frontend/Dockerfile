# ResearchLens web UI: production Angular build served by nginx, which proxies /api.
FROM node:24-slim AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:1.31-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist/frontend/browser /usr/share/nginx/html
# index.html gets its public origin from SITE_ADDRESS at start; keep the build output.
COPY --from=build /app/dist/frontend/browser/index.html /usr/share/nginx/index.source.html
COPY --chmod=755 docker/40-site-origin.sh /docker-entrypoint.d/40-site-origin.sh
EXPOSE 80
