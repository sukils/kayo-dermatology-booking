/**
 * スケジュール予約用のJavaScript
 */

document.addEventListener('DOMContentLoaded', function() {
    initializeScheduledPage();
});

/**
 * スケジュールページの初期化
 */
function initializeScheduledPage() {
    const form = document.getElementById('scheduledBookingForm');
    const submitBtn = document.getElementById('submitBtn');
    
    // フォーム送信イベント
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        handleScheduledBookingSubmission();
    });
    
    // 入力値の検証設定
    setupValidation();
    
    // スケジュール予約一覧を読み込み
    loadScheduledBookings();
}

/**
 * スケジュール予約送信の処理
 */
async function handleScheduledBookingSubmission() {
    const form = document.getElementById('scheduledBookingForm');
    const submitBtn = document.getElementById('submitBtn');
    const statusDiv = document.getElementById('scheduledStatus');
    const statusMessage = document.getElementById('statusMessage');
    
    // フォームデータの取得
    const formData = new FormData(form);
    const targetBookingDate = formData.get('target_booking_date');
    const executionTime = formData.get('execution_time');
    const patientNumber = formData.get('patient_number');
    const birthDate = formData.get('birth_date');
    const bookingTime = formData.get('booking_time');
    
    // 入力値の検証
    if (!validateScheduledInputs(targetBookingDate, executionTime, patientNumber, birthDate)) {
        return;
    }
    
    // 送信ボタンを無効化
    submitBtn.disabled = true;
    submitBtn.textContent = '設定中...';
    
    // ステータス表示をクリア
    statusDiv.style.display = 'block';
    statusMessage.innerHTML = '<div class="loading">🔄 スケジュール予約を設定中...</div>';
    
    try {
        // APIにスケジュール予約リクエストを送信
        const response = await fetch('/api/scheduled-booking', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                target_booking_date: targetBookingDate,
                execution_time: executionTime,
                patient_number: patientNumber,
                birth_date: birthDate,
                booking_time: bookingTime
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            // スケジュール予約成功
            statusMessage.innerHTML = `
                <div class="success-message">
                    <h3>🎉 スケジュール予約設定完了！</h3>
                    <p><strong>予約ID:</strong> <span class="booking-id">${result.scheduled_booking_id}</span></p>
                    <p><strong>メッセージ:</strong> ${result.message}</p>
                    <p><strong>予約希望日:</strong> ${formatDate(targetBookingDate)}</p>
                    <p><strong>実行時刻:</strong> ${formatDateTime(executionTime)}</p>
                    <p><strong>患者番号:</strong> ${patientNumber}</p>
                    <p><strong>誕生日:</strong> ${formatDate(birthDate)}</p>
                    <div class="success-actions">
                        <button onclick="resetForm()" class="btn btn-primary">🔄 新規設定</button>
                    </div>
                </div>
            `;
            
            // フォームをリセット
            form.reset();
            
            // スケジュール予約一覧を更新
            loadScheduledBookings();
            
            // 成功通知
            showNotification('スケジュール予約が設定されました！', 'success');
            
        } else {
            // スケジュール予約失敗
            statusMessage.innerHTML = `
                <div class="error-message">
                    <h3>❌ スケジュール予約設定失敗</h3>
                    <p><strong>エラー:</strong> ${result.message}</p>
                    <div class="error-actions">
                        <button onclick="retrySubmission()" class="btn btn-primary">🔄 再試行</button>
                        <button onclick="resetForm()" class="btn btn-secondary">📝 フォームリセット</button>
                    </div>
                </div>
            `;
            
            // エラー通知
            showNotification('スケジュール予約の設定に失敗しました', 'error');
        }
        
    } catch (error) {
        console.error('スケジュール予約エラー:', error);
        statusMessage.innerHTML = `
            <div class="error-message">
                <h3>❌ システムエラー</h3>
                <p>スケジュール予約設定中にエラーが発生しました。</p>
                <p><strong>エラー詳細:</strong> ${error.message}</p>
                <div class="error-actions">
                    <button onclick="retrySubmission()" class="btn btn-primary">🔄 再試行</button>
                    <button onclick="resetForm()" class="btn btn-secondary">📝 フォームリセット</button>
                </div>
            </div>
        `;
        
        // エラー通知
        showNotification('システムエラーが発生しました', 'error');
    } finally {
        // 送信ボタンを再有効化
        submitBtn.disabled = false;
        submitBtn.textContent = '🚀 スケジュール予約設定';
    }
}

