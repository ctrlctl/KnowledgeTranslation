#!/bin/bash
# 将 production/*/images/ 同步到 output/web/images/{article_stem}/
# 用于 Cloudflare Pages 部署前

PROJ_ROOT="$(cd "$(dirname "$0")/../../../.." && pwd)"
SRC="$PROJ_ROOT/production"
DST="$PROJ_ROOT/output/web/images"

mkdir -p "$DST"

for img_dir in "$SRC"/*/images; do
    [ -d "$img_dir" ] || continue
    article="$(basename "$(dirname "$img_dir")")"
    mkdir -p "$DST/$article"
    cp -u "$img_dir"/* "$DST/$article/" 2>/dev/null
done

echo "已同步图片到 $DST"
