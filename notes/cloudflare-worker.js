// Cloudflare Worker: 托管 flashcards.html + KV 读写 API
// 绑定 KV 命名空间时变量名设为 FLASHCARDS_KV

const AUTH_TOKEN = 'YOUR_SECRET_TOKEN_HERE'; // 改成你自己的密码

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const path = url.pathname;

    // CORS headers
    const corsHeaders = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    };

    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders });
    }

    // API: 读取数据
    if (path === '/api/load' && request.method === 'GET') {
      const data = await env.FLASHCARDS_KV.get('user_data', 'json');
      return new Response(JSON.stringify(data || {}), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }

    // API: 保存数据
    if (path === '/api/save' && request.method === 'POST') {
      const auth = request.headers.get('Authorization');
      if (auth !== `Bearer ${AUTH_TOKEN}`) {
        return new Response('Unauthorized', { status: 401, headers: corsHeaders });
      }
      const body = await request.json();
      await env.FLASHCARDS_KV.put('user_data', JSON.stringify(body));
      return new Response('OK', { headers: corsHeaders });
    }

    // 默认：返回 flashcards.html（从 KV 中读取，或内嵌）
    if (path === '/' || path === '/index.html') {
      const html = await env.FLASHCARDS_KV.get('page_html');
      if (html) {
        return new Response(html, {
          headers: { ...corsHeaders, 'Content-Type': 'text/html;charset=UTF-8' }
        });
      }
      return new Response('Page not found. Upload HTML via /api/upload', { status: 404 });
    }

    // API: 上传 HTML（用于更新页面内容）
    if (path === '/api/upload' && request.method === 'POST') {
      const auth = request.headers.get('Authorization');
      if (auth !== `Bearer ${AUTH_TOKEN}`) {
        return new Response('Unauthorized', { status: 401, headers: corsHeaders });
      }
      const html = await request.text();
      await env.FLASHCARDS_KV.put('page_html', html);
      return new Response('Uploaded', { headers: corsHeaders });
    }

    return new Response('Not found', { status: 404 });
  }
};
