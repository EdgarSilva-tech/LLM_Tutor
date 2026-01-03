FROM node:20-alpine AS build
WORKDIR /app
COPY services/frontend/package*.json ./
RUN [ -f package-lock.json ] && npm ci || npm install
COPY services/frontend/. .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
RUN printf 'server { listen 80; root /usr/share/nginx/html; include /etc/nginx/mime.types; location / { try_files $uri /index.html; } }' > /etc/nginx/conf.d/default.conf
