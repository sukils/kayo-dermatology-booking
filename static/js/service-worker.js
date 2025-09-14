// かよ皮膚科予約管理アプリ - サービスワーカー
// バックグラウンドで動作し、ロック中でも予約処理を継続

const CACHE_NAME = 'kayo-dermatology-booking-v1';
const API_BASE_URL = '/api';

// キャッシュするリソース
const CACHE_URLS = [
  '/',
  '/booking',
  '/advance',
  '/scheduled',
  '/history',
  '/static/css/style.css',
  '/static/js/main.js',
  '/static/js/booking.js',
  '/static/js/advance.js',
  '/static/js/history.js',
  '/static/manifest.json'
];

// インストール時の処理
self.addEventListener('install', (event) => {
  console.log('Service Worker: インストール中...');
  
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('Service Worker: キャッシュを開きました');
        return cache.addAll(CACHE_URLS);
      })
      .then(() => {
        console.log('Service Worker: インストール完了');
        return self.skipWaiting();
      })
      .catch((error) => {
        console.error('Service Worker: インストールエラー', error);
      })
  );
});

// アクティベート時の処理
self.addEventListener('activate', (event) => {
  console.log('Service Worker: アクティベート中...');
  
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME) {
            console.log('Service Worker: 古いキャッシュを削除:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => {
      console.log('Service Worker: アクティベート完了');
      return self.clients.claim();
    })
  );
});

// フェッチイベントの処理（ネットワークリクエストのインターセプト）
self.addEventListener('fetch', (event) => {
  const request = event.request;
  const url = new URL(request.url);
  
  // APIリクエストの処理
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(handleApiRequest(request));
  } else {
    // 静的リソースの処理
    event.respondWith(handleStaticRequest(request));
  }
});

// APIリクエストの処理
async function handleApiRequest(request) {
  try {
    // まずネットワークから取得を試行
    const networkResponse = await fetch(request);
    
    // 成功した場合はそのまま返す
    if (networkResponse.ok) {
      return networkResponse;
    }
    
    // 失敗した場合はキャッシュから取得
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    
    // キャッシュにもない場合はネットワークレスポンスを返す
    return networkResponse;
    
  } catch (error) {
    console.error('APIリクエストエラー:', error);
    
    // ネットワークエラーの場合はキャッシュから取得
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    
    // オフライン用のレスポンスを返す
    return new Response(
      JSON.stringify({
        success: false,
        message: 'オフラインです。ネットワーク接続を確認してください。',
        offline: true
      }),
      {
        status: 503,
        headers: { 'Content-Type': 'application/json' }
      }
    );
  }
}

// 静的リソースの処理
async function handleStaticRequest(request) {
  try {
    // まずキャッシュから取得を試行
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    
    // キャッシュにない場合はネットワークから取得
    const networkResponse = await fetch(request);
    
    if (networkResponse.ok) {
      // 成功した場合はキャッシュに保存
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, networkResponse.clone());
    }
    
    return networkResponse;
    
  } catch (error) {
    console.error('静的リソース取得エラー:', error);
    
    // オフライン用のフォールバックページを返す
    if (request.destination === 'document') {
      return caches.match('/') || new Response('オフラインです', { status: 503 });
    }
    
    throw error;
  }
}

// バックグラウンド同期の処理
self.addEventListener('sync', (event) => {
  console.log('Service Worker: バックグラウンド同期', event.tag);
  
  if (event.tag === 'booking-sync') {
    event.waitUntil(syncBookings());
  }
});

// 予約データの同期
async function syncBookings() {
  try {
    console.log('Service Worker: 予約データを同期中...');
    
    // IndexedDBから同期待ちの予約データを取得
    const pendingBookings = await getPendingBookings();
    
    for (const booking of pendingBookings) {
      try {
        const response = await fetch('/api/booking', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(booking)
        });
        
        if (response.ok) {
          // 成功した場合は同期済みとしてマーク
          await markBookingAsSynced(booking.id);
          console.log('予約同期成功:', booking.id);
        }
      } catch (error) {
        console.error('予約同期エラー:', error);
      }
    }
    
  } catch (error) {
    console.error('バックグラウンド同期エラー:', error);
  }
}

// プッシュ通知の処理
self.addEventListener('push', (event) => {
  console.log('Service Worker: プッシュ通知を受信');
  
  let notificationData = {
    title: 'かよ皮膚科予約管理',
    body: '新しい通知があります',
    icon: '/static/icons/icon-192x192.png',
    badge: '/static/icons/icon-72x72.png',
    tag: 'booking-notification',
    requireInteraction: true,
    actions: [
      {
        action: 'view',
        title: '確認する'
      },
      {
        action: 'dismiss',
        title: '閉じる'
      }
    ]
  };
  
  if (event.data) {
    try {
      const data = event.data.json();
      notificationData = { ...notificationData, ...data };
    } catch (error) {
      console.error('プッシュデータの解析エラー:', error);
    }
  }
  
  event.waitUntil(
    self.registration.showNotification(notificationData.title, notificationData)
  );
});

// 通知クリックの処理
self.addEventListener('notificationclick', (event) => {
  console.log('Service Worker: 通知がクリックされました');
  
  event.notification.close();
  
  if (event.action === 'view') {
    event.waitUntil(
      clients.openWindow('/')
    );
  }
});

// IndexedDBの操作（簡易版）
async function getPendingBookings() {
  // 実際の実装ではIndexedDBを使用
  // ここでは簡易的にlocalStorageを使用
  try {
    const pending = localStorage.getItem('pendingBookings');
    return pending ? JSON.parse(pending) : [];
  } catch (error) {
    console.error('pendingBookings取得エラー:', error);
    return [];
  }
}

async function markBookingAsSynced(bookingId) {
  try {
    const pending = await getPendingBookings();
    const updated = pending.filter(booking => booking.id !== bookingId);
    localStorage.setItem('pendingBookings', JSON.stringify(updated));
  } catch (error) {
    console.error('予約同期マークエラー:', error);
  }
}

// メッセージの処理
self.addEventListener('message', (event) => {
  console.log('Service Worker: メッセージを受信', event.data);
  
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
  
  if (event.data && event.data.type === 'SYNC_BOOKINGS') {
    syncBookings();
  }
});

console.log('Service Worker: 読み込み完了');
