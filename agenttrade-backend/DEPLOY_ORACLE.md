# Deploying on Oracle Cloud (Always Free)

## 1. Create the VM
Oracle Cloud console -> Compute -> Instances -> Create.
Use an Ampere A1 shape (ARM) — it's the free one with real headroom
(up to 4 OCPU / 24GB across your free-tier VMs). Ubuntu 22.04 image
is the simplest to work with.

## 2. Open the port — TWO firewalls to clear, both required
- **OCI Security List / NSG** (console): add ingress rules for TCP 80
  and 443 from 0.0.0.0/0. This is the cloud-level firewall — miss this
  and nothing else matters.
- **VM's own firewall** (iptables, on by default on Oracle's Ubuntu
  images):
  ```bash
  sudo iptables -I INPUT -p tcp --dport 80 -j ACCEPT
  sudo iptables -I INPUT -p tcp --dport 443 -j ACCEPT
  sudo netfilter-persistent save
  ```

## 3. Install Docker
```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
# log out and back in for the group change to apply
```

## 4. Get a free domain pointed at your VM
Sign up at duckdns.org (free), create a subdomain, point it at your
VM's public IP. Update the Caddyfile with that domain.

## 5. Deploy
```bash
git clone <your-repo-url>
cd agenttrade-backend
cp .env.example .env       # fill in real values — this file never gets committed
mkdir -p data
docker compose up -d --build
```

Caddy requests and renews the TLS cert automatically the first time
your domain resolves to the VM — no manual cert steps.

## 6. Updating later
```bash
git pull
docker compose up -d --build
```
Your SQLite db in `./data` survives this since it's a mounted volume,
not baked into the image.
