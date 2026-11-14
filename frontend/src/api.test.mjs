import test from 'node:test';
import assert from 'node:assert/strict';
import { ConnectionError, requestAPI } from './api.ts';

function options(fetcher) {
  let token = 'old';
  return { getToken: () => token, setToken: value => { token = value; }, fetcher };
}
const json = (value, status = 200) => new Response(JSON.stringify(value), { status, headers: { 'Content-Type': 'application/json' } });

test('lost write response gives recovery instructions without replaying mutation', async () => {
  let calls = 0;
  const client = options(async () => { calls++; throw new TypeError('Failed to fetch'); });
  await assert.rejects(requestAPI('/api/matters', 'POST', { title: 'Preserved draft' }, client), error => error instanceof ConnectionError && error.message.includes('scripts/start_local.py'));
  assert.equal(calls, 1);
});

test('known pre-handler session rejection refreshes token and retries the same request once', async () => {
  const calls = [];
  const client = options(async (url, init) => {
    calls.push({ url, init });
    if (calls.length === 1) return json({ detail: 'Refresh the workspace to obtain a local session token' }, 403);
    if (url === '/api/bootstrap') return json({ csrf_token: 'fresh' });
    return json({ id: 'saved' });
  });
  assert.deepEqual(await requestAPI('/api/matters', 'POST', { title: 'Draft' }, client), { id: 'saved' });
  assert.equal(calls.length, 3);
  assert.equal(calls[2].init.headers['X-Workspace-Token'], 'fresh');
  assert.equal(calls[2].init.body, calls[0].init.body);
});

test('arbitrary 403 and repeated session rejection do not loop or replay blindly', async () => {
  let calls = 0;
  await assert.rejects(requestAPI('/api/matters', 'POST', {}, options(async () => { calls++; return json({detail:'Cross-origin access is not permitted'},403); })), /Cross-origin/);
  assert.equal(calls,1);
  calls = 0;
  await assert.rejects(requestAPI('/api/matters','POST',{},options(async url => {
    calls++;
    return url === '/api/bootstrap' ? json({csrf_token:'fresh'}) : json({detail:'Refresh the workspace to obtain a local session token'},403);
  })), /local session token/);
  assert.equal(calls,3);
});
