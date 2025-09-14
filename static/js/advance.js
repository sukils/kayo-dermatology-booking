/**
 * 事前予約ページ用JavaScript
 * かよ皮膚科予約システム
 */

document.addEventListener('DOMContentLoaded', function() {
    // 要素の取得
    const advanceBookingForm = document.getElementById('advanceBookingForm');
    const refreshBookingsBtn = document.getElementById('refreshBookings');
    const bookingsList = document.getElementById('bookingsList');
    const messageContainer = document.getElementById('messageContainer');
    const messageText = document.getElementById('messageText');
    const closeMessageBtn = document.getElementById('closeMessage');

    // 日付入力の初期化
    initializeDateInputs();

    // イベントリスナーの設定
    advanceBookingForm.addEventListener('submit', handleAdvanceBookingSubmit);
    refreshBookingsBtn.addEventListener('click', loadAdvanceBookings);
    closeMessageBtn.addEventListener('click', hideMessage);

    // 初期データ読み込み
    loadAdvanceBookings();
    
    // カレンダー連携状況の確認
    checkCalendarStatus();
});

/**
 * 日付入力フィールドの初期化
 */
function initializeDateInputs() {
    const today = new Date();
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);
    
    // 予約希望日の最小値を明日に設定
    const targetBookingDate = document.getElementById('targetBookingDate');
    targetBookingDate.min = tomorrow.toISOString().split('T')[0];
    
    // 実行日の最大値を今日に設定
    const executionDate = document.getElementById('executionDate');
    executionDate.max = today.toISOString().split('T')[0];
    
    // 予約希望日が変更された時の処理
    targetBookingDate.addEventListener('change', function() {
        const targetDate = new Date(this.value);
        const maxExecutionDate = new Date(targetDate);
        maxExecutionDate.setDate(maxExecutionDate.getDate() - 1);
        
        executionDate.max = maxExecutionDate.toISOString().split('T')[0];
        
        // 実行日が予約希望日より後になっている場合はクリア
        if (executionDate.value && new Date(executionDate.value) >= targetDate) {
            executionDate.value = '';
        }
    });
    
    // 実行日が変更された時の処理
    executionDate.addEventListener('change', function() {
        const executionDateValue = new Date(this.value);
        const targetDate = new Date(targetBookingDate.value);
        
        if (executionDateValue >= targetDate) {
            showMessage('実行日は予約希望日より前の日付を選択してください', 'error');
            this.value = '';
        }
    });
}

/**
 * カレンダー連携状況の確認
 */
async function checkCalendarStatus() {
    const statusElement = document.getElementById('calendarStatus');
    
    try {
        // 設定ファイルからカレンダー連携の状況を確認
        const response = await fetch('/api/calendar-status');
        const data = await response.json();
        
        if (data.success) {
            if (data.enabled) {
                statusElement.textContent = '連携中';
                statusElement.className = 'status-value connected';
            } else {
                statusElement.textContent = '無効';
                statusElement.className = 'status-value disconnected';
            }
        } else {
            statusElement.textContent = '確認失敗';
            statusElement.className = 'status-value disconnected';
        }
    } catch (error) {
        console.error('カレンダー状況確認エラー:', error);
        statusElement.textContent = '確認失敗';
        statusElement.className = 'status-value disconnected';
    }
}

/**
 * 事前予約フォームの送信処理
 */
async function handleAdvanceBookingSubmit(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const bookingData = {
        patient_number: formData.get('patientNumber'),
        birth_date: formData.get('birthDate'),
        target_booking_date: formData.get('targetBookingDate'),
        execution_date: formData.get('executionDate'),
        booking_time: formData.get('bookingTime')
    };
    
    // 入力値の検証
    if (!validateAdvanceBookingData(bookingData)) {
        return;
    }
    
    try {
        // 送信ボタンを無効化
        const submitBtn = event.target.querySelector('button[type="submit"]');
        const originalText = submitBtn.textContent;
        submitBtn.disabled = true;
        submitBtn.textContent = '作成中...';
        
        const response = await fetch('/api/advance-booking', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(bookingData)
        });
        
        const result = await response.json();
        
        if (result.success) {
            showMessage(result.message, 'success');
            event.target.reset();
            loadAdvanceBookings(); // 一覧を更新
        } else {
            showMessage(result.message, 'error');
        }
        
    } catch (error) {
        console.error('事前予約作成エラー:', error);
        showMessage('システムエラーが発生しました。しばらく時間をおいて再度お試しください。', 'error');
    } finally {
        // 送信ボタンを有効化
        const submitBtn = event.target.querySelector('button[type="submit"]');
        submitBtn.disabled = false;
        submitBtn.textContent = originalText;
    }
}

