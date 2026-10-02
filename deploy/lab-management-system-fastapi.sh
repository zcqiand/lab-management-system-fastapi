#!/bin/sh
# Usage: lab-management-system-fastapi.sh <DOCKER_USERNAME> <DOCKER_PASSWORD> [VERSION]
#
# 由 .github/workflows/ci.yml 的 deploy job 远程调用:
#   ssh deploy@vps -- cd /home/deploy/lab-management-system-fastapi
#                    && sh lab-management-system-fastapi.sh $DOCKER_USERNAME $DOCKER_PASSWORD $VERSION
#
# VERSION 默认是 latest。tag-based deploy 时显式传 tag 名（v0.1.x-YYYYMMDD）。
# CI 同时 push :latest + :<tag> 两份镜像,回滚只要手动指定旧 tag 再跑一次本脚本。
#
# 与姊妹仓 lab-management-system-rails.sh 的差异:
#   - 运行时 Python 3.11 + uvicorn，健康探针 /health；端口 X07 段 5207（host=container）
#   - fastapi 读 DATABASE_URL 单串（postgresql://，impl/config.normalize_database_url
#     归一成 +psycopg2 方言）；PG_* 五件套只作 env-file 锚点，应用不读
#   - SSO 链 prod 值：LAB_SAAS_BASE_URL=https://saas-fastapi.xiangru.uk（同栈匹配，
#     lab-rails→saas-rails 同款原则）；登录页=saas-react（与栈无关）
#   - 服务账号 fail-fast：LAB_SAAS_SERVICE_USER/PASSWORD 缺失即败（2026-08-28 纪律，
#     禁 prod 静默吃 dev 默认 alice）
#
# 前置: deploy 用户需在 docker 组中(sudo usermod -aG docker deploy)。
#        fastapi.env 必须由 setup-vps.sh 或本脚本首启生成。

set -eu

USERNAME="${1:-}"
PASSWORD="${2:-}"
VERSION="${3:-latest}"
IMAGE="${USERNAME}/lab-management-system-fastapi:${VERSION}"
BASE="/home/deploy/lab-management-system-fastapi"
CONTAINER_NAME="lab-management-system-fastapi"

NGINX_DOMAIN="${NGINX_DOMAIN:-lab-fastapi.xiangru.uk}"
NGINX_CERT_BASENAME="${NGINX_CERT_BASENAME:-xiangru-uk}"

if [ -z "$USERNAME" ] || [ -z "$PASSWORD" ]; then
  echo "Usage: $0 <DOCKER_USERNAME> <DOCKER_PASSWORD> [VERSION]" >&2
  exit 2
fi

# 服务账号 fail-fast（ADR-0019 同族纪律：prod 身份字段禁兜底——缺了 login 后
# 拉菜单快照静默吃 dev 默认，黑洞 saas 降级直接 503）
if [ -z "${LAB_SAAS_SERVICE_USER:-}" ] || [ -z "${LAB_SAAS_SERVICE_PASSWORD:-}" ]; then
  echo "ERROR: LAB_SAAS_SERVICE_USER/LAB_SAAS_SERVICE_PASSWORD secrets required (菜单快照服务账号，禁 dev 兜底)" >&2
  exit 1
fi
if [ -z "${PG_PASSWORD:-}" ] || [ -z "${JWT_SIGNING_KEY:-}" ] || [ -z "${LAB_SAAS_CLIENT_SECRET:-}" ] || [ -z "${LAB_AUTH_DEV_PASSWORD:-}" ]; then
  echo "ERROR: PG_PASSWORD / JWT_SIGNING_KEY / LAB_SAAS_CLIENT_SECRET / LAB_AUTH_DEV_PASSWORD secrets required" >&2
  exit 1
fi

