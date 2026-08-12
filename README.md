# Deployment

Baseline project: https://github.com/kabeier/Simple-Deployment-Demo

Deploy from a **standalone repo**, not the course monorepo.

---


## 1. Prep your project (already done)

- `server/Dockerfile` → `FROM python:3.13-slim`
- `client/Dockerfile` → `FROM node:22-alpine`, and `RUN npm ci`
- `docker-compose.yml` → remove the `./client/dist:/usr/share/nginx/html` volume
- `server/task_api/settings.py` → `ALLOWED_HOSTS = ['*']`
- Keep `baseURL: '/api/v1/'` relative — do not hardcode the IP
- Commit a `server/.env.example`; keep the real `.env` gitignored
- Push to GitHub

## 2. Create an EC2 instance

- `t3.micro`, **Ubuntu Server 24.04 LTS**
- Create and download a PEM key
- Security group inbound:
  - SSH (22) → **My IP**
  - HTTP (80) → Anywhere
  - HTTPS (443) → Anywhere
- Allocate an **Elastic IP** and associate it with the instance

## 3. SSH in

```bash
mv ~/Downloads/<name_of_key>.pem ~/.ssh/
chmod 600 ~/.ssh/<name_of_key>.pem
ssh -i ~/.ssh/<name_of_key>.pem ubuntu@<ipv4_address>
```

## 4. Install Docker

```bash
sudo apt update
sudo apt install -y docker.io docker-compose-v2
sudo systemctl status docker --no-pager
```

Add yourself to the `docker` group, then reconnect:

```bash
sudo usermod -aG docker ubuntu
exit
```

```bash
ssh -i ~/.ssh/<name_of_key>.pem ubuntu@<ipv4_address>
docker ps
```

> The reconnect is required — group membership only loads at login.

## 5. Clone the repo

```bash
git clone https://github.com/kabeier/Simple-Deployment-Demo
cd Simple-Deployment-Demo
```

## 6. Create `.env` on the server

```bash
cp server/.env.example server/.env
nano server/.env        # set a real POSTGRES_PASSWORD
```

> `.env` is gitignored, so it does not exist after a fresh clone. Without it
> `docker compose up` fails immediately with `env file ... not found`.

## 7. Build and run

```bash
docker compose up -d --build
docker compose ps       # expect 3 containers Up
```

## 8. Migrate

```bash
docker exec -it django-container python manage.py migrate
```

## 9. Verify

```
http://<ipv4_address>
```

Use `http://`, not `https://` — nothing is on 443 yet. Register an account and
create a task.

```bash
docker logs -f nginx-container    # Ctrl+C to stop
```

## 10. Exit

```bash
exit    # containers keep running because of -d
```

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `UNPROTECTED PRIVATE KEY FILE` | `chmod 600 ~/.ssh/<key>.pem` |
| `Permission denied (publickey)` | use `ubuntu@`, not `ec2-user@` |
| `ssh: connect ... timed out` | your IP changed — update the SG's SSH rule |
| `Error opening terminal: xterm-kitty` | `export TERM=xterm-256color` |
| `permission denied ... docker daemon socket` | `exit` and ssh back in |
| `docker compose` → `is not a docker command` | install `docker-compose-v2`; use a **space** |
| `env file ... not found` | step 6 — create `server/.env` |
| Page loads but register/login **400** | `ALLOWED_HOSTS` missing `'*'` |
| Site loads blank / 404 | `client/dist` bind mount still in compose |
| Build killed, `exit code 137` | out of RAM — add swap (below) |
| `502 Bad Gateway` | `docker logs django-container` |

```bash
# 2 GB swap if the vite build OOMs on t3.micro
sudo fallocate -l 2G /swapfile && sudo chmod 600 /swapfile
sudo mkswap /swapfile && sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```