/**
 * 入力値の検証
 */
function validateScheduledInputs(targetBookingDate, executionTime, patientNumber, birthDate) {
    // 予約希望日の検証
    if (!targetBookingDate) {
        showNotification('予約希望日を選択してください', 'error');
        return false;
    }
    
    const targetDate = new Date(targetBookingDate);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    
    if (targetDate < today) {
        showNotification('予約希望日は今日以降の日付を選択してください', 'error');
        return false;
    }
    
    // 実行時刻の検証
    if (!executionTime) {
        showNotification('実行時刻を選択してください', 'error');
        return false;
    }
    
    const executionDateTime = new Date(executionTime);
    if (executionDateTime <= new Date()) {
        showNotification('実行時刻は現在時刻より後の時刻を設定してください', 'error');
        return false;
    }
    
    // 患者番号の検証
    if (!patientNumber || !patientNumber.trim()) {
        showNotification('診察券番号を入力してください', 'error');
        return false;
    }
    
    if (!/^\d+$/.test(patientNumber.trim())) {
        showNotification('診察券番号は数字のみ入力してください', 'error');
        return false;
    }
    
    // 誕生日の検証
    if (!birthDate) {
        showNotification('誕生日を選択してください', 'error');
        return false;
    }
    
    return true;
}

/**
 * 入力値の検証設定
 */
function setupValidation() {
    const targetBookingDateInput = document.getElementById('target_booking_date');
    const executionTimeInput = document.getElementById('execution_time');
    const patientNumberInput = document.getElementById('patient_number');
    const birthDateInput = document.getElementById('birth_date');
    
    // 予約希望日の最小値を今日に設定
    const today = new Date().toISOString().split('T')[0];
    targetBookingDateInput.min = today;
    
    // 実行時刻の最小値を現在時刻に設定
    const now = new Date();
    const localDateTime = new Date(now.getTime() - now.getTimezoneOffset() * 60000);
    executionTimeInput.min = localDateTime.toISOString().slice(0, 16);
    
    // 患者番号の入力制限（数字のみ）
    patientNumberInput.addEventListener('input', function(e) {
        this.value = this.value.replace(/[^0-9]/g, '');
    });
    
    // 誕生日の最大値を今日に設定
    birthDateInput.max = today;
}

/**
 * スケジュール予約一覧の読み込み
 */
async function loadScheduledBookings() {
    try {
        const response = await fetch('/api/scheduled-bookings');
        const result = await response.json();
        
        if (result.success) {
            displayScheduledBookings(result.scheduled_bookings);
        } else {
            showNotification('スケジュール予約一覧の取得に失敗しました', 'error');
        }
    } catch (error) {
        console.error('スケジュール予約一覧取得エラー:', error);
        showNotification('スケジュール予約一覧の取得に失敗しました', 'error');
    }
}

/**
 * スケジュール予約一覧の表示
 */
function displayScheduledBookings(scheduledBookings) {
    const bookingsList = document.getElementById('scheduledBookingsList');
    if (!bookingsList) return;
    
    if (scheduledBookings.length === 0) {
        bookingsList.innerHTML = '<div class="no-bookings">設定済みのスケジュール予約がありません</div>';
        return;
    }
    
    const bookingsHTML = scheduledBookings.map(booking => createScheduledBookingCard(booking)).join('');
    bookingsList.innerHTML = bookingsHTML;
    
    // 各カードにイベントリスナーを設定
    scheduledBookings.forEach(booking => {
        setupScheduledBookingCardEvents(booking.id);
    });
}

