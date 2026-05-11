#!/bin/bash
# 上传 flashcards.html 到 Cloudflare Worker
curl -X POST https://flashcards.lqita507.workers.dev/api/upload \
  -H "Authorization: Bearer 233996" \
  --data-binary @"$(dirname "$0")/flashcards.html"
echo ""
echo "上传完成"
