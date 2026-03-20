FROM node:22-bookworm

RUN apt-get update \
  && apt-get install -y --no-install-recommends python3 python3-pip python3-venv \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace/src/frontend

COPY src/frontend/package.json src/frontend/package-lock.json ./
RUN npm ci

COPY src/backend/requirements.txt /tmp/backend-requirements.txt
RUN python3 -m pip install --break-system-packages -r /tmp/backend-requirements.txt

RUN npx playwright install --with-deps chromium

COPY . /workspace

CMD ["npm", "run", "dev", "--", "--hostname", "0.0.0.0", "--port", "3000"]
