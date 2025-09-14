/**
 * 予約履歴用のJavaScript
 */

document.addEventListener('DOMContentLoaded', function() {
    initializeHistoryPage();
});

/**
 * 履歴ページの初期化
 */
function initializeHistoryPage() {
    setupEventListeners();
    loadBookings();
    initializeFilters();
}

/**
 * イベントリスナーの設定
 */
function setupEventListeners() {
    // 更新ボタン
    const refreshBtn = document.getElementById('refreshBtn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', loadBookings);
    }
    
    // フィルター
    const statusFilter = document.getElementById('statusFilter');
    const dateFilter = document.getElementById('dateFilter');
    const clearFilterBtn = document.getElementById('clearFilterBtn');
    
    if (statusFilter) {
        statusFilter.addEventListener('change', applyFilters);
    }
    if (dateFilter) {
        dateFilter.addEventListener('change', applyFilters);
    }
    if (clearFilterBtn) {
        clearFilterBtn.addEventListener('click', clearFilters);
    }
    
    // モーダル
    const modalClose = document.getElementById('modalClose');
    if (modalClose) {
        modalClose.addEventListener('click', closeModal);
    }
    
    // モーダル外クリックで閉じる
    const modal = document.getElementById('bookingModal');
    if (modal) {
        modal.addEventListener('click', function(e) {
            if (e.target === modal) {
                closeModal();
            }
        });
    }
}

/**
 * 予約一覧の読み込み
 */
async function loadBookings() {
    try {
        const response = await fetch('/api/bookings');
        const result = await response.json();
        
        if (result.success) {
            displayBookings(result.bookings);
            updateStats(result.bookings);
        } else {
            showNotification('予約一覧の取得に失敗しました', 'error');
        }
    } catch (error) {
        console.error('予約一覧取得エラー:', error);
        showNotification('予約一覧の取得に失敗しました', 'error');
    }
}

/**
 * 予約一覧の表示
 */
function displayBookings(bookings) {
    const bookingsList = document.getElementById('bookingsList');
    if (!bookingsList) return;
    
    if (bookings.length === 0) {
        bookingsList.innerHTML = '<div class="no-bookings">予約履歴がありません</div>';
        return;
    }
    
    const bookingsHTML = bookings.map(booking => createBookingCard(booking)).join('');
    bookingsList.innerHTML = bookingsHTML;
    
    // 各カードにイベントリスナーを設定
    bookings.forEach(booking => {
        setupBookingCardEvents(booking.id);
    });
}

/**
 * 予約カードの作成
 */
function createBookingCard(booking) {
    const statusClass = booking.status === 'success' ? 'success' : 'error';
    const statusText = getStatusText(booking.status);
    const createdDate = formatDateTime(booking.created_at);
    
    return `
        <div class="booking-card ${statusClass}" data-booking-id="${booking.id}">
            <div class="booking-header">
                <h3>予約 #${booking.id}</h3>
                <span class="status-badge ${statusClass}">${statusText}</span>
            </div>
            <div class="booking-details">
                <p><strong>患者番号:</strong> ${booking.patient_number}</p>
                <p><strong>誕生日:</strong> ${formatDate(booking.birth_date)}</p>
                <p><strong>予約日:</strong> ${formatDate(booking.booking_date)}</p>
                <p><strong>作成日時:</strong> ${createdDate}</p>
                ${booking.message ? `<p><strong>メッセージ:</strong> ${booking.message}</p>` : ''}
            </div>
            <div class="booking-actions">
                <button class="btn btn-secondary btn-sm" onclick="showBookingDetails(${booking.id})">
                    📋 詳細
                </button>
                <button class="btn btn-primary btn-sm" onclick="rebookPatient('${booking.patient_number}', '${booking.birth_date}')">
                    🔄 再予約
                </button>
            </div>
        </div>
    `;
}

/**
 * 予約カードのイベント設定
 */
function setupBookingCardEvents(bookingId) {
    const card = document.querySelector(`[data-booking-id="${bookingId}"]`);
    if (!card) return;
    
    // カードクリックで詳細表示
    card.addEventListener('click', function(e) {
        if (!e.target.closest('button')) {
            showBookingDetails(bookingId);
        }
    });
}

/**
 * 予約詳細の表示
 */
async function showBookingDetails(bookingId) {
    try {
        const response = await fetch(`/api/bookings/${bookingId}`);
        const result = await response.json();
        
        if (result.success) {
            displayBookingModal(result.booking);
        } else {
            showNotification('予約詳細の取得に失敗しました', 'error');
        }
    } catch (error) {
        console.error('予約詳細取得エラー:', error);
        showNotification('予約詳細の取得に失敗しました', 'error');
    }
}

/**
 * 予約詳細モーダルの表示
 */
