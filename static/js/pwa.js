// PWA（Progressive Web App）機能
// アプリのインストール、プッシュ通知、オフライン対応を管理

class PWAManager {
  constructor() {
    this.isOnline = navigator.onLine;
    this.deferredPrompt = null;
    this.serviceWorker = null;
    this.pushSubscription = null;
    
    this.init();
  }
  
  async init() {
    console.log('PWA Manager: 初期化中...');
    
    // オンライン状態の監視
    this.setupOnlineStatusListener();
    
    // サービスワーカーの登録
    await this.registerServiceWorker();
    
    // アプリインストールの監視
    this.setupInstallPrompt();
    
    // プッシュ通知の設定
    await this.setupPushNotifications();
    
    // バックグラウンド同期の設定
    this.setupBackgroundSync();
    
    // インストール状態をチェック
    this.checkInstallStatus();
    
    console.log('PWA Manager: 初期化完了');
  }
  
  // オンライン状態の監視
  setupOnlineStatusListener() {
    window.addEventListener('online', () => {
      console.log('PWA Manager: オンラインになりました');
      this.isOnline = true;
      this.showNotification('オンラインに接続しました', 'success');
      this.syncPendingData();
    });
    
    window.addEventListener('offline', () => {
      console.log('PWA Manager: オフラインになりました');
      this.isOnline = false;
      this.showNotification('オフラインです。データは同期待ちになります', 'warning');
    });
  }
  
  // サービスワーカーの登録
  async registerServiceWorker() {
    if ('serviceWorker' in navigator) {
      try {
        this.serviceWorker = await navigator.serviceWorker.register('/static/js/service-worker.js');
        console.log('Service Worker 登録成功:', this.serviceWorker);
        
        // 更新の監視
        this.serviceWorker.addEventListener('updatefound', () => {
          console.log('Service Worker 更新が見つかりました');
          this.showUpdateNotification();
        });
        
      } catch (error) {
        console.error('Service Worker 登録エラー:', error);
      }
    } else {
      console.log('Service Worker はサポートされていません');
    }
  }
  
  // アプリインストールプロンプトの設定
  setupInstallPrompt() {
    // 既にインストールされているかチェック
    if (this.isAppInstalled()) {
      console.log('PWA Manager: アプリは既にインストールされています');
      this.hideInstallButton();
      return;
    }
    
    window.addEventListener('beforeinstallprompt', (e) => {
      console.log('PWA Manager: インストールプロンプトが利用可能');
      e.preventDefault();
      this.deferredPrompt = e;
      this.showInstallButton();
    });
    
    // インストール完了の監視
    window.addEventListener('appinstalled', () => {
      console.log('PWA Manager: アプリがインストールされました');
      this.hideInstallButton();
      this.hideManualInstallGuide();
      this.showNotification('アプリがインストールされました！', 'success');
      
      // インストール状態を保存
      localStorage.setItem('pwa_installed', 'true');
    });
    
    // 手動でインストールボタンを表示（HTTPでも動作するように）
    setTimeout(() => {
      if (!this.isAppInstalled()) {
        console.log('PWA Manager: インストールボタンを表示');
        this.showInstallButton();
        
        // 手動インストール案内も表示
        this.showManualInstallGuide();
      }
    }, 2000);
  }
  
  // インストールボタンの表示
  showInstallButton() {
    const installButton = document.getElementById('install-button');
    if (installButton) {
      installButton.style.display = 'block';
      installButton.addEventListener('click', () => this.installApp());
      
      // ボタンが表示されたことを通知
      console.log('PWA Manager: インストールボタンを表示しました');
      this.showNotification('アプリをインストールできます', 'info');
    } else {
      console.error('PWA Manager: インストールボタンが見つかりません');
    }
  }
  
  // インストールボタンの非表示
  hideInstallButton() {
    const installButton = document.getElementById('install-button');
    if (installButton) {
      installButton.style.display = 'none';
    }
  }
  
  // 手動インストール案内の表示
  showManualInstallGuide() {
    const guide = document.getElementById('manual-install-guide');
    if (guide) {
      guide.style.display = 'block';
      console.log('PWA Manager: 手動インストール案内を表示');
    }
  }
  
  // 手動インストール案内の非表示
  hideManualInstallGuide() {
    const guide = document.getElementById('manual-install-guide');
    if (guide) {
      guide.style.display = 'none';
      console.log('PWA Manager: 手動インストール案内を非表示');
    }
  }
  
  // アプリがインストールされているかチェック
  isAppInstalled() {
    // スタンドアロンモードで表示されているかチェック
    if (window.matchMedia('(display-mode: standalone)').matches) {
      return true;
    }
    
    // フルスクリーンモードで表示されているかチェック
    if (window.navigator.standalone === true) {
      return true;
    }
    
    // localStorageでインストール状態をチェック
    if (localStorage.getItem('pwa_installed') === 'true') {
      return true;
    }
    
    return false;
  }
  
  // インストール状態をチェックしてUIを更新
  checkInstallStatus() {
    if (this.isAppInstalled()) {
      console.log('PWA Manager: アプリは既にインストールされています');
      this.hideInstallButton();
      this.hideManualInstallGuide();
      
      // インストール済みの通知を表示
      this.showNotification('アプリがインストール済みです', 'success');
    } else {
      console.log('PWA Manager: アプリはインストールされていません');
    }
  }
  
  // アプリのインストール
  async installApp() {
    if (this.deferredPrompt) {
      this.deferredPrompt.prompt();
      const { outcome } = await this.deferredPrompt.userChoice;
      console.log('インストール結果:', outcome);
      
      if (outcome === 'accepted') {
        // インストールが受け入れられた場合
        this.hideInstallButton();
        this.hideManualInstallGuide();
        this.showNotification('アプリのインストールを開始しました', 'success');
        localStorage.setItem('pwa_installed', 'true');
      }
      
      this.deferredPrompt = null;
    } else {
      // 手動インストール案内を表示
      this.showManualInstallGuide();
      this.showNotification('手動でインストールしてください', 'info');
    }
  }
  
