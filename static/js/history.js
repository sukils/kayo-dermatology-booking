// 予約管理アプリ - 予約履歴JavaScript

document.addEventListener('DOMContentLoaded', function() {
    console.log('予約履歴ページが読み込まれました');
    
    // 初期化
    initializeHistoryPage();
    
    // イベントリスナーの設定
    setupEventListeners();
    
    // 予約データの読み込み
    loadBookings();
});

/**
 * 予約履歴ページの初期化
 */
function initializeHistoryPage() {
    // 統計情報の初期化
    updateStats();
    
    // フィルターの初期化
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
    if (statusFilter) {
        statusFilter.addEventListener('change', applyFilters);
    }
    
    const dateFilter = document.getElementById('dateFilter');
    if (dateFilter) {
        dateFilter.addEventListener('change', applyFilters);
    }
    
    // クリアフィルターボタン
    const clearFilterBtn = document.getElementById('clearFilterBtn');
    if (clearFilterBtn) {
        clearFilterBtn.addEventListener('click', clearFilters);
    }
    
    // モーダルの閉じるボタン
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
 * 予約データの読み込み
 */
async function loadBookings() {
    try {
        const response = await fetch('/api/bookings');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        if (data.success) {
            displayBookings(data.bookings);
            updateStats(data.bookings);
        } else {
            showNotification('予約データの読み込みに失敗しました', 'error');
        }
        
    } catch (error) {
        console.error('予約データ読み込みエラー:', error);
        showNotification('予約データの読み込み中にエラーが発生しました', 'error');
    }
}

/**
 * 予約一覧の表示
 */
function displayBookings(bookings) {
    const bookingsList = document.getElementById('bookingsList');
    if (!bookingsList) return;
    
    if (!bookings || bookings.length === 0) {
        bookingsList.innerHTML = `
            <div class="no-bookings">
                <p>予約データがありません</p>
            </div>
        `;
        return;
    }
    
    const bookingsHTML = bookings.map(booking => createBookingCard(booking)).join('');
    bookingsList.innerHTML = bookingsHTML;
    
    // カードのイベントリスナーを設定
    setupBookingCardEvents();
}

/**
 * 予約カードの作成
 */
function createBookingCard(booking) {
    const statusClass = booking.status === 'success' ? 'success' : 'error';
    const statusIcon = booking.status === 'success' ? '✅' : '❌';
    const calendarIcon = booking.google_calendar_event_id ? '📅' : '📝';
    
    return `
        <div class="booking-card ${statusClass}" data-booking-id="${booking.id}">
            <div class="booking-header">
                <div class="booking-status">
                    <span class="status-icon">${statusIcon}</span>
                    <span class="status-text">${getStatusText(booking.status)}</span>
                </div>
                <div class="booking-date">
                    ${formatDate(booking.booking_date)}
                </div>
            </div>
            
            <div class="booking-content">
                <div class="patient-info">
                    <div class="info-item">
                        <strong>患者番号:</strong> ${booking.patient_number}
                    </div>
                    <div class="info-item">
                        <strong>誕生日:</strong> ${formatDate(booking.birth_date)}
                    </div>
                </div>
                
                <div class="booking-message">
                    ${booking.message || 'メッセージなし'}
                </div>
                
                <div class="calendar-info">
                    <span class="calendar-icon">${calendarIcon}</span>
                    ${booking.google_calendar_event_id ? 'Googleカレンダー連携済み' : 'カレンダー未連携'}
                </div>
            </div>
            
            <div class="booking-footer">
                <button class="btn btn-small btn-primary view-details-btn">
                    詳細表示
                </button>
                ${booking.google_calendar_event_id ? 
                    `<a href="${booking.google_calendar_link}" target="_blank" class="btn btn-small btn-secondary">カレンダー表示</a>` : 
                    ''
                }
            </div>
        </div>
    `;
}

/**
 * 予約カードのイベントリスナー設定
 */
function setupBookingCardEvents() {
    const viewButtons = document.querySelectorAll('.view-details-btn');
    viewButtons.forEach(button => {
        button.addEventListener('click', function() {
            const bookingCard = this.closest('.booking-card');
            const bookingId = bookingCard.dataset.bookingId;
            showBookingDetails(bookingId);
        });
    });
}

/**
 * 予約詳細の表示
 */
async function showBookingDetails(bookingId) {
    try {
        const response = await fetch(`/api/bookings/${bookingId}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        if (data.success) {
            displayBookingModal(data.booking);
        } else {
            showNotification('予約詳細の取得に失敗しました', 'error');
        }
        
    } catch (error) {
        console.error('予約詳細取得エラー:', error);
        showNotification('予約詳細の取得中にエラーが発生しました', 'error');
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
    
    // タイトルの設定
    modalTitle.textContent = `予約詳細 - ${formatDate(booking.booking_date)}`;
    
    // 内容の設定
    modalBody.innerHTML = `
        <div class="booking-details">
            <div class="detail-section">
                <h4>基本情報</h4>
                <div class="detail-grid">
                    <div class="detail-item">
                        <strong>予約ID:</strong> ${booking.id}
                    </div>
                    <div class="detail-item">
                        <strong>患者番号:</strong> ${booking.patient_number}
                    </div>
                    <div class="detail-item">
                        <strong>誕生日:</strong> ${formatDate(booking.birth_date)}
                    </div>
                    <div class="detail-item">
                        <strong>予約日:</strong> ${formatDate(booking.booking_date)}
                    </div>
                    <div class="detail-item">
                        <strong>ステータス:</strong> 
                        <span class="status-badge ${booking.status}">${getStatusText(booking.status)}</span>
                    </div>
                </div>
            </div>
            
            <div class="detail-section">
                <h4>メッセージ</h4>
                <p>${booking.message || 'メッセージなし'}</p>
            </div>
            
            <div class="detail-section">
                <h4>Googleカレンダー連携</h4>
                ${booking.google_calendar_event_id ? 
                    `<div class="calendar-linked">
                        <p>✅ カレンダー連携済み</p>
                        <p><strong>イベントID:</strong> ${booking.google_calendar_event_id}</p>
                        <a href="${booking.google_calendar_link}" target="_blank" class="btn btn-small btn-primary">
                            📅 カレンダーで表示
                        </a>
                    </div>` : 
                    '<p>❌ カレンダー未連携</p>'
                }
            </div>
            
            <div class="detail-section">
                <h4>タイムスタンプ</h4>
                <div class="detail-grid">
                    <div class="detail-item">
                        <strong>作成日時:</strong> ${formatDateTime(booking.created_at)}
                    </div>
                    <div class="detail-item">
                        <strong>更新日時:</strong> ${formatDateTime(booking.updated_at)}
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // モーダルを表示
    modal.style.display = 'block';
    
    // ボタンのイベントリスナーを設定
    setupModalButtons(booking);
}

/**
 * モーダルボタンのイベントリスナー設定
 */
function setupModalButtons(booking) {
    // 編集ボタン
    const editBtn = document.getElementById('editBtn');
    if (editBtn) {
        editBtn.addEventListener('click', () => editBooking(booking));
    }
    
    // 削除ボタン
    const deleteBtn = document.getElementById('deleteBtn');
    if (deleteBtn) {
        deleteBtn.addEventListener('click', () => deleteBooking(booking.id));
    }
    
    // 再予約ボタン
    const rebookBtn = document.getElementById('rebookBtn');
    if (rebookBtn) {
        rebookBtn.addEventListener('click', () => rebookPatient(booking));
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
function updateStats(bookings = []) {
    if (!bookings || bookings.length === 0) {
        // データがない場合は0を表示
        document.getElementById('totalBookings').textContent = '0';
        document.getElementById('successBookings').textContent = '0';
        document.getElementById('failedBookings').textContent = '0';
        document.getElementById('calendarLinked').textContent = '0';
        return;
    }
    
    const total = bookings.length;
    const success = bookings.filter(b => b.status === 'success').length;
    const failed = bookings.filter(b => b.status === 'failed').length;
    const calendarLinked = bookings.filter(b => b.google_calendar_event_id).length;
    
    document.getElementById('totalBookings').textContent = total;
    document.getElementById('successBookings').textContent = success;
    document.getElementById('failedBookings').textContent = failed;
    document.getElementById('calendarLinked').textContent = calendarLinked;
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
    const statusFilter = document.getElementById('statusFilter').value;
    const dateFilter = document.getElementById('dateFilter').value;
    
    // フィルター条件に基づいて予約データを再読み込み
    loadBookingsWithFilters(statusFilter, dateFilter);
}

/**
 * フィルター条件付きで予約データを読み込み
 */
async function loadBookingsWithFilters(status, date) {
    try {
        const params = new URLSearchParams();
        if (status) params.append('status', status);
        if (date) params.append('date', date);
        
        const response = await fetch(`/api/bookings?${params.toString()}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        if (data.success) {
            displayBookings(data.bookings);
            updateStats(data.bookings);
        }
        
    } catch (error) {
        console.error('フィルター適用エラー:', error);
        showNotification('フィルターの適用中にエラーが発生しました', 'error');
    }
}

/**
 * フィルターのクリア
 */
function clearFilters() {
    document.getElementById('statusFilter').value = '';
    document.getElementById('dateFilter').value = '';
    
    // 全データを再読み込み
    loadBookings();
}

/**
 * 予約の編集
 */
function editBooking(booking) {
    // 編集ページに遷移（実装予定）
    showNotification('編集機能は実装予定です', 'info');
}

/**
 * 予約の削除
 */
async function deleteBooking(bookingId) {
    if (!confirm('この予約を削除しますか？この操作は取り消せません。')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/bookings/${bookingId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        if (data.success) {
            showNotification('予約を削除しました', 'success');
            closeModal();
            loadBookings(); // 一覧を更新
        } else {
            showNotification('予約の削除に失敗しました', 'error');
        }
        
    } catch (error) {
        console.error('予約削除エラー:', error);
        showNotification('予約の削除中にエラーが発生しました', 'error');
    }
}

/**
 * 患者の再予約
 */
function rebookPatient(booking) {
    // 予約フォームページに遷移し、患者情報を事前入力
    const params = new URLSearchParams({
        patient_number: booking.patient_number,
        birth_date: booking.birth_date
    });
    
    window.location.href = `/booking?${params.toString()}`;
}

/**
 * ステータステキストの取得
 */
function getStatusText(status) {
    switch (status) {
        case 'success':
            return '成功';
        case 'failed':
            return '失敗';
        default:
            return status;
    }
}

/**
 * 日付のフォーマット
 */
function formatDate(dateString) {
    if (!dateString) return '不明';
    
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
    if (!dateTimeString) return '不明';
    
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
    // グローバル関数が利用可能な場合
    if (window.showNotification) {
        window.showNotification(message, type);
    } else {
        // フォールバック
        alert(message);
    }
}
