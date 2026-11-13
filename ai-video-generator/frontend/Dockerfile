FROM node:20-alpine
WORKDIR /app

COPY package.json ./
RUN npm install
COPY . .

ARG NEXT_PUBLIC_API_URL=http://localhost:8005
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}

RUN npm run build
EXPOSE 3005
CMD ["npm", "run", "start"]
