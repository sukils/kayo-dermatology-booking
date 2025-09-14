#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
予約管理アプリ - HTTPS対応版
PWAのインストール条件を満たすためHTTPSで起動
"""

import ssl
from app import app

if __name__ == '__main__':
    # 自己署名証明書を作成（初回のみ）
    try:
        # 既存の証明書ファイルをチェック
        import os
        if not os.path.exists('cert.pem') or not os.path.exists('key.pem'):
            print("自己署名証明書を生成中...")
            from cryptography import x509
            from cryptography.x509.oid import NameOID
            from cryptography.hazmat.primitives import hashes
            from cryptography.hazmat.primitives.asymmetric import rsa
            from cryptography.hazmat.primitives import serialization
            import datetime
            
            # 秘密鍵を生成
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
            )
            
            # 証明書の情報を設定
            subject = issuer = x509.Name([
                x509.NameAttribute(NameOID.COUNTRY_NAME, "JP"),
                x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Tokyo"),
                x509.NameAttribute(NameOID.LOCALITY_NAME, "Tokyo"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Kayo Dermatology"),
                x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
            ])
            
            # 証明書を生成
            cert = x509.CertificateBuilder().subject_name(
                subject
            ).issuer_name(
                issuer
            ).public_key(
                private_key.public_key()
            ).serial_number(
                x509.random_serial_number()
            ).not_valid_before(
                datetime.datetime.utcnow()
            ).not_valid_after(
                datetime.datetime.utcnow() + datetime.timedelta(days=365)
            ).add_extension(
                x509.SubjectAlternativeName([
                    x509.DNSName("localhost"),
                    x509.IPAddress("127.0.0.1"),
                    x509.IPAddress("192.168.1.9"),
                ]),
                critical=False,
            ).sign(private_key, hashes.SHA256())
            
            # ファイルに保存
            with open("key.pem", "wb") as f:
                f.write(private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                ))
            
            with open("cert.pem", "wb") as f:
                f.write(cert.public_bytes(serialization.Encoding.PEM))
            
            print("証明書の生成が完了しました")
        
        # HTTPSで起動
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain('cert.pem', 'key.pem')
        
        print("HTTPSでアプリを起動中...")
        print("スマホで以下のURLにアクセスしてください:")
        print("https://192.168.1.9:5000")
        print("(証明書の警告が出たら「詳細設定」→「続行」を選択)")
        
        app.run(debug=True, host='0.0.0.0', port=5000, ssl_context=context)
        
    except ImportError:
        print("cryptographyライブラリがインストールされていません")
        print("以下のコマンドでインストールしてください:")
        print("pip install cryptography")
        
    except Exception as e:
        print(f"HTTPS起動エラー: {e}")
        print("HTTPで起動します...")
        app.run(debug=True, host='0.0.0.0', port=5000)
