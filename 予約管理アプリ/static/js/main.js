/**
 * メインページ用のJavaScript
 */

document.addEventListener('DOMContentLoaded', function() {
    initializeMainPage();
});

/**
 * メインページの初期化
 */
function initializeMainPage() {
    // アニメーションの開始
    startAnimations();
    
    // リアルタイム時計の開始
    startRealTimeClock();
    
    // 予約状況の確認
    checkBookingStatus();
    
    // イベントリスナーの設定
    setupEventListeners();
}

/**
 * アニメーションの開始
 */
function startAnimations() {
    // ヒーローセクションのフェードイン
    const heroSection = document.querySelector('.hero-section');
    if (heroSection) {
        heroSection.style.opacity = '0';
        heroSection.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
            heroSection.style.transition = 'all 0.8s ease-out';
            heroSection.style.opacity = '1';
            heroSection.style.transform = 'translateY(0)';
        }, 300);
    }
    
    // カードの順次表示
    const cards = document.querySelectorAll('.info-card');
    cards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
            card.style.transition = 'all 0.6s ease-out';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, 500 + (index * 200));
    });
}

/**
 * リアルタイム時計の開始
 */
function startRealTimeClock() {
    function updateClock() {
        const now = new Date();
        const timeString = now.toLocaleTimeString('ja-JP', {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
        
        // 時計表示要素があれば更新
        const clockElement = document.getElementById('currentTime');
        if (clockElement) {
            clockElement.textContent = timeString;
        }
        
        // 受付時間の確認
        checkReceptionTime(now);
    }
    
    // 1秒ごとに更新
    updateClock();
    setInterval(updateClock, 1000);
}

/**
 * 受付時間の確認
 */
function checkReceptionTime(now) {
    const hour = now.getHours();
    const minute = now.getMinutes();
    const currentTime = hour * 60 + minute;
    const receptionStart = 9 * 60 + 15; // 09:15
    
    const statusElement = document.getElementById('receptionStatus');
    if (statusElement) {
        if (currentTime >= receptionStart) {
            statusElement.textContent = '🟢 受付中';
            statusElement.className = 'status-indicator open';
        } else {
            const remainingMinutes = receptionStart - currentTime;
            const remainingHours = Math.floor(remainingMinutes / 60);
            const remainingMins = remainingMinutes % 60;
            
            if (remainingHours > 0) {
                statusElement.textContent = `⏰ 受付開始まで ${remainingHours}時間${remainingMins}分`;
            } else {
                statusElement.textContent = `⏰ 受付開始まで ${remainingMins}分`;
            }
            statusElement.className = 'status-indicator waiting';
        }
    }
}

/**
 * 予約状況の確認
 */
async function checkBookingStatus() {
    try {
        const response = await fetch('/api/bookings');
        const result = await response.json();
        
        if (result.success) {
            updateBookingStats(result.bookings);
        }
    } catch (error) {
        console.error('予約状況の取得に失敗:', error);
    }
}

/**
 * 予約統計の更新
 */
function updateBookingStats(bookings) {
    const totalElement = document.getElementById('totalBookings');
    const successElement = document.getElementById('successBookings');
    const failedElement = document.getElementById('failedBookings');
    
    if (totalElement && successElement && failedElement) {
        const total = bookings.length;
        const success = bookings.filter(b => b.status === 'success').length;
        const failed = bookings.filter(b => b.status === 'failed').length;
        
        totalElement.textContent = total;
        successElement.textContent = success;
        failedElement.textContent = failed;
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
            this.style.boxShadow = '0 4px 8px rgba(0,0,0,0.2)';
        });
        
        button.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
            this.style.boxShadow = '0 2px 4px rgba(0,0,0,0.1)';
        });
    });
    
    // カードのホバーエフェクト
    const cards = document.querySelectorAll('.info-card');
    cards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-5px)';
            this.style.boxShadow = '0 8px 16px rgba(0,0,0,0.2)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
            this.style.boxShadow = '0 2px 8px rgba(0,0,0,0.1)';
        });
    });
}

/**
 * 通知の表示
 */
function showNotification(message, type = 'info') {
    // 既存の通知を削除
    const existingNotification = document.querySelector('.notification');
    if (existingNotification) {
        existingNotification.remove();
    }
    
    // 新しい通知を作成
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <span class="notification-message">${message}</span>
            <button class="notification-close" onclick="this.parentElement.parentElement.remove()">&times;</button>
        </div>
    `;
    
    // 通知を表示
    document.body.appendChild(notification);
    
    // 3秒後に自動で非表示
    setTimeout(() => {
        if (notification.parentElement) {
            notification.remove();
        }
    }, 3000);
}

/**
 * 成功通知の表示
 */
function showSuccess(message) {
    showNotification(message, 'success');
}

/**
 * エラー通知の表示
 */
function showError(message) {
    showNotification(message, 'error');
}

/**
 * 情報通知の表示
 */
function showInfo(message) {
    showNotification(message, 'info');
}

/**
 * エラーハンドリング
 */
function handleError(error, context = '') {
    console.error(`エラー (${context}):`, error);
    showError(`エラーが発生しました: ${error.message}`);
}
