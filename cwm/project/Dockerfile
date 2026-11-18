FROM oven/bun:1.4.4@sha256:1d22548f177f4ff38e0c15baa3c2c46c6c2060ba2d1bc573bb4720b407548f1d
WORKDIR /opt/cwm
COPY package.json bun.lock ./
RUN bun install --frozen-lockfile --production --ignore-scripts
USER 65534:65534
WORKDIR /tmp