# fastapi.env 自举保护: 缺失时从 SSH env 透传的 secrets 生成（key 集合 = 应用
# AppConfig.from_env 全集 + PG/SERVER_PORT 锚点）; setup-vps.sh 仍是首推
# （VPS 一次性）, 本分支仅给"先有 env 临时上线"场景。
if [ ! -f "$BASE/fastapi.env" ]; then
  echo "→ bootstrapping $BASE/fastapi.env from SSH env secrets"
  umask 077
  {
    printf 'SERVER_PORT=5207\n'
    printf 'PG_HOST=%s\n' "${PG_HOST:-100.79.128.25}"
    printf 'PG_PORT=5432\n'
    printf 'PG_USER=%s\n' "${PG_USER:-postgres}"
    printf 'PG_PASSWORD=%s\n' "$PG_PASSWORD"
    printf 'PG_DATABASE=lab_prod\n'
    # 应用唯一读的库连接形态（fastapi 方言：postgresql://，运行时归一 +psycopg2）
    printf 'DATABASE_URL=postgresql://%s:%s@%s:5432/lab_prod\n' "${PG_USER:-postgres}" "$PG_PASSWORD" "${PG_HOST:-100.79.128.25}"
    printf 'JWT_SIGNING_KEY=%s\n' "$JWT_SIGNING_KEY"
    printf 'JWT_ISSUER=lab-management-system\n'
    printf 'JWT_TTL_SECONDS=3600\n'
    printf 'JWT_REFRESH_TTL_SECONDS=604800\n'
    # SSO 跳板：同栈匹配连 saas-fastapi（lab-rails→saas-rails 同款原则）
    printf 'LAB_SAAS_BASE_URL=https://saas-fastapi.xiangru.uk\n'
    # 登录 UI：saas-react 登录页已补 OAuth code 回跳（家族既有约定，与 lab 后端栈无关）
    printf 'LAB_SSO_LOGIN_URL=https://saas-react.xiangru.uk\n'
    printf 'LAB_SAAS_CLIENT_ID=lab-management\n'
    printf 'LAB_SAAS_CLIENT_SECRET=%s\n' "$LAB_SAAS_CLIENT_SECRET"
    printf 'LAB_SAAS_DEFAULT_TENANT_ID=%s\n' "${LAB_SAAS_DEFAULT_TENANT_ID:-00000000-0000-0000-0000-000000000001}"
    printf 'LAB_SSO_CALLBACK_REDIRECT=https://lab-react.xiangru.uk/login\n'
    printf 'LAB_SAAS_SERVICE_USER=%s\n' "$LAB_SAAS_SERVICE_USER"
    printf 'LAB_SAAS_SERVICE_PASSWORD=%s\n' "$LAB_SAAS_SERVICE_PASSWORD"
    printf 'LAB_SAAS_SERVICE_CLIENT_ID=lab-management\n'
    printf 'LAB_AUTH_DEV_PASSWORD=%s\n' "$LAB_AUTH_DEV_PASSWORD"
    printf 'LAB_CORS_ALLOWED_ORIGINS=https://lab-fastapi.xiangru.uk,https://lab-react.xiangru.uk,https://lab-vue.xiangru.uk,https://lab-nextjs.xiangru.uk,https://saas-react.xiangru.uk\n'
  } > "$BASE/fastapi.env"
  chown deploy:deploy "$BASE/fastapi.env" 2>/dev/null || true
  chmod 600 "$BASE/fastapi.env"
fi
if ! grep -q '^DATABASE_URL=' "$BASE/fastapi.env"; then
  echo "ERROR: $BASE/fastapi.env has no DATABASE_URL line" >&2
  exit 1
fi

# nginx vhost 重渲染（每次 deploy 都跑,ADR-0018:容器端口变了 vhost 必须跟）。
# 模板每次都从 master 拉最新 —— VPS 本地老模板会渲染出老端口全家族 502（2026-09-03 事故）。
NGINX_SITES_AVAILABLE="/etc/nginx/sites-available"
NGINX_SITES_ENABLED="/etc/nginx/sites-enabled"
NGINX_VHOST_FILE="${NGINX_SITES_AVAILABLE}/${NGINX_DOMAIN}"
NGINX_VHOST_LINK="${NGINX_SITES_ENABLED}/${NGINX_DOMAIN}"
NGINX_TEMPLATE="${BASE}/nginx-vps.conf.example"

echo "→ fetching nginx-vps.conf.example template (always fresh from master)"
curl -fsSL "https://raw.githubusercontent.com/zcqiand/lab-management-system-fastapi/refs/heads/master/deploy/nginx-vps.conf.example" -o "${NGINX_TEMPLATE}"

