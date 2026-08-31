# syntax=docker/dockerfile:1

FROM node:22-alpine AS build
WORKDIR /app

COPY package.json ./
RUN yarn install

COPY . .
RUN yarn build

FROM node:22-alpine AS runtime
WORKDIR /app
ENV NODE_ENV=production

RUN npm install --global serve@14
COPY --from=build /app/build ./build

EXPOSE 3000
CMD ["sh", "-c", "serve -s build -l ${PORT:-3000}"]
