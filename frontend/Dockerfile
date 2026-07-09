FROM node:20-slim

WORKDIR /app

COPY package.json .

# Install dependencies and explicitly install compatible ajv versions
RUN npm install --legacy-peer-deps && \
    npm install ajv@8.12.0 ajv-keywords@5.1.0 --save --legacy-peer-deps

COPY . .

CMD ["npm", "start"]
