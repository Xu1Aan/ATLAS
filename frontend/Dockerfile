ARG NODE_BASE_IMAGE=docker.m.daocloud.io/library/node:20-alpine
ARG NGINX_BASE_IMAGE=docker.m.daocloud.io/library/nginx:1.27-alpine
FROM ${NODE_BASE_IMAGE} AS build

ARG NPM_REGISTRY=https://registry.npmmirror.com

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm config set registry "${NPM_REGISTRY}" && npm ci

COPY . .
RUN npm run build

FROM ${NGINX_BASE_IMAGE}

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