# 渲染到临时文件 —— sed 顺序：cert 归一化规则必须排在 <domain>/YOUR_DOMAIN 通配之前
# （先替换 <domain> 会把 cert 路径占位符一并吃掉,2026-09-03 事故根因）。
TMP_VHOST="$(mktemp -t vpstpl.XXXXXX)"
sed \
  -e "s|/etc/nginx/ssl/<domain>\.crt|/etc/nginx/ssl/${NGINX_CERT_BASENAME}.cert|g" \
  -e "s|/etc/nginx/ssl/<domain>\.cert|/etc/nginx/ssl/${NGINX_CERT_BASENAME}.cert|g" \
  -e "s|/etc/nginx/ssl/<domain>\.key|/etc/nginx/ssl/${NGINX_CERT_BASENAME}.key|g" \
  -e "s|/etc/nginx/ssl/your-cert\.crt|/etc/nginx/ssl/${NGINX_CERT_BASENAME}.cert|g" \
  -e "s|/etc/nginx/ssl/your-cert\.cert|/etc/nginx/ssl/${NGINX_CERT_BASENAME}.cert|g" \
  -e "s|/etc/nginx/ssl/your-cert\.key|/etc/nginx/ssl/${NGINX_CERT_BASENAME}.key|g" \
  -e "s|<domain>|${NGINX_DOMAIN}|g" \
  -e "s|lab\.YOUR_DOMAIN|${NGINX_DOMAIN}|g" \
  -e "s|saas\.YOUR_DOMAIN|${NGINX_DOMAIN}|g" \
  "${NGINX_TEMPLATE}" > "${TMP_VHOST}"

if [ -e "${NGINX_VHOST_FILE}" ] && diff -q "${TMP_VHOST}" "${NGINX_VHOST_FILE}" >/dev/null 2>&1; then
  echo "→ nginx vhost ${NGINX_VHOST_FILE} unchanged, skip"
  rm -f "${TMP_VHOST}"
else
  echo "→ rendering nginx vhost ${NGINX_VHOST_FILE} (domain=${NGINX_DOMAIN} cert=${NGINX_CERT_BASENAME})"
  if [ -w "${NGINX_SITES_AVAILABLE}" ]; then
    cp "${TMP_VHOST}" "${NGINX_VHOST_FILE}"
  else
    sudo cp "${TMP_VHOST}" "${NGINX_VHOST_FILE}" \
      || { echo "ERROR: sudo cp ${NGINX_VHOST_FILE} failed"; rm -f "${TMP_VHOST}"; exit 1; }
  fi
  if [ -w "${NGINX_SITES_ENABLED}" ]; then
    ln -sf "${NGINX_VHOST_FILE}" "${NGINX_VHOST_LINK}"
  else
    sudo ln -sf "${NGINX_VHOST_FILE}" "${NGINX_VHOST_LINK}" \
      || { echo "ERROR: sudo ln ${NGINX_VHOST_LINK} failed"; rm -f "${TMP_VHOST}"; exit 1; }
  fi
  rm -f "${TMP_VHOST}"
  echo "→ nginx -t"
  sudo nginx -t
  echo "→ systemctl reload nginx"
  sudo systemctl reload nginx
  echo "✓ nginx reloaded"
fi

