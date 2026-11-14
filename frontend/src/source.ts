import type { CaseResult, Passage, ResearchSource } from './types';

export function canSearch(options: {
  source: ResearchSource; corpusCount: number; courtlistenerAvailable: boolean;
  consentSource: boolean; useModel: boolean; agentAvailable: boolean; consentModel: boolean;
}) {
  const sourceReady = options.source === 'courtlistener'
    ? options.courtlistenerAvailable && options.consentSource
    : options.corpusCount > 0;
  return sourceReady && (!options.useModel || options.agentAvailable && options.consentModel);
}

export function passageLocation(passage: Passage) {
  // Links come from the stored source snapshot. Section numbers are app locators,
  // never PDF pages, reporter pinpoints, or invented URL fragments.
  return {
    url: passage.source_url,
    label: passage.pdf_page !== undefined ? `PDF page ${passage.pdf_page}`
      : passage.locator_label || (passage.section_number !== undefined ? `Text section ${passage.section_number}` : 'Source passage'),
  };
}

export function isCourtListenerCase(item: CaseResult) {
  return item.retrieval_mode?.startsWith('courtlistener') || item.id.startsWith('cl-')
    || item.passages.some(passage => passage.section_number !== undefined);
}
