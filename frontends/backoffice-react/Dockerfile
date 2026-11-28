FROM node:20-alpine AS build
WORKDIR /app

COPY package*.json ./
# Use npm ci or npm install, depending on whether lockfile exists
RUN npm ci --include=dev || npm install

COPY . .
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV PORT=3000
ENV HOST=0.0.0.0

COPY --from=build /app/.output ./.output

EXPOSE 3000
CMD ["node", ".output/server/index.mjs"]