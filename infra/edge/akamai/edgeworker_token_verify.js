function b64urlToStr(b64url) {
  var b64 = b64url.replace(/-/g, '+').replace(/_/g, '/');
  var pad = b64.length % 4;
  if (pad) b64 += new Array(5 - pad).join('=');
  var bin = Buffer.from(b64, 'base64').toString('binary');
  var s = '';
  for (var i = 0; i < bin.length; i++) s += String.fromCharCode(bin.charCodeAt(i));
  return decodeURIComponent(escape(s));
}

function parseJwtPayload(token) {
  var parts = token.split('.');
  if (parts.length < 2) throw new Error('bad token');
  var json = b64urlToStr(parts[1]);
  return JSON.parse(json);
}

export function responseProvider(request) {
  var url = new URL(request.url);
  var token = url.searchParams.get('t');
  if (!token) return { status: 401, body: 'Missing token' };
  var ref = request.headers.get('referer') || '';
  if (ref && ref.indexOf('tapmad.com') === -1) return { status: 403, body: 'Bad referrer' };
  try {
    var payload = parseJwtPayload(token);
    var now = Math.floor(Date.now() / 1000);
    var exp = Number(payload.exp || 0);
    var iat = Number(payload.iat || (exp ? exp - 120 : 0));
    if (!exp || now > exp) return { status: 401, body: 'Expired' };
    if (exp - iat > 120) return { status: 401, body: 'TTL too long' };
    if (!payload.uid || typeof payload.uid !== 'string') return { status: 401, body: 'Missing uid' };
    return { status: 200, body: 'OK' };
  } catch (e) {
    return { status: 401, body: 'Invalid token' };
  }
}


