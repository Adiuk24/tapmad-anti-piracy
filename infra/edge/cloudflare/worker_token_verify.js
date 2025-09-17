function b64urlToStr(b64url) {
  let b64 = b64url.replace(/-/g, '+').replace(/_/g, '/');
  const pad = b64.length % 4;
  if (pad) b64 += '='.repeat(4 - pad);
  const bin = atob(b64);
  let s = '';
  for (let i = 0; i < bin.length; i++) s += String.fromCharCode(bin.charCodeAt(i));
  return decodeURIComponent(escape(s));
}

function parseJwtPayload(token) {
  const parts = token.split('.');
  if (parts.length < 2) throw new Error('bad token');
  const json = b64urlToStr(parts[1]);
  return JSON.parse(json);
}

export default {
  async fetch(request) {
    const url = new URL(request.url);
    const token = url.searchParams.get('t');
    if (!token) return new Response('Missing token', { status: 401 });
    const ref = request.headers.get('referer') || '';
    if (ref && !ref.includes('tapmad.com')) return new Response('Bad referrer', { status: 403 });
    try {
      const payload = parseJwtPayload(token);
      const now = Math.floor(Date.now() / 1000);
      const exp = Number(payload.exp || 0);
      const iat = Number(payload.iat || (exp ? exp - 120 : 0));
      if (!exp || now > exp) return new Response('Expired', { status: 401 });
      if (exp - iat > 120) return new Response('TTL too long', { status: 401 });
      if (!payload.uid || typeof payload.uid !== 'string') return new Response('Missing uid', { status: 401 });
      return new Response('OK');
    } catch (e) {
      return new Response('Invalid token', { status: 401 });
    }
  },
};


