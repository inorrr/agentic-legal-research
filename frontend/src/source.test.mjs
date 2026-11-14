import assert from 'node:assert/strict';
import test from 'node:test';
import { canSearch, isCourtListenerCase, passageLocation } from './source.ts';

const ready = { source: 'courtlistener', corpusCount: 0, courtlistenerAvailable: true,
  consentSource: true, useModel: false, agentAvailable: false, consentModel: false };

test('live source works without local opinions and requires its own consent', () => {
  assert.equal(canSearch(ready), true);
  assert.equal(canSearch({ ...ready, consentSource: false }), false);
  assert.equal(canSearch({ ...ready, courtlistenerAvailable: false }), false);
  assert.equal(canSearch({ ...ready, consentSource: false, consentModel: true }), false);
});

test('model and source consent are independent; local retrieval remains available', () => {
  assert.equal(canSearch({ ...ready, useModel: true, agentAvailable: true }), false);
  assert.equal(canSearch({ ...ready, useModel: true, agentAvailable: true, consentModel: true }), true);
  assert.equal(canSearch({ ...ready, useModel: true, consentModel: true }), false);
  assert.equal(canSearch({ ...ready, source: 'local', corpusCount: 6, courtlistenerAvailable: false, consentSource: false }), true);
  assert.equal(canSearch({ ...ready, source: 'local', corpusCount: 0 }), false);
});

test('HTML evidence preserves source URLs and never invents PDF page fragments', () => {
  const passage = { source_url: 'https://www.courtlistener.com/opinion/123/example/', section_number: 4,
    locator_label: 'Text section 4', text: 'Synthetic evidence', opinion_scope: 'lead opinion' };
  assert.deepEqual(passageLocation(passage), { url: passage.source_url, label: 'Text section 4' });
  assert.equal(passageLocation({ ...passage, locator_label: undefined }).label, 'Text section 4');
  assert.equal(passageLocation({ ...passage, locator_label: undefined, section_number: undefined }).label, 'Source passage');
  assert.equal(isCourtListenerCase({ id: 'cl-123', passages: [] }), true);
});

test('saved PDF evidence retains its existing page URL and PDF label', () => {
  const passage = { source_url: 'https://www.govinfo.gov/example.pdf#page=5', pdf_page: 5,
    text: 'Synthetic text', opinion_scope: 'unsegmented_pdf_page' };
  assert.deepEqual(passageLocation(passage), { url: passage.source_url, label: 'PDF page 5' });
  assert.equal(isCourtListenerCase({ id: 'example', retrieval_mode: 'local_lexical', passages: [passage] }), false);
});