/**
 * 事前予約データの検証
 */
function validateAdvanceBookingData(data) {
    // 患者番号の検証
    if (!data.patient_number || !/^\d+$/.test(data.patient_number)) {
        showMessage('患者番号は数字のみ入力してください', 'error');
        return false;
    }
    
    // 日付の検証
    if (!data.birth_date || !data.target_booking_date || !data.execution_date) {
        showMessage('すべての日付を入力してください', 'error');
        return false;
    }
    
    const today = new Date();
    const targetDate = new Date(data.target_booking_date);
    const executionDate = new Date(data.execution_date);
    
    // 予約希望日が今日以降かチェック
    if (targetDate <= today) {
        showMessage('予約希望日は明日以降の日付を選択してください', 'error');
        return false;
    }
    
    // 実行日が予約希望日より前かチェック
    if (executionDate >= targetDate) {
        showMessage('実行日は予約希望日より前の日付を選択してください', 'error');
        return false;
    }
    
    return true;
}

/**
 * 事前予約一覧の読み込み
 */
async function loadAdvanceBookings() {
    try {
        bookingsList.innerHTML = '<p class="loading">読み込み中...</p>';
        
        const response = await fetch('/api/advance-bookings');
        const result = await response.json();
        
        if (result.success) {
            displayAdvanceBookings(result.advance_bookings);
        } else {
            bookingsList.innerHTML = `<p class="error">エラー: ${result.message}</p>`;
        }
        
    } catch (error) {
        console.error('事前予約一覧取得エラー:', error);
        bookingsList.innerHTML = '<p class="error">データの取得に失敗しました</p>';
    }
}

/**
 * 事前予約一覧の表示
 */
function displayAdvanceBookings(bookings) {
    if (bookings.length === 0) {
        bookingsList.innerHTML = '<p class="no-data">事前予約がありません</p>';
        return;
    }
    
    const bookingsHTML = bookings.map(booking => `
        <div class="booking-item ${booking.status}" data-id="${booking.id}">
            <div class="booking-header">
                <h3>事前予約 #${booking.id}</h3>
                <span class="status-badge ${booking.status}">${getStatusText(booking.status)}</span>
            </div>
            <div class="booking-details">
                <div class="detail-row">
                    <span class="label">患者番号:</span>
                    <span class="value">${booking.patient_number}</span>
                </div>
                <div class="detail-row">
                    <span class="label">誕生日:</span>
                    <span class="value">${formatDate(booking.birth_date)}</span>
                </div>
                <div class="detail-row">
                    <span class="label">予約希望日:</span>
                    <span class="value">${formatDate(booking.target_booking_date)} ${booking.booking_time}</span>
                </div>
                <div class="detail-row">
                    <span class="label">実行日:</span>
                    <span class="value">${formatDate(booking.execution_date)}</span>
                </div>
                <div class="detail-row">
                    <span class="label">作成日:</span>
                    <span class="value">${formatDateTime(booking.created_at)}</span>
                </div>
                ${booking.message ? `
                <div class="detail-row">
                    <span class="label">メッセージ:</span>
                    <span class="value">${booking.message}</span>
                </div>
                ` : ''}
            </div>
            <div class="booking-actions">
                <button class="btn btn-danger btn-sm" onclick="deleteAdvanceBooking(${booking.id})">
                    削除
                </button>
            </div>
        </div>
    `).join('');
    
    bookingsList.innerHTML = bookingsHTML;
}

/**
 * 事前予約の削除
 */
async function deleteAdvanceBooking(bookingId) {
    if (!confirm('この事前予約を削除しますか？')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/advance-bookings/${bookingId}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (result.success) {
            showMessage(result.message, 'success');
            loadAdvanceBookings(); // 一覧を更新
        } else {
            showMessage(result.message, 'error');
        }
        
    } catch (error) {
        console.error('事前予約削除エラー:', error);
        showMessage('削除に失敗しました', 'error');
    }
}

/**
 * ステータスの表示テキストを取得
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
 * 日付のフォーマット
 */
function formatDate(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString('ja-JP');
}

/**
 * 日時のフォーマット
 */
function formatDateTime(dateTimeString) {
    if (!dateTimeString) return '-';
    const date = new Date(dateTimeString);
    return date.toLocaleString('ja-JP');
}

/**
 * メッセージの表示
 */
function showMessage(message, type = 'info') {
    messageText.textContent = message;
    messageContainer.className = `message-container ${type}`;
    messageContainer.style.display = 'block';
    
    // 5秒後に自動で非表示
    setTimeout(() => {
        hideMessage();
    }, 5000);
}

/**
 * メッセージの非表示
 */
function hideMessage() {
    messageContainer.style.display = 'none';
}
