"""The demo launcher serves only built assets, with the existing API guards."""
import pytest
from fastapi.testclient import TestClient
from legal_research.main import create_app


@pytest.mark.parametrize('port', [5173, 5174])
def test_single_origin_ui_api_and_filesystem_boundary(tmp_path, port):
    assets=tmp_path/'dist';assets.mkdir()
    (assets/'index.html').write_text('<html><body>Casework test UI</body></html>')
    (assets/'app.js').write_text('/* synthetic asset */')
    (tmp_path/'.env').write_text('SYNTHETIC_PRIVATE_SENTINEL')
    with TestClient(create_app(tmp_path/'state',ui_dir=assets),base_url=f'http://127.0.0.1:{port}') as client:
        assert 'Casework test UI' in client.get('/').text
        assert client.get('/app.js').status_code==200
        assert client.get('/api/health').json()['stage']=='local_workspace'
        bootstrap=client.get('/api/bootstrap').json()
        result=client.post('/api/matters',json={'title':'Single origin','question':'Synthetic question'},headers={
            'Origin':f'http://127.0.0.1:{port}','X-Workspace-Token':bootstrap['csrf_token']})
        assert result.status_code==201
        for path in ['/.env','/data/workspace.sqlite3','/%2e%2e/.env']:
            response=client.get(path)
            assert response.status_code==404
            assert 'SYNTHETIC_PRIVATE_SENTINEL' not in response.text
        assert client.get('/api/bootstrap',headers={'Origin':'https://evil.example'}).status_code==403
