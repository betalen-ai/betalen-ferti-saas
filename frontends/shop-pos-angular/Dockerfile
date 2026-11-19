@'
# Stage 1: Build
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN NODE_OPTIONS="--max-old-space-size=4096" npm run build -- --configuration production

# Stage 2: Serve
FROM nginx:alpine
# Changed to /app/dist/shop-pos (removed /browser)
COPY --from=build /app/dist/shop-pos /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
'@ | Set-Content Dockerfile -Encoding UTF8