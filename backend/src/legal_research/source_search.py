"""Bounded CourtListener keyword search without model-generated interpretation."""
from __future__ import annotations

import time

from .corpus import excerpt, terms
from .courtlistener import SourceError


def in_scope(case, matter):
    return ((matter['court'] == 'all' or case.get('court') == matter['court'])
            and matter['date_from'] <= case.get('decision_date', '') <= matter['date_to'])


def search_terms(matter, feedback):
    reasons = [f.get('reason', '') for f in feedback.values() if f.get('relevance') == 'relevant']
    # An explicit, visible keyword baseline, not a model interpretation of the facts.
    feedback_words = list(dict.fromkeys(terms(' '.join(reasons))))[:6]
    question_words = [word for word in dict.fromkeys(terms(matter['question'])) if word not in feedback_words]
    keywords = feedback_words + question_words[:18-len(feedback_words)]
    return ' OR '.join('"' + word + '"' for word in keywords)


def source_passages(case, query):
    keywords = terms(query)
    sections = sorted(case.get('sections', []),
        key=lambda section: -len(set(terms(section['text'])) & set(keywords)))[:2]
    passages = []
    for section in sections:
        text = excerpt(section['text'], keywords)
        if not text.strip():
            continue
        offset = section['text'].find(text)
        start = section.get('text_start', 0) + offset
        passages.append({
            'text':text, 'section_number':section['section_number'], 'locator_type':'text_section',
            'locator_label':section.get('locator_label', f"Text section {section['section_number']}"),
            'source_url':section['source_url'], 'opinion_id':section['opinion_id'],
            'opinion_scope':section['opinion_scope'], 'text_start':start, 'text_end':start+len(text),
            'text_sha256':case.get('text_sha256'),
        })
    return passages


def run_source_search(source, matter, feedback, seen_ids, search_query=''):
    start = time.monotonic()
    query = search_query.strip() or search_terms(matter, feedback)
    selected, actions = [], []
    status, error = 'completed', None
    reason = 'No matching cases returned for this query and scope.'
    try:
        found = source.search(query, court=matter['court'], date_from=matter['date_from'],
            date_to=matter['date_to'], excluded_ids=seen_ids, limit=10) if query else []
        found = [case for case in found if in_scope(case, matter)]
        # Feedback changes order; it never excludes a case because of its outcome.
        def order(case):
            vote = feedback.get(case['id'], {}).get('relevance')
            return (case.get('text_status') == 'unavailable', case['id'] in seen_ids,
                    {'relevant':-1, 'not_relevant':1}.get(vote, 0))
        found.sort(key=order)
        actions.append({'tool':'courtlistener_search', 'detail':f'Query: {query}. Found {len(found)} candidates within unchanged court/date filters.'})
        actions.append({'tool':'feedback', 'detail': 'Used the explicit search terms when supplied; otherwise built visible keyword alternatives from the question and positive feedback reasons. Votes adjust ordering only; negative reasons are not interpreted without the model.'})
        unavailable_count = 0
        for candidate in found:
            if len(selected) >= 3:
                break
            if candidate.get('text_status') == 'unavailable':
                unavailable_count += 1
                actions.append({'tool':'unavailable_text', 'detail':f"A recent source check found no usable opinion text for {candidate['id']}; continuing with available candidates."})
                continue
            try:
                case = source.get_case(candidate['id'])
            except SourceError as failure:
                if failure.category != 'opinion_text_missing':
                    raise
                unavailable_count += 1
                actions.append({'tool':'unavailable_text', 'detail':f"No usable opinion text for {candidate['id']}; trying another candidate within the same filters and budget."})
                continue
            if not case or not in_scope(case, matter):
                continue
            passages = source_passages(case, query)
            short_record = len(case.get('canonical_text', '')) < 500
            explanation = 'CourtListener returned this case for the search query. Inspect the retrieved opinion to assess relevance; search ranking is not a legal conclusion.'
            if short_record:
                explanation += ' The retrieved text is short and may be only a procedural entry; do not assume it contains substantive reasoning.'
            selected.append({**candidate, 'passages':passages, 'explanation':explanation,
                'explanation_kind':'source_search_not_legal_analysis', 'is_new':candidate['id'] not in seen_ids,
                'text_status':'short_record' if short_record else 'retrieved', 'treatment_status':'not_checked'})
            actions.append({'tool':'read_case', 'detail':f"Read the available opinion for {candidate['id']}; saved {len(passages)} exact text excerpts."})
        new_count = sum(case['is_new'] for case in selected)
        if selected:
            reason = (f'Showing {len(selected)} source results; {new_count} new to this matter.' if new_count
                      else 'No new matching cases in the inspected search pages; showing previously seen matches.')
        elif unavailable_count:
            reason = f'No readable results from the inspected candidates; {unavailable_count} records had unavailable text. This does not establish that no relevant case exists.'
        discovery = getattr(source, 'last_search', {})
        if discovery.get('stopped_reason'):
            status = 'partial'
            reason += ' ' + discovery['stopped_reason']
            error = {'provider':'courtlistener', 'category':discovery.get('error_category', 'pagination_limit')}
            if discovery.get('retry_after') is not None:
                error['retry_after'] = discovery['retry_after']
    except SourceError as failure:
        status = 'partial' if selected else 'failed'
        reason = failure.message
        error = {'provider':'courtlistener', 'category':failure.category}
        if failure.retry_after is not None:
            error['retry_after'] = failure.retry_after
    except Exception:
        status = 'partial' if selected else 'failed'
        reason = 'Source retrieval could not finish; prior rounds remain available. Provider details were withheld.'
        error = {'provider':'courtlistener', 'category':'source_failure'}
    result = {'mode':'courtlistener_search', 'status':status, 'query':query, 'results':selected,
        'actions':actions, 'stop_reason':reason,
        'metrics':{'elapsed_ms':round((time.monotonic()-start)*1000), 'model_calls':0,
                   'model_cost_usd':0, **getattr(source, 'metrics', {})},
        'source_search':getattr(source, 'last_search', {})}
    if error:
        result['error'] = error
    return result
