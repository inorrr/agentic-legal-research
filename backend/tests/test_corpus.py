"""Synthetic corpus fixtures; these are not real legal relevance judgments."""
import importlib.util
import json
from pathlib import Path

import pytest

from legal_research.corpus import Corpus, excerpt

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('import_demo_corpus', ROOT / 'scripts/import_demo_corpus.py')
importer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(importer)


@pytest.fixture
def corpus(tmp_path):
    payload = {'schema_version': 1, 'collection': {'id': 'synthetic-test'}, 'cases': [
        {'id': 'a', 'case_name': 'Synthetic vehicle opinion', 'court': 'scotus', 'decision_date': '2001-01-01', 'source_url': 'https://example.org/a.pdf', 'summary': 'Vehicle citation comparison.', 'pages': [{'pdf_page': 3, 'text': 'An arrest and a traffic citation are different. The car was locked.'}]},
        {'id': 'b', 'case_name': 'Synthetic passenger opinion', 'court': 'scotus', 'decision_date': '2010-01-01', 'source_url': 'https://example.org/b.pdf', 'summary': 'Passenger purse comparison.', 'pages': [{'pdf_page': 4, 'text': 'The passenger purse could hold the object sought during the search.'}]},
        {'id': 'c', 'case_name': 'Different court', 'court': 'ca1', 'decision_date': '2001-01-01', 'source_url': 'https://example.org/c.pdf', 'summary': 'Arrest.', 'pages': [{'pdf_page': 1, 'text': 'An arrest and a traffic citation.'}]},
    ]}
    path = tmp_path/'index.json'
    path.write_text(json.dumps(payload))
    return Corpus(path)


def test_search_filters_and_exclusion(corpus):
    results = corpus.search('arrest citation', 'scotus', '2000-01-01', '2009-12-31')
    assert [x['id'] for x in results] == ['a']
    assert corpus.search('arrest citation', 'scotus', '2000-01-01', '2009-12-31', ['a']) == []
    assert corpus.search('passenger', 'scotus', '2000-01-01', '2009-12-31') == []


def test_passages_are_source_slices_and_have_page_links(corpus):
    result = corpus.search('passenger purse', 'scotus', '1980-01-01', '2020-12-31')[0]
    passage = result['passages'][0]
    assert passage['text'] in corpus.get_case(result['id'])['pages'][0]['text']
    assert passage['source_url'].endswith('#page=4')
    assert passage['opinion_scope'] == 'unsegmented_pdf_page'
    assert result['summary_kind'] == 'editorial_seed_summary_not_generated_analysis'
    assert result['treatment_status'] == 'not_checked'


def test_feedback_query_terms_can_change_ranking(corpus):
    before = corpus.search('arrest citation', 'scotus', '1980-01-01', '2020-12-31')
    after = corpus.search('passenger purse', 'scotus', '1980-01-01', '2020-12-31')
    assert before[0]['id'] != after[0]['id']


def test_no_text_match_does_not_return_editorial_summary(corpus):
    assert corpus.search('comparison', 'scotus', '1980-01-01', '2020-12-31') == []


def test_missing_corrupt_and_duplicate_corpora(tmp_path):
    path = tmp_path / 'index.json'
    assert Corpus(path).status()['ready'] is False
    path.write_text('{')
    assert Corpus(path).error == 'invalid_corpus_index'
    path.write_text(json.dumps({'schema_version': 1, 'cases': [{'id': 'a'}]}))
    assert Corpus(path).count == 0


def test_excerpts_preserve_broken_words():
    text = ('intro ' * 40) + 'The automo-\nbile was searched. ' + ('ending ' * 200)
    quote = excerpt(text, ['searched'], max_chars=300)
    assert quote in text
    assert 'automo-\nbile' in quote


def test_invalid_limits_dates_and_empty_query(corpus):
    with pytest.raises(ValueError): corpus.search('car', 'scotus', '2020-01-01', '2000-01-01')
    with pytest.raises(ValueError): corpus.search('car', 'scotus', '2000-01-01', '2020-01-01', limit=100)
    assert corpus.search('the and', 'scotus', '2000-01-01', '2020-01-01') == []


@pytest.mark.parametrize('url', ['http://www.govinfo.gov/content/pkg/USREPORTS-525/a.pdf','https://evil.test/a.pdf','https://www.govinfo.gov@evil.test/a.pdf','https://www.govinfo.gov/other/a.pdf','https://tile.loc.gov/storage-services/service/ll/usrep/a.pdf?token=secret'])
def test_importer_rejects_unapproved_urls(url):
    with pytest.raises(importer.ImportFailure): importer.allowed_url(url)


def test_importer_accepts_only_expected_paths():
    url='https://www.govinfo.gov/content/pkg/USREPORTS-525/pdf/USREPORTS-525-113.pdf'
    assert importer.allowed_url(url) == url