/**
 * スケジュール予約カードの作成
 */
function createScheduledBookingCard(booking) {
    const statusClass = getStatusClass(booking.status);
    const statusText = getStatusText(booking.status);
    const executionDateTime = formatDateTime(booking.execution_time);
    const targetDate = formatDate(booking.target_booking_date);
    
    return `
        <div class="scheduled-booking-card ${statusClass}" data-booking-id="${booking.id}">
            <div class="booking-header">
                <h3>スケジュール予約 #${booking.id}</h3>
                <span class="status-badge ${statusClass}">${statusText}</span>
            </div>
            <div class="booking-details">
                <p><strong>予約希望日:</strong> ${targetDate}</p>
                <p><strong>実行時刻:</strong> ${executionDateTime}</p>
                <p><strong>患者番号:</strong> ${booking.patient_number}</p>
                <p><strong>誕生日:</strong> ${formatDate(booking.birth_date)}</p>
                <p><strong>希望時間:</strong> ${booking.booking_time}</p>
                ${booking.message ? `<p><strong>メッセージ:</strong> ${booking.message}</p>` : ''}
            </div>
            <div class="booking-actions">
                <button class="btn btn-danger btn-sm" onclick="deleteScheduledBooking(${booking.id})">
                    🗑️ 削除
                </button>
            </div>
        </div>
    `;
}

/**
 * スケジュール予約カードのイベント設定
 */
function setupScheduledBookingCardEvents(bookingId) {
    const card = document.querySelector(`[data-booking-id="${bookingId}"]`);
    if (!card) return;
    
    // カードクリックで詳細表示（必要に応じて）
    card.addEventListener('click', function(e) {
        if (!e.target.closest('button')) {
            // 詳細表示の処理（必要に応じて実装）
        }
    });
}

/**
 * スケジュール予約の削除
 */
async function deleteScheduledBooking(bookingId) {
    if (!confirm('このスケジュール予約を削除しますか？')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/scheduled-bookings/${bookingId}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (result.success) {
            showNotification('スケジュール予約を削除しました', 'success');
            loadScheduledBookings(); // 一覧を更新
        } else {
            showNotification('スケジュール予約の削除に失敗しました', 'error');
        }
    } catch (error) {
        console.error('スケジュール予約削除エラー:', error);
        showNotification('スケジュール予約の削除に失敗しました', 'error');
    }
}

/**
 * ステータスクラスの取得
 */
function getStatusClass(status) {
    const statusMap = {
        'pending': 'pending',
        'completed': 'success',
        'failed': 'error'
    };
    return statusMap[status] || 'pending';
}

/**
 * ステータステキストの取得
 */
function getStatusText(status) {
    const statusMap = {
        'pending': '待機中',
        'completed': '完了',
        'failed': '失敗'
    };
    return statusMap[status] || status;
}

/**
 * フォームをリセット
 */
function resetForm() {
    const form = document.getElementById('scheduledBookingForm');
    const statusDiv = document.getElementById('scheduledStatus');
    
    form.reset();
    statusDiv.style.display = 'none';
    
    // フォーカスを予約希望日フィールドに移動
    document.getElementById('target_booking_date').focus();
}

/**
 * 再試行
 */
function retrySubmission() {
    const statusDiv = document.getElementById('scheduledStatus');
    statusDiv.style.display = 'none';
    
    // フォーカスを送信ボタンに移動
    document.getElementById('submitBtn').focus();
}

/**
 * 日付のフォーマット
 */
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('ja-JP', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit'
    });
}

/**
 * 日時のフォーマット
 */
function formatDateTime(dateTimeString) {
    const date = new Date(dateTimeString);
    return date.toLocaleString('ja-JP', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
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