function displayBookingModal(booking) {
    const modal = document.getElementById('bookingModal');
    const modalTitle = document.getElementById('modalTitle');
    const modalBody = document.getElementById('modalBody');
    
    if (!modal || !modalTitle || !modalBody) return;
    
    modalTitle.textContent = `予約詳細 #${booking.id}`;
    
    const statusClass = booking.status === 'success' ? 'success' : 'error';
    const statusText = getStatusText(booking.status);
    
    modalBody.innerHTML = `
        <div class="booking-details-full">
            <div class="detail-section">
                <h4>基本情報</h4>
                <p><strong>予約番号:</strong> ${booking.id}</p>
                <p><strong>ステータス:</strong> <span class="status-badge ${statusClass}">${statusText}</span></p>
                <p><strong>患者番号:</strong> ${booking.patient_number}</p>
                <p><strong>誕生日:</strong> ${formatDate(booking.birth_date)}</p>
                <p><strong>予約日:</strong> ${formatDate(booking.booking_date)}</p>
            </div>
            
            <div class="detail-section">
                <h4>日時情報</h4>
                <p><strong>作成日時:</strong> ${formatDateTime(booking.created_at)}</p>
                <p><strong>更新日時:</strong> ${formatDateTime(booking.updated_at)}</p>
            </div>
            
            ${booking.message ? `
                <div class="detail-section">
                    <h4>メッセージ</h4>
                    <p>${booking.message}</p>
                </div>
            ` : ''}
            
            ${booking.google_calendar_event_id ? `
                <div class="detail-section">
                    <h4>Googleカレンダー連携</h4>
                    <p><strong>イベントID:</strong> ${booking.google_calendar_event_id}</p>
                    ${booking.google_calendar_link ? `<p><a href="${booking.google_calendar_link}" target="_blank">カレンダーで確認</a></p>` : ''}
                </div>
            ` : ''}
        </div>
    `;
    
    // モーダルボタンの設定
    setupModalButtons(booking);
    
    // モーダルを表示
    modal.style.display = 'block';
}

/**
 * モーダルボタンの設定
 */
function setupModalButtons(booking) {
    const editBtn = document.getElementById('editBtn');
    const deleteBtn = document.getElementById('deleteBtn');
    const rebookBtn = document.getElementById('rebookBtn');
    
    if (editBtn) {
        editBtn.onclick = () => editBooking(booking.id);
    }
    
    if (deleteBtn) {
        deleteBtn.onclick = () => deleteBooking(booking.id);
    }
    
    if (rebookBtn) {
        rebookBtn.onclick = () => rebookPatient(booking.patient_number, booking.birth_date);
    }
}

/**
 * モーダルを閉じる
 */
function closeModal() {
    const modal = document.getElementById('bookingModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

/**
 * 統計情報の更新
 */
function updateStats(bookings) {
    const totalElement = document.getElementById('totalBookings');
    const successElement = document.getElementById('successBookings');
    const failedElement = document.getElementById('failedBookings');
    const calendarElement = document.getElementById('calendarLinked');
    
    if (totalElement && successElement && failedElement && calendarElement) {
        const total = bookings.length;
        const success = bookings.filter(b => b.status === 'success').length;
        const failed = bookings.filter(b => b.status === 'failed').length;
        const calendarLinked = bookings.filter(b => b.google_calendar_event_id).length;
        
        totalElement.textContent = total;
        successElement.textContent = success;
        failedElement.textContent = failed;
        calendarElement.textContent = calendarLinked;
    }
}

/**
 * フィルターの初期化
 */
function initializeFilters() {
    // 日付フィルターのデフォルト値を今日に設定
    const dateFilter = document.getElementById('dateFilter');
    if (dateFilter) {
        const today = new Date().toISOString().split('T')[0];
        dateFilter.value = today;
    }
}

/**
 * フィルターの適用
 */
function applyFilters() {
    loadBookingsWithFilters();
}

/**
 * フィルター付きで予約一覧を読み込み
 */
async function loadBookingsWithFilters() {
    const statusFilter = document.getElementById('statusFilter');
    const dateFilter = document.getElementById('dateFilter');
    
    const status = statusFilter ? statusFilter.value : '';
    const date = dateFilter ? dateFilter.value : '';
    
    try {
        let url = '/api/bookings';
        const params = new URLSearchParams();
        
        if (status) params.append('status', status);
        if (date) params.append('date', date);
        
        if (params.toString()) {
            url += '?' + params.toString();
        }
        
        const response = await fetch(url);
        const result = await response.json();
        
        if (result.success) {
            displayBookings(result.bookings);
            updateStats(result.bookings);
        }
    } catch (error) {
        console.error('フィルター適用エラー:', error);
    }
}

/**
 * フィルターのクリア
 */
function clearFilters() {
    const statusFilter = document.getElementById('statusFilter');
    const dateFilter = document.getElementById('dateFilter');
    
    if (statusFilter) statusFilter.value = '';
    if (dateFilter) dateFilter.value = '';
    
    loadBookings();
}

/**
 * 予約の編集（プレースホルダー）
 */
function editBooking(bookingId) {
    showNotification('編集機能は現在開発中です', 'info');
}

/**
 * 予約の削除
 */
async function deleteBooking(bookingId) {
    if (!confirm('この予約を削除しますか？')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/bookings/${bookingId}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (result.success) {
            showNotification('予約を削除しました', 'success');
            closeModal();
            loadBookings();
        } else {
            showNotification('予約の削除に失敗しました', 'error');
        }
    } catch (error) {
        console.error('予約削除エラー:', error);
        showNotification('予約の削除に失敗しました', 'error');
    }
}

/**
 * 患者の再予約
 */
function rebookPatient(patientNumber, birthDate) {
    const url = `/booking?patient_number=${patientNumber}&birth_date=${birthDate}`;
    window.location.href = url;
}

/**
 * ステータステキストの取得
 */
function getStatusText(status) {
    const statusMap = {
        'success': '成功',
        'failed': '失敗',
        'pending': '処理中'
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
