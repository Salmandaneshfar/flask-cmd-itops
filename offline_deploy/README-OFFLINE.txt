# Offline deployment steps (server has no internet)

1) On an online machine:
   - docker build -t flask-cms:prod .
   - docker pull postgres:15-alpine redis:7-alpine nginx:alpine dpage/pgadmin4:latest
   - docker save -o flask-cms-images.tar flask-cms:prod postgres:15-alpine redis:7-alpine nginx:alpine dpage/pgadmin4:latest
   - Copy this folder (offline_deploy) and flask-cms-images.tar to the server.

2) On the offline server:
   - docker load -i /path/to/flask-cms-images.tar
   - Place production.env beside docker-compose.prod.yml
   - docker-compose -f docker-compose.prod.yml up -d

Paths mounted:
- ./static/uploads -> /app/static/uploads
- ./logs -> /app/logs
- ./backups -> /app/backups

Health:
- curl http://localhost/health

Notes:
- Change SECRET_KEY/DB_PASSWORD/REDIS_PASSWORD before running.
- Put SSL certs in ssl/ and configure nginx if needed.
