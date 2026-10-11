#!/usr/bin/env bash
# 一键部署脚本(阶段9): 在 Linux 服务器上执行
#   首次部署: ./deploy.sh
#   后续更新: ./deploy.sh (拉取最新代码 + 重建镜像 + 重启)
set -euo pipefail

REPO_URL="${1:-https://github.com/Serendipity0807/Smart-Travel-Assistant.git}"
DIR_NAME="Smart-Travel-Assistant"

# 1. 检查 Docker, 没有则安装(国内镜像加速用 daocloud)
if ! command -v docker >/dev/null 2>&1; then
  echo "==> 安装 Docker..."
  curl -fsSL https://get.docker.com | sh
  sudo mkdir -p /etc/docker
  sudo tee /etc/docker/daemon.json >/dev/null <<'EOF'
{
  "registry-mirrors": ["https://docker.m.daocloud.io"]
}
EOF
  sudo systemctl enable --now docker
  sudo systemctl restart docker
fi

# 2. 拉取代码
if [ ! -d "$DIR_NAME/.git" ]; then
  git clone "$REPO_URL" "$DIR_NAME"
fi
cd "$DIR_NAME"
git pull --ff-only

# 3. 检查密钥文件(从模板复制, 让用户填真实密钥)
if [ ! -f backend/.env ]; then
  cp backend/.env.example backend/.env
  echo "==> 请先编辑 backend/.env 填入真实密钥(LLM_API_KEY / AMAP_MAPS_API_KEY / UNSPLASH_ACCESS_KEY),"
  echo "    然后重新运行 ./deploy.sh"
  exit 1
fi

# 4. 构建并启动
docker compose up -d --build
docker compose ps

echo ""
echo "==> 部署完成, 验证: curl http://localhost/api/health"
echo "==> 别忘去高德控制台把服务器域名/IP 加进 Web端(JS API) key 的白名单"
