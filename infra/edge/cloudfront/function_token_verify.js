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

function handler(event) {
  var request = event.request;
  var qs = request.querystring;
  if (!qs.t || !qs.t.value) {
    return { statusCode: 401, statusDescription: 'Missing token' };
  }
  var ref = request.headers && request.headers.referer && request.headers.referer.value || '';
  if (ref && ref.indexOf('tapmad.com') === -1) {
    return { statusCode: 403, statusDescription: 'Bad referrer' };
  }
  try {
    var payload = parseJwtPayload(qs.t.value);
    var now = Math.floor(Date.now() / 1000);
    var exp = Number(payload.exp || 0);
    var iat = Number(payload.iat || (exp ? exp - 120 : 0));
    if (!exp || now > exp) return { statusCode: 401, statusDescription: 'Expired' };
    if (exp - iat > 120) return { statusCode: 401, statusDescription: 'TTL too long' };
    if (!payload.uid || typeof payload.uid !== 'string') return { statusCode: 401, statusDescription: 'Missing uid' };
    return request;
  } catch (e) {
    return { statusCode: 401, statusDescription: 'Invalid token' };
  }
}


