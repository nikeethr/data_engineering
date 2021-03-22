FROM node:15-alpine AS builder

COPY app /app
WORKDIR /app

RUN npm install
RUN npm run prepublish
RUN cp /app/src/index.html /app/output/index.html && \
    cp /app/src/style.css /app/output/style.css && \
    cp -r /app/node_modules /app/output/node_modules

FROM nginx:latest

WORKDIR /app
COPY --from=builder /app/output /app

