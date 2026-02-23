"""
Merlai API クライアント使用例

APIサーバーを使用した作曲支援の実践的な例
"""

import base64
import json
import time
import httpx


def example_1_basic_generation():
    """例1: 基本的な音楽生成"""
    print("=" * 60)
    print("例1: APIを使った基本的な音楽生成")
    print("=" * 60)
    print()
    
    # APIエンドポイント
    api_url = "http://localhost:8000/api/v1/generate"
    
    # リクエストデータ
    request_data = {
        "melody": [
            {"pitch": 60, "velocity": 80, "duration": 1.0, "start_time": 0.0},
            {"pitch": 64, "velocity": 80, "duration": 1.0, "start_time": 1.0},
            {"pitch": 67, "velocity": 80, "duration": 1.0, "start_time": 2.0},
            {"pitch": 72, "velocity": 80, "duration": 1.0, "start_time": 3.0},
        ],
        "style": "pop",
        "tempo": 120,
        "key": "C",
        "generate_harmony": True,
        "generate_bass": True,
        "generate_drums": True,
    }
    
    print("リクエスト:")
    print(f"  メロディ: {len(request_data['melody'])}ノート")
    print(f"  スタイル: {request_data['style']}")
    print(f"  テンポ: {request_data['tempo']} BPM")
    print()
    
    try:
        # APIリクエストを送信
        print("APIリクエストを送信中...")
        response = httpx.post(api_url, json=request_data, timeout=30.0)
        
        if response.status_code == 200:
            data = response.json()
            
            print("✅ 生成成功！")
            print()
            print("生成された内容:")
            print(f"  ハーモニー: {len(data.get('harmony', []))}コード")
            print(f"  ベースライン: {len(data.get('bass_line', []))}ノート")
            print(f"  ドラム: {len(data.get('drums', []))}ノート")
            print(f"  曲の長さ: {data.get('duration', 0)}秒")
            print()
            
            # MIDIデータを保存
            if data.get("midi_data"):
                midi_bytes = base64.b64decode(data["midi_data"])
                output_path = "examples/output/api_generated.mid"
                
                with open(output_path, "wb") as f:
                    f.write(midi_bytes)
                
                print(f"📁 MIDIファイルを保存: {output_path}")
                print(f"   サイズ: {len(midi_bytes)} bytes")
            
        else:
            print(f"❌ エラー: HTTP {response.status_code}")
            print(response.text)
    
    except httpx.ConnectError:
        print("❌ APIサーバーに接続できません")
        print("   サーバーを起動してください: python3 -m merlai.api.main")
    except Exception as e:
        print(f"❌ エラー: {e}")
    
    print()


def example_2_style_comparison():
    """例2: 複数のスタイルで比較"""
    print("=" * 60)
    print("例2: 同じメロディで複数のスタイルを比較")
    print("=" * 60)
    print()
    
    # 同じメロディで異なるスタイルを試す
    melody = [
        {"pitch": 60, "velocity": 80, "duration": 1.0, "start_time": 0.0},
        {"pitch": 62, "velocity": 80, "duration": 1.0, "start_time": 1.0},
        {"pitch": 64, "velocity": 80, "duration": 1.0, "start_time": 2.0},
    ]
    
    styles = ["pop", "jazz", "rock", "electronic", "classical"]
    api_url = "http://localhost:8000/api/v1/generate"
    
    print("同じメロディで5つのスタイルを試します...")
    print()
    
    try:
        for style in styles:
            request_data = {
                "melody": melody,
                "style": style,
                "tempo": 120,
                "key": "C",
                "generate_harmony": True,
                "generate_bass": False,
                "generate_drums": False,
            }
            
            response = httpx.post(api_url, json=request_data, timeout=30.0)
            
            if response.status_code == 200:
                data = response.json()
                harmony_count = len(data.get('harmony', []))
                
                print(f"  {style.ljust(12)}: {harmony_count}コード生成")
            else:
                print(f"  {style.ljust(12)}: エラー")
        
        print()
        print("✅ スタイル比較完了")
        
    except httpx.ConnectError:
        print("❌ APIサーバーに接続できません")
    
    print()


def example_3_health_check():
    """例3: APIサーバーの状態確認"""
    print("=" * 60)
    print("例3: APIサーバーの状態確認")
    print("=" * 60)
    print()
    
    try:
        # ヘルスチェック
        response = httpx.get("http://localhost:8000/health", timeout=5.0)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ APIサーバーは正常に稼働しています")
            print()
            print("サーバー情報:")
            print(f"  ステータス: {data.get('status')}")
            print(f"  モデル読み込み: {data.get('model_loaded')}")
            print(f"  プラグイン数: {data.get('plugins_loaded')}")
        else:
            print(f"⚠️ サーバーステータス: HTTP {response.status_code}")
        
    except httpx.ConnectError:
        print("❌ APIサーバーが起動していません")
        print()
        print("サーバーを起動してください:")
        print("  cd /workspace")
        print("  python3 -m merlai.api.main")
    
    print()


def main():
    """すべての例を実行"""
    print()
    print("🎵" * 30)
    print("   Merlai API クライアント使用例")
    print("🎵" * 30)
    print()
    
    # まずヘルスチェック
    example_3_health_check()
    
    # サーバーが起動している場合のみ、他の例を実行
    try:
        response = httpx.get("http://localhost:8000/health", timeout=2.0)
        if response.status_code == 200:
            input("Enterキーを押して例1を実行... ")
            example_1_basic_generation()
            
            input("Enterキーを押して例2を実行... ")
            example_2_style_comparison()
            
            print("=" * 60)
            print("✅ すべての例が完了しました！")
            print("=" * 60)
        else:
            print("⚠️ APIサーバーは起動していますが、正常に応答していません")
    
    except httpx.ConnectError:
        print("📝 注意: 他の例を実行するには、まずAPIサーバーを起動してください")
        print()
        print("別のターミナルで:")
        print("  cd /workspace")
        print("  python3 -m merlai.api.main")
        print()
    
    except KeyboardInterrupt:
        print("\n\n👋 終了します")


if __name__ == "__main__":
    main()
