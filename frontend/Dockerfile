# Frontend (Next.js) production image. BACKEND_URL is read at runtime, not build,
# so the build never needs the API up.
FROM node:22-slim
WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

EXPOSE 3000
CMD ["npm", "run", "start"]