  // プッシュ通知の設定
  async setupPushNotifications() {
    if ('Notification' in window && 'serviceWorker' in navigator) {
      // 通知許可のリクエスト
      const permission = await Notification.requestPermission();
      
      if (permission === 'granted') {
        console.log('PWA Manager: プッシュ通知が許可されました');
        await this.subscribeToPush();
      } else {
        console.log('PWA Manager: プッシュ通知が拒否されました');
      }
    }
  }
  
  // プッシュ通知の購読
  async subscribeToPush() {
    try {
      const registration = await navigator.serviceWorker.ready;
      this.pushSubscription = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: this.urlBase64ToUint8Array('YOUR_VAPID_PUBLIC_KEY')
      });
      
      console.log('プッシュ通知購読成功:', this.pushSubscription);
      
      // サーバーに購読情報を送信
      await this.sendSubscriptionToServer(this.pushSubscription);
      
    } catch (error) {
      console.error('プッシュ通知購読エラー:', error);
    }
  }
  
  // サーバーに購読情報を送信
  async sendSubscriptionToServer(subscription) {
    try {
      const response = await fetch('/api/push-subscription', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(subscription)
      });
      
      if (response.ok) {
        console.log('プッシュ通知購読情報をサーバーに送信しました');
      }
    } catch (error) {
      console.error('プッシュ通知購読情報送信エラー:', error);
    }
  }
  
  // バックグラウンド同期の設定
  setupBackgroundSync() {
    if ('serviceWorker' in navigator && 'sync' in window.ServiceWorkerRegistration.prototype) {
      console.log('PWA Manager: バックグラウンド同期が利用可能');
    }
  }
  
  // データの同期
  async syncPendingData() {
    if (this.serviceWorker) {
      try {
        // サービスワーカーに同期を指示
        this.serviceWorker.postMessage({ type: 'SYNC_BOOKINGS' });
        console.log('PWA Manager: データ同期を開始しました');
      } catch (error) {
        console.error('データ同期エラー:', error);
      }
    }
  }
  
  // 通知の表示
  showNotification(message, type = 'info') {
    // ブラウザの通知APIを使用
    if ('Notification' in window && Notification.permission === 'granted') {
      const notification = new Notification('かよ皮膚科予約管理', {
        body: message,
        icon: '/static/icons/icon-192x192.png',
        tag: 'booking-notification'
      });
      
      notification.onclick = () => {
        window.focus();
        notification.close();
      };
    }
    
    // アプリ内通知も表示
    this.showInAppNotification(message, type);
  }
  
  // アプリ内通知の表示
  showInAppNotification(message, type) {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    
    // スタイルを適用
    Object.assign(notification.style, {
      position: 'fixed',
      top: '20px',
      right: '20px',
      padding: '15px 20px',
      borderRadius: '5px',
      color: 'white',
      fontWeight: 'bold',
      zIndex: '10000',
      maxWidth: '300px',
      boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)'
    });
    
    // タイプに応じて色を設定
    const colors = {
      success: '#4CAF50',
      warning: '#FF9800',
      error: '#F44336',
      info: '#2196F3'
    };
    notification.style.backgroundColor = colors[type] || colors.info;
    
    document.body.appendChild(notification);
    
    // 3秒後に自動削除
    setTimeout(() => {
      if (notification.parentNode) {
        notification.parentNode.removeChild(notification);
      }
    }, 3000);
  }
  
  // 更新通知の表示
  showUpdateNotification() {
    const updateButton = document.createElement('button');
    updateButton.textContent = 'アプリを更新';
    updateButton.className = 'update-button';
    updateButton.style.cssText = `
      position: fixed;
      bottom: 20px;
      right: 20px;
      padding: 10px 20px;
      background-color: #4CAF50;
      color: white;
      border: none;
      border-radius: 5px;
      cursor: pointer;
      z-index: 10000;
      font-weight: bold;
    `;
    
    updateButton.addEventListener('click', () => {
      if (this.serviceWorker && this.serviceWorker.waiting) {
        this.serviceWorker.waiting.postMessage({ type: 'SKIP_WAITING' });
        window.location.reload();
      }
    });
    
    document.body.appendChild(updateButton);
  }
  
  // VAPIDキーの変換（実際のキーに置き換える必要があります）
  urlBase64ToUint8Array(base64String) {
    const padding = '='.repeat((4 - base64String.length % 4) % 4);
    const base64 = (base64String + padding)
      .replace(/-/g, '+')
      .replace(/_/g, '/');
    
    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);
    
    for (let i = 0; i < rawData.length; ++i) {
      outputArray[i] = rawData.charCodeAt(i);
    }
    return outputArray;
  }
  
  // オフライン時のデータ保存
  saveOfflineData(key, data) {
    try {
      localStorage.setItem(`offline_${key}`, JSON.stringify(data));
      console.log(`オフライン データを保存しました: ${key}`);
    } catch (error) {
      console.error('オフライン データ保存エラー:', error);
    }
  }
  
  // オフライン時のデータ取得
  getOfflineData(key) {
    try {
      const data = localStorage.getItem(`offline_${key}`);
      return data ? JSON.parse(data) : null;
    } catch (error) {
      console.error('オフライン データ取得エラー:', error);
      return null;
    }
  }
}

// PWA Managerのインスタンスを作成
const pwaManager = new PWAManager();

// グローバルに公開
window.pwaManager = pwaManager;