# 存量 env-file 补键：逐 key append-if-missing 到 fastapi.env 全集
# (显式写值,漂移在 deploy 期暴露)。
if [ -f "$BASE/fastapi.env" ]; then
  append_if_missing() {
    key="$1"; val="$2"
    if ! grep -q "^${key}=" "$BASE/fastapi.env"; then
      echo "→ append ${key} to existing $BASE/fastapi.env"
      umask 077
      printf '%s=%s\n' "$key" "$val" >> "$BASE/fastapi.env"
    fi
  }
  append_if_missing SERVER_PORT '5207'
  append_if_missing PG_HOST '100.79.128.25'
  append_if_missing PG_PORT '5432'
  append_if_missing PG_USER 'postgres'
  append_if_missing PG_DATABASE 'lab_prod'
  append_if_missing JWT_ISSUER 'lab-management-system'
  append_if_missing JWT_TTL_SECONDS '3600'
  append_if_missing JWT_REFRESH_TTL_SECONDS '604800'
  append_if_missing LAB_SAAS_BASE_URL 'https://saas-fastapi.xiangru.uk'
  append_if_missing LAB_SSO_LOGIN_URL 'https://saas-react.xiangru.uk'
  append_if_missing LAB_SAAS_CLIENT_ID 'lab-management'
  append_if_missing LAB_SAAS_DEFAULT_TENANT_ID '00000000-0000-0000-0000-000000000001'
  append_if_missing LAB_SSO_CALLBACK_REDIRECT 'https://lab-react.xiangru.uk/login'
  append_if_missing LAB_SAAS_SERVICE_CLIENT_ID 'lab-management'

  # 密钥类双模 append：缺 key 追加；key 在但值为空/CHANGE_ME 也覆盖
  # （bootstrap 残留占位会让 fastapi 启动即 RuntimeError 或 SSO 401，
  # append_if_missing 见行存在跳过 → 容器起来即坏。空值与占位值都必须 reconcile。）
  upsert_if_placeholder() {
    key="$1"; val="$2"
    if ! grep -q "^${key}=..*" "$BASE/fastapi.env" \
       || grep -q "^${key}=$" "$BASE/fastapi.env" \
       || grep -q "^${key}=CHANGE_ME$" "$BASE/fastapi.env"; then
      echo "→ upsert ${key} to existing $BASE/fastapi.env"
      sed -i "s#^${key}=.*#${key}=${val}#" "$BASE/fastapi.env"
    fi
  }
  upsert_if_placeholder PG_PASSWORD "$PG_PASSWORD"
  upsert_if_placeholder JWT_SIGNING_KEY "$JWT_SIGNING_KEY"
  upsert_if_placeholder LAB_SAAS_CLIENT_SECRET "$LAB_SAAS_CLIENT_SECRET"
  upsert_if_placeholder LAB_SAAS_SERVICE_USER "$LAB_SAAS_SERVICE_USER"
  upsert_if_placeholder LAB_SAAS_SERVICE_PASSWORD "$LAB_SAAS_SERVICE_PASSWORD"
  upsert_if_placeholder LAB_AUTH_DEV_PASSWORD "$LAB_AUTH_DEV_PASSWORD"

  # origin 级无损追加（家族同款）：lab 三前端 + saas 登录页 + 本域都可跨源调本后端，
  # 存量 env-file 缺哪个 origin 就补哪个（不整值覆盖，运维手工 origin 保留）。
  for cors_origin in "https://${NGINX_DOMAIN}" \
                     "https://lab-nextjs.xiangru.uk" \
                     "https://lab-react.xiangru.uk" \
                     "https://lab-vue.xiangru.uk" \
                     "https://saas-react.xiangru.uk"; do
    if grep -q '^LAB_CORS_ALLOWED_ORIGINS=' "$BASE/fastapi.env" && ! grep '^LAB_CORS_ALLOWED_ORIGINS=' "$BASE/fastapi.env" | grep -qF "$cors_origin"; then
      sed -i "s#^\(LAB_CORS_ALLOWED_ORIGINS=.*\)#\1,${cors_origin}#" "$BASE/fastapi.env"
      echo "→ reconcile LAB_CORS_ALLOWED_ORIGINS: 追加缺失 origin ${cors_origin}（origin 级，不整值覆盖）"
    fi
  done
fi

echo "→ image: $IMAGE"
echo "→ docker login"
printf '%s' "$PASSWORD" | docker login -u "$USERNAME" --password-stdin

echo "→ docker pull"
docker pull "$IMAGE"

echo "→ docker stop & rm $CONTAINER_NAME"
docker stop "$CONTAINER_NAME" 2>/dev/null || true
docker rm "$CONTAINER_NAME" 2>/dev/null || true

echo "→ docker run"
docker run -d \
  --name "$CONTAINER_NAME" \
  --restart unless-stopped \
  -p "127.0.0.1:5207:5207" \
  --env-file "$BASE/fastapi.env" \
  "$IMAGE"

echo "→ docker image prune"
docker image prune -f

echo "→ docker ps"
docker ps --filter name="$CONTAINER_NAME"

# 健康检查: 直接 wget /health 探 200。容器死亡提前终止循环, 立刻报失败。
i=0
while [ $i -lt 120 ]; do
  if wget --tries=1 --timeout=3 -q "http://127.0.0.1:5207/health" -O /dev/null 2>/dev/null; then
    echo "→ /health 200 (host 127.0.0.1:5207) after ${i}s"
    break
  fi
  if ! docker inspect --format='{{.State.Running}}' "$CONTAINER_NAME" 2>/dev/null | grep -q true; then
    echo "→ container not running, logs:"
    docker logs --tail 30 "$CONTAINER_NAME"
    exit 1
  fi
  i=$((i+1))
  sleep 1
done

if [ $i -ge 120 ]; then
  echo "→ /health 仍未 200（120s 上限）, logs:"
  docker logs --tail 30 "$CONTAINER_NAME"
  exit 1
fi

echo "→ deploy done at $(date -u)"
