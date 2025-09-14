// 予約管理アプリ - メインJavaScript

document.addEventListener('DOMContentLoaded', function() {
    console.log('予約管理アプリが読み込まれました');
    
    // ページ読み込み時のアニメーション
    initializeAnimations();
    
    // イベントリスナーの設定
    setupEventListeners();
    
    // 初期化処理
    initializeApp();
});

/**
 * アニメーションの初期化
 */
function initializeAnimations() {
    // 情報カードのアニメーション
    const infoCards = document.querySelectorAll('.info-card');
    infoCards.forEach((card, index) => {
        card.style.animationDelay = `${index * 0.1}s`;
    });
    
    // ヘッダーのアニメーション
    const header = document.querySelector('.header');
    if (header) {
        header.style.opacity = '0';
        header.style.transform = 'translateY(-20px)';
        
        setTimeout(() => {
            header.style.transition = 'all 0.8s ease-out';
            header.style.opacity = '1';
            header.style.transform = 'translateY(0)';
        }, 100);
    }
}

/**
 * イベントリスナーの設定
 */
function setupEventListeners() {
    // ボタンのホバーエフェクト
    const buttons = document.querySelectorAll('.btn');
    buttons.forEach(button => {
        button.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-2px)';
        });
        
        button.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });
    
    // 情報カードのホバーエフェクト
    const infoCards = document.querySelectorAll('.info-card');
    infoCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-5px) scale(1.02)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0) scale(1)';
        });
    });
}

/**
 * アプリケーションの初期化
 */
function initializeApp() {
    // 現在時刻の表示
    updateCurrentTime();
    
    // 1秒ごとに時刻を更新
    setInterval(updateCurrentTime, 1000);
    
    // 受付時間のチェック
    checkBookingAvailability();
}

/**
 * 現在時刻の更新
 */
function updateCurrentTime() {
    const now = new Date();
    const timeString = now.toLocaleString('ja-JP', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
    
    // 時刻表示要素があれば更新
    const timeElement = document.getElementById('current-time');
    if (timeElement) {
        timeElement.textContent = timeString;
    }
}

/**
 * 受付可能時間のチェック
 */
function checkBookingAvailability() {
    const now = new Date();
    const currentHour = now.getHours();
    const currentMinute = now.getMinutes();
    const currentTime = currentHour * 60 + currentMinute;
    
    // 受付時間の設定
    const morningStart = 9 * 60 + 15;  // 9:15
    const morningEnd = 12 * 60;         // 12:00
    const afternoonStart = 14 * 60;     // 14:00
    const afternoonEnd = 16 * 60;       // 16:00
    
    let isAvailable = false;
    let nextAvailable = '';
    
    if (currentTime >= morningStart && currentTime < morningEnd) {
        isAvailable = true;
        nextAvailable = '午前受付中';
    } else if (currentTime >= afternoonStart && currentTime < afternoonEnd) {
        isAvailable = true;
        nextAvailable = '午後受付中';
    } else if (currentTime < morningStart) {
        nextAvailable = `次回受付開始: ${Math.floor(morningStart / 60)}:${String(morningStart % 60).padStart(2, '0')}`;
    } else if (currentTime >= morningEnd && currentTime < afternoonStart) {
        nextAvailable = `次回受付開始: ${Math.floor(afternoonStart / 60)}:${String(afternoonStart % 60).padStart(2, '0')}`;
    } else {
        nextAvailable = '本日の受付は終了しました';
    }
    
    // 受付状況の表示
    updateAvailabilityStatus(isAvailable, nextAvailable);
}

/**
 * 受付状況の表示を更新
 */
function updateAvailabilityStatus(isAvailable, message) {
    // 受付状況表示要素があれば更新
    const statusElement = document.getElementById('availability-status');
    if (statusElement) {
        statusElement.textContent = message;
        statusElement.className = isAvailable ? 'status-available' : 'status-unavailable';
    }
    
    // 新規予約ボタンの状態を更新
    const bookingButton = document.querySelector('.btn-primary');
    if (bookingButton) {
        if (isAvailable) {
            bookingButton.disabled = false;
            bookingButton.style.opacity = '1';
            bookingButton.style.cursor = 'pointer';
        } else {
            bookingButton.disabled = true;
            bookingButton.style.opacity = '0.6';
            bookingButton.style.cursor = 'not-allowed';
        }
    }
}

/**
 * 通知の表示
 */
function showNotification(message, type = 'info') {
    // 通知要素の作成
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <span class="notification-message">${message}</span>
            <button class="notification-close">&times;</button>
        </div>
    `;
    
    // スタイルの設定
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${type === 'success' ? '#2ecc71' : type === 'error' ? '#e74c3c' : '#3498db'};
        color: white;
        padding: 15px 20px;
        border-radius: 10px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
        z-index: 1000;
        transform: translateX(100%);
        transition: transform 0.3s ease;
        max-width: 300px;
    `;
    
    // ページに追加
    document.body.appendChild(notification);
    
    // アニメーション表示
    setTimeout(() => {
        notification.style.transform = 'translateX(0)';
    }, 100);
    
    // 閉じるボタンのイベント
    const closeButton = notification.querySelector('.notification-close');
    closeButton.addEventListener('click', () => {
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    });
    
    // 自動で閉じる（5秒後）
    setTimeout(() => {
        if (document.body.contains(notification)) {
            notification.style.transform = 'translateX(100%)';
            setTimeout(() => {
                if (document.body.contains(notification)) {
                    document.body.removeChild(notification);
                }
            }, 300);
        }
    }, 5000);
}

/**
 * ページ遷移のアニメーション
 */
function animatePageTransition() {
    const container = document.querySelector('.container');
    if (container) {
        container.style.opacity = '0';
        container.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
            container.style.transition = 'all 0.5s ease-out';
            container.style.opacity = '1';
            container.style.transform = 'translateY(0)';
        }, 100);
    }
}

/**
 * エラーハンドリング
 */
function handleError(error, context = '') {
    console.error(`エラーが発生しました (${context}):`, error);
    
    // ユーザーに通知
    showNotification(
        `エラーが発生しました: ${error.message || '不明なエラー'}`,
        'error'
    );
}

/**
 * 成功通知
 */
function showSuccess(message) {
    showNotification(message, 'success');
}

/**
 * 情報通知
 */
function showInfo(message) {
    showNotification(message, 'info');
}

// グローバル関数として公開
window.showNotification = showNotification;
window.showSuccess = showSuccess;
window.showInfo = showInfo;
window.handleError = handleError;
