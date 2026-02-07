"""
エンドツーエンド動作確認テスト（実際のAPIサーバーを使用）

このテストは実際にAPIサーバーを起動して、
完全な動作確認を行います。
"""

import base64
import json
import os
import subprocess
import tempfile
import time
from typing import Generator

import httpx
import pytest


@pytest.fixture(scope="module")
def api_server() -> Generator[str, None, None]:
    """APIサーバーを起動するフィクスチャ"""
    # サーバーを起動
    env = os.environ.copy()
    env["PATH"] = f"/home/ubuntu/.local/bin:{env.get('PATH', '')}"
    
    process = subprocess.Popen(
        ["python3", "-m", "merlai.api.main"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )
    
    # サーバーが起動するまで待機
    base_url = "http://localhost:8000"
    max_retries = 30
    for i in range(max_retries):
        try:
            response = httpx.get(f"{base_url}/health", timeout=2.0)
            if response.status_code == 200:
                print(f"✅ APIサーバーが起動しました (試行回数: {i+1})")
                break
        except (httpx.ConnectError, httpx.ReadTimeout):
            if i < max_retries - 1:
                time.sleep(1)
            else:
                process.terminate()
                raise RuntimeError("APIサーバーの起動に失敗しました")
    
    yield base_url
    
    # サーバーを停止
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()


class TestE2EAPIServer:
    """実際のAPIサーバーを使用したエンドツーエンドテスト"""
    
    def test_server_health_check(self, api_server: str) -> None:
        """ヘルスチェックエンドポイントのテスト"""
        response = httpx.get(f"{api_server}/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        print(f"✅ ヘルスチェック成功: {data}")
    
    def test_server_ready_check(self, api_server: str) -> None:
        """レディネスチェックエンドポイントのテスト"""
        response = httpx.get(f"{api_server}/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        print(f"✅ レディネスチェック成功: {data}")
    
    def test_root_endpoint(self, api_server: str) -> None:
        """ルートエンドポイントのテスト"""
        response = httpx.get(api_server)
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        print(f"✅ ルートエンドポイント成功: {data}")
    
    def test_api_health_endpoint(self, api_server: str) -> None:
        """APIヘルスチェックエンドポイントのテスト"""
        response = httpx.get(f"{api_server}/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print(f"✅ APIヘルスチェック成功: {data}")
    
    def test_complete_music_generation_workflow(self, api_server: str) -> None:
        """完全な音楽生成ワークフローのテスト"""
        # 1. メロディを定義
        request_data = {
            "melody": [
                {"pitch": 60, "velocity": 80, "duration": 1.0, "start_time": 0.0},
                {"pitch": 62, "velocity": 80, "duration": 1.0, "start_time": 1.0},
                {"pitch": 64, "velocity": 80, "duration": 1.0, "start_time": 2.0},
                {"pitch": 65, "velocity": 80, "duration": 1.0, "start_time": 3.0},
            ],
            "style": "pop",
            "tempo": 120,
            "key": "C",
            "generate_harmony": True,
            "generate_bass": True,
            "generate_drums": True,
        }
        
        # 2. 音楽生成をリクエスト
        response = httpx.post(
            f"{api_server}/api/v1/generate",
            json=request_data,
            timeout=30.0,
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # 3. レスポンスの検証
        assert data["success"] is True
        assert "midi_data" in data
        assert data["midi_data"] is not None
        
        # MIDIデータのデコード
        midi_bytes = base64.b64decode(data["midi_data"])
        assert len(midi_bytes) > 0
        
        # 4. MIDIファイルとして保存して検証
        with tempfile.NamedTemporaryFile(suffix=".mid", delete=False) as tmp_file:
            tmp_file.write(midi_bytes)
            midi_path = tmp_file.name
        
        try:
            # ファイルが存在し、サイズがあることを確認
            assert os.path.exists(midi_path)
            assert os.path.getsize(midi_path) > 0
            
            print(f"✅ 音楽生成成功:")
            print(f"   - ハーモニー: {len(data.get('harmony', [])) if data.get('harmony') else 0} コード")
            print(f"   - ベースライン: {len(data.get('bass_line', [])) if data.get('bass_line') else 0} ノート")
            print(f"   - ドラム: {len(data.get('drums', [])) if data.get('drums') else 0} ノート")
            print(f"   - MIDI サイズ: {len(midi_bytes)} bytes")
            print(f"   - 曲の長さ: {data.get('duration', 0):.2f} 秒")
            print(f"   - MIDIファイル: {midi_path}")
        finally:
            # クリーンアップ
            if os.path.exists(midi_path):
                os.unlink(midi_path)
    
    def test_plugin_list_endpoint(self, api_server: str) -> None:
        """プラグインリストエンドポイントのテスト"""
        response = httpx.get(f"{api_server}/api/v1/plugins")
        assert response.status_code == 200
        data = response.json()
        assert "plugins" in data
        assert "count" in data
        print(f"✅ プラグインリスト取得成功: {data['count']} プラグイン")
    
    def test_config_endpoints(self, api_server: str) -> None:
        """設定エンドポイントのテスト"""
        # 設定取得
        response = httpx.get(f"{api_server}/api/v1/config")
        assert response.status_code == 200
        config = response.json()
        assert "temperature" in config
        print(f"✅ 設定取得成功: {config}")
        
        # 設定更新
        update_data = {"temperature": 0.9}
        response = httpx.post(
            f"{api_server}/api/v1/config",
            json=update_data,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Configuration updated successfully"
        print(f"✅ 設定更新成功: {data}")
    
    def test_error_handling_empty_melody(self, api_server: str) -> None:
        """エラーハンドリング: 空のメロディ"""
        request_data = {
            "melody": [],
            "style": "pop",
            "tempo": 120,
            "key": "C",
        }
        
        response = httpx.post(
            f"{api_server}/api/v1/generate",
            json=request_data,
        )
        
        # 空のメロディは422エラーを返すべき
        assert response.status_code == 422
        print(f"✅ 空のメロディエラーハンドリング成功")
    
    def test_multiple_concurrent_requests(self, api_server: str) -> None:
        """複数の同時リクエストのテスト"""
        import asyncio
        
        async def make_request(client: httpx.AsyncClient, i: int) -> dict:
            """非同期リクエストを作成"""
            request_data = {
                "melody": [
                    {"pitch": 60 + i, "velocity": 80, "duration": 1.0, "start_time": 0.0},
                ],
                "style": "pop",
                "tempo": 120,
                "key": "C",
            }
            response = await client.post(
                f"{api_server}/api/v1/generate",
                json=request_data,
                timeout=30.0,
            )
            return response.json()
        
        async def run_concurrent_requests() -> list:
            """複数のリクエストを同時実行"""
            async with httpx.AsyncClient() as client:
                tasks = [make_request(client, i) for i in range(5)]
                return await asyncio.gather(*tasks)
        
        # 5つの同時リクエストを実行
        results = asyncio.run(run_concurrent_requests())
        
        # すべて成功したことを確認
        assert len(results) == 5
        for result in results:
            assert result["success"] is True
        
        print(f"✅ 同時リクエストテスト成功: {len(results)} 件のリクエストを処理")


class TestE2EPerformance:
    """パフォーマンステスト"""
    
    def test_response_time_health_check(self, api_server: str) -> None:
        """ヘルスチェックのレスポンスタイム"""
        start_time = time.time()
        response = httpx.get(f"{api_server}/health")
        end_time = time.time()
        
        assert response.status_code == 200
        response_time = (end_time - start_time) * 1000  # ミリ秒
        
        print(f"✅ ヘルスチェックレスポンスタイム: {response_time:.2f}ms")
        
        # レスポンスタイムは100ms以下であるべき
        assert response_time < 100, f"レスポンスタイムが遅すぎます: {response_time:.2f}ms"
    
    def test_response_time_music_generation(self, api_server: str) -> None:
        """音楽生成のレスポンスタイム"""
        request_data = {
            "melody": [
                {"pitch": 60, "velocity": 80, "duration": 1.0, "start_time": 0.0},
                {"pitch": 62, "velocity": 80, "duration": 1.0, "start_time": 1.0},
            ],
            "style": "pop",
            "tempo": 120,
            "key": "C",
        }
        
        start_time = time.time()
        response = httpx.post(
            f"{api_server}/api/v1/generate",
            json=request_data,
            timeout=30.0,
        )
        end_time = time.time()
        
        assert response.status_code == 200
        response_time = (end_time - start_time) * 1000  # ミリ秒
        
        print(f"✅ 音楽生成レスポンスタイム: {response_time:.2f}ms")
        
        # レスポンスタイムは10秒以下であるべき
        assert response_time < 10000, f"レスポンスタイムが遅すぎます: {response_time:.2f}ms"


if __name__ == "__main__":
    # 直接実行する場合
    pytest.main([__file__, "-v", "-s"])
