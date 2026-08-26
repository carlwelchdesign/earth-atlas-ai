ARG NODE_IMAGE=node:20.20.1-alpine3.22@sha256:c0a3cda003a229d51f0f118c12a706842f43450ae505ed6825d66b5acdef127f
ARG NGINX_IMAGE=nginxinc/nginx-unprivileged:1.29.4-alpine@sha256:a6c4f61f456b85b8fdf7ec7ab28cc3e299440e6fb4a9dea520e5fd8fd440025e

FROM ${NODE_IMAGE} AS builder
WORKDIR /app
COPY package.json package-lock.json ./
COPY apps/workbench/package.json ./apps/workbench/package.json
RUN npm ci --ignore-scripts
COPY apps/workbench ./apps/workbench
RUN npm run build --workspace @echoatlas/workbench

FROM ${NGINX_IMAGE} AS runtime
COPY deploy/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/apps/workbench/dist /usr/share/nginx/html
EXPOSE 8080
HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=5 \
  CMD ["wget", "-qO-", "http://127.0.0.1:8080/healthz"]
