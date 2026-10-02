# lab-management-system-fastapi — prod 容器（X07 段 5207，host=container）
#
# 家族 deploy 链同款（rails/springboot/aspnetcore 先例）：
#   VPS nginx 终结 TLS → proxy_pass http://127.0.0.1:5207 → 容器 uvicorn。
#   CI deploy job build & push（latest + tag 双份）→ VPS deploy/deploy*.sh 拉镜像起容器。
#
# 端口是家族契约（docs/conventions/multi-repo-family.md §6 X07=5207），钉死在
# CMD 里不走 env 兜底（suite 硬规则 §1 同款口径：fail-fast，不留静默默认）。
#
# 运行时依赖（sqlalchemy / psycopg2-binary）已升进 pyproject 主依赖（镜像 saas 仓
# 2026-10-02 首航事故修复：sqlalchemy 只经 dev 组传递带入，镜像容器 import 即炸；
# psycopg2 原靠本文件 build 补丁——两处一并归位主依赖，此处只装包本体）。
FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml ./
COPY src/ ./src/

RUN pip install --no-cache-dir .

EXPOSE 5207
CMD ["uvicorn", "lab_management_system_fastapi.app:app", "--host", "0.0.0.0", "--port", "5207"]
