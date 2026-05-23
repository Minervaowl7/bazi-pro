#!/usr/bin/env python3
import importlib
import os

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client_no_key():
    import server.app as app_module
    return TestClient(app_module.app)


@pytest.fixture
def client_with_key():
    import server.app as app_module
    original = os.environ.get('BAZI_API_KEY', '')
    os.environ['BAZI_API_KEY'] = 'test-contract-key'
    importlib.reload(app_module)
    try:
        yield TestClient(app_module.app)
    finally:
        os.environ['BAZI_API_KEY'] = original
        importlib.reload(app_module)


class TestFrontendAuthContract:

    def test_index_page_contains_api_key_input(self, client_no_key):
        resp = client_no_key.get('/')
        assert resp.status_code == 200
        assert 'apiKeyInput' in resp.text

    def test_index_page_contains_auth_headers_function(self, client_no_key):
        resp = client_no_key.get('/')
        assert resp.status_code == 200
        assert 'authHeaders' in resp.text
        assert 'X-API-Key' in resp.text

    def test_index_page_contains_get_api_key_function(self, client_no_key):
        resp = client_no_key.get('/')
        assert resp.status_code == 200
        assert 'getApiKey' in resp.text

    def test_index_page_websocket_uses_headers_not_query(self, client_no_key):
        resp = client_no_key.get('/')
        assert resp.status_code == 200
        html = resp.text
        assert 'x-api-key' in html or 'X-API-Key' in html
        ws_lines = [ln for ln in html.split('\n') if 'WebSocket' in ln or 'ws://' in ln or 'wss://' in ln]
        for line in ws_lines:
            assert 'api_key=' not in line, "WebSocket URL should not contain api_key query param"

    def test_index_page_fetch_calls_include_auth(self, client_no_key):
        resp = client_no_key.get('/')
        html = resp.text
        assert "headers: authHeaders()" in html or "headers:authHeaders()" in html.replace(' ', '')


class TestAPIKeyEnforcement:

    def test_no_key_when_not_configured(self, client_no_key):
        resp = client_no_key.post('/api/analyze', json={
            '性别': '女', '八字': '壬午 乙巳 丁亥 癸卯', '日主': '丁',
        })
        assert resp.status_code == 200

    def test_missing_key_when_configured(self, client_with_key):
        resp = client_with_key.post('/api/analyze', json={
            '性别': '女', '八字': '壬午 乙巳 丁亥 癸卯', '日主': '丁',
        })
        assert resp.status_code == 401

    def test_wrong_key_when_configured(self, client_with_key):
        resp = client_with_key.post('/api/analyze', json={
            '性别': '女', '八字': '壬午 乙巳 丁亥 癸卯', '日主': '丁',
        }, headers={'X-API-Key': 'wrong'})
        assert resp.status_code == 401

    def test_correct_key_when_configured(self, client_with_key):
        resp = client_with_key.post('/api/analyze', json={
            '性别': '女', '八字': '壬午 乙巳 丁亥 癸卯', '日主': '丁',
        }, headers={'X-API-Key': 'test-contract-key'})
        assert resp.status_code == 200

    def test_status_endpoint_requires_key(self, client_with_key):
        run_id = 'test-status-auth'
        import server.app as app_module
        app_module._task_store.create(run_id, {
            'status': 'running', '_created_ts': 0, 'visible': True,
        })
        try:
            resp = client_with_key.get(f'/api/status/{run_id}')
            assert resp.status_code == 401
            resp = client_with_key.get(f'/api/status/{run_id}', headers={
                'X-API-Key': 'test-contract-key',
            })
            assert resp.status_code == 200
        finally:
            app_module._task_store.delete(run_id)

    def test_result_endpoint_requires_key(self, client_with_key):
        run_id = 'test-result-auth'
        import server.app as app_module
        app_module._task_store.create(run_id, {
            'status': 'completed', '_created_ts': 0,
        })
        try:
            resp = client_with_key.get(f'/api/result/{run_id}')
            assert resp.status_code == 401
            resp = client_with_key.get(f'/api/result/{run_id}', headers={
                'X-API-Key': 'test-contract-key',
            })
            assert resp.status_code == 200
        finally:
            app_module._task_store.delete(run_id)

    def test_websocket_rejects_without_key(self, client_with_key):
        with client_with_key.websocket_connect('/ws/test-ws-no-key') as ws:
            msg = ws.receive()
            assert msg['type'] == 'websocket.close'
            assert msg['code'] == 4001

    def test_websocket_accepts_with_header_key(self, client_with_key):
        import server.app as app_module
        run_id = 'test-ws-header-key'
        app_module._task_store.create(run_id, {
            'status': 'running', '_created_ts': 0,
        })
        try:
            with client_with_key.websocket_connect(
                f'/ws/{run_id}',
                headers={'x-api-key': 'test-contract-key'},
            ) as ws:
                ws.send_text('ping')
        except Exception as e:
            if 'close' in str(e).lower() or '4001' in str(e):
                pytest.fail("WebSocket should not close with valid API key header")
        finally:
            app_module._task_store.delete(run_id)


class TestErrorFormatContract:

    def test_auth_error_has_structured_format(self, client_with_key):
        resp = client_with_key.post('/api/analyze', json={
            '性别': '女', '八字': '壬午 乙巳 丁亥 癸卯', '日主': '丁',
        })
        assert resp.status_code == 401
        data = resp.json()
        assert 'error' in data
        assert 'code' in data['error']
        assert 'message' in data['error']
        assert data['error']['code'] == 'UNAUTHORIZED'

    def test_auth_error_no_stack_trace(self, client_with_key):
        resp = client_with_key.post('/api/analyze', json={
            '性别': '女', '八字': '壬午 乙巳 丁亥 癸卯', '日主': '丁',
        })
        data = resp.json()
        body_str = str(data)
        assert 'traceback' not in body_str.lower()
        assert 'exception' not in body_str.lower()
