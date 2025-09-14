/**
 * 予約フォーム用のJavaScript
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('予約フォームが読み込まれました');
    initializeBookingForm();
});

/**
 * 予約フォームの初期化
 */
function initializeBookingForm() {
    console.log('予約フォームの初期化を開始');
    
    const form = document.getElementById('bookingForm');
    const submitBtn = document.getElementById('submitBtn');
    const statusDiv = document.getElementById('bookingStatus');
    const statusMessage = document.getElementById('statusMessage');
    
    console.log('フォーム要素:', form);
    console.log('送信ボタン:', submitBtn);
    console.log('ステータス要素:', statusDiv);
    console.log('メッセージ要素:', statusMessage);
    
    if (!form) {
        console.error('フォームが見つかりません');
        return;
    }
    
    if (!submitBtn) {
        console.error('送信ボタンが見つかりません');
        return;
    }
    
    // フォーム送信イベント
    form.addEventListener('submit', function(e) {
        console.log('フォーム送信イベントが発生');
        e.preventDefault();
        handleBookingSubmission();
    });
    
    // 送信ボタンのクリックイベントも追加
    submitBtn.addEventListener('click', function(e) {
        console.log('送信ボタンがクリックされました');
        e.preventDefault();
        handleBookingSubmission();
    });
    
    // 入力値の検証設定
    setupValidation();
    
    // URLパラメータから患者情報を事前入力
    prefillPatientInfo();
    
    // 現在の日付と受付状況を表示
    updateCurrentInfo();
    
    console.log('予約フォームの初期化が完了');
}

/**
 * 予約送信の処理
 */
async function handleBookingSubmission() {
    console.log('予約送信処理を開始');
    
    const form = document.getElementById('bookingForm');
    const submitBtn = document.getElementById('submitBtn');
    const statusDiv = document.getElementById('bookingStatus');
    const statusMessage = document.getElementById('statusMessage');
    
    // フォームデータの取得
    const formData = new FormData(form);
    const bookingDate = formData.get('booking_date');
    const patientNumber = formData.get('patient_number');
    const birthDate = formData.get('birth_date');
    const bookingTime = formData.get('booking_time');
    
    console.log('フォームデータ:', {
        bookingDate,
        patientNumber,
        birthDate,
        bookingTime
    });
    
    // 入力値の検証
    if (!validateInputs(bookingDate, patientNumber, birthDate)) {
        console.log('入力値の検証に失敗');
        return;
    }
    
    console.log('入力値の検証が完了');
    
    // 送信ボタンを無効化
    submitBtn.disabled = true;
    submitBtn.textContent = '予約処理中...';
    
    // ステータス表示をクリア
    statusDiv.style.display = 'block';
    statusMessage.innerHTML = '<div class="loading">🔄 予約処理中...</div>';
    
    try {
        // APIに送信するデータを構築
        const requestData = {
            booking_date: bookingDate,
            patient_number: patientNumber,
            birth_date: birthDate,
            booking_time: bookingTime
        };
        
        console.log('APIに送信するデータ:', requestData);
        
        // APIに予約リクエストを送信
        const response = await fetch('/api/booking', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestData)
        });
        
        console.log('APIレスポンス:', response);
        console.log('レスポンスステータス:', response.status);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        console.log('APIレスポンス結果:', result);
        
        if (result.success) {
            // 予約成功
            const bookingId = result.booking_id;
            const message = result.message;
            
            statusMessage.innerHTML = `
                <div class="success-message">
                    <h3>🎉 予約完了！</h3>
                    <p><strong>予約番号:</strong> <span class="booking-id">${bookingId}</span></p>
                    <p><strong>メッセージ:</strong> ${message}</p>
                    <p><strong>予約日:</strong> ${formatDate(bookingDate)}</p>
                    <p><strong>患者番号:</strong> ${patientNumber}</p>
                    <p><strong>誕生日:</strong> ${formatDate(birthDate)}</p>
                    <p><strong>予約日時:</strong> ${new Date().toLocaleString('ja-JP')}</p>
                    <div class="success-actions">
                        <a href="/history" class="btn btn-secondary">📋 予約履歴を確認</a>
                        <button onclick="resetForm()" class="btn btn-primary">🔄 新規予約</button>
                    </div>
                </div>
            `;
            
            // フォームをリセット
            form.reset();
            
            // 成功通知
            showNotification('予約が完了しました！', 'success');
            
        } else {
            // 予約失敗
            statusMessage.innerHTML = `
                <div class="error-message">
                    <h3>❌ 予約失敗</h3>
                    <p><strong>エラー:</strong> ${result.message}</p>
                    ${result.booking_data ? `
                        <p><strong>予約日:</strong> ${formatDate(result.booking_data.booking_date)}</p>
                        <p><strong>患者番号:</strong> ${result.booking_data.patient_number}</p>
                        <p><strong>誕生日:</strong> ${formatDate(result.booking_data.birth_date)}</p>
                    ` : ''}
                    <div class="error-actions">
                        <button onclick="retrySubmission()" class="btn btn-primary">🔄 再試行</button>
                        <button onclick="resetForm()" class="btn btn-secondary">📝 フォームリセット</button>
                    </div>
                </div>
            `;
            
            // エラー通知
            showNotification('予約に失敗しました', 'error');
        }
        
    } catch (error) {
        console.error('予約処理エラー:', error);
        statusMessage.innerHTML = `
            <div class="error-message">
                <h3>❌ システムエラー</h3>
                <p>予約処理中にエラーが発生しました。</p>
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
        submitBtn.textContent = '🚀 予約実行';
    }
}

/**
 * 入力値の検証
 */
function validateInputs(bookingDate, patientNumber, birthDate) {
    // 予約日の検証
    if (!bookingDate) {
        showNotification('予約希望日を選択してください', 'error');
        return false;
    }
    
    const selectedDate = new Date(bookingDate);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    
    if (selectedDate < today) {
        showNotification('予約日は今日以降の日付を選択してください', 'error');
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
    console.log('入力値の検証設定を開始');
    
    const patientNumberInput = document.getElementById('patient_number');
    const birthDateInput = document.getElementById('birth_date');
    const bookingDateInput = document.getElementById('booking_date');
    
    console.log('日付フィールド要素:', {
        bookingDateInput,
        birthDateInput
    });
    
    if (!bookingDateInput) {
        console.error('予約日フィールドが見つかりません');
        return;
    }
    
    if (!birthDateInput) {
        console.error('誕生日フィールドが見つかりません');
        return;
    }
    
    // 患者番号の入力制限（数字のみ）
    if (patientNumberInput) {
        patientNumberInput.addEventListener('input', function(e) {
            this.value = this.value.replace(/[^0-9]/g, '');
        });
    }
    
    // 予約日の最小値を今日に設定
    const today = new Date();
    const todayString = today.toISOString().split('T')[0];
    console.log('今日の日付:', todayString);
    
    bookingDateInput.min = todayString;
    console.log('予約日の最小値設定:', bookingDateInput.min);
    
    // 予約日の初期値を明日に設定
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);
    const tomorrowString = tomorrow.toISOString().split('T')[0];
    bookingDateInput.value = tomorrowString;
    console.log('予約日の初期値設定:', tomorrowString);
    
    // 誕生日の最大値を今日に設定
    birthDateInput.max = todayString;
    console.log('誕生日の最大値設定:', birthDateInput.max);
    
    // 誕生日の初期値を設定（例：1990年1月1日）
    const defaultBirthDate = '1990-01-01';
    birthDateInput.value = defaultBirthDate;
    console.log('誕生日の初期値設定:', defaultBirthDate);
    
    // 日付フィールドの属性を確認
    console.log('予約日フィールドの属性:', {
        type: bookingDateInput.type,
        min: bookingDateInput.min,
        max: bookingDateInput.max,
        required: bookingDateInput.required,
        value: bookingDateInput.value
    });
    
    console.log('誕生日フィールドの属性:', {
        type: birthDateInput.type,
        min: birthDateInput.min,
        max: birthDateInput.max,
        required: birthDateInput.required,
        value: birthDateInput.value
    });
    
    console.log('入力値の検証設定が完了');
}

/**
 * URLパラメータから患者情報を事前入力
 */
function prefillPatientInfo() {
    const urlParams = new URLSearchParams(window.location.search);
    const patientNumber = urlParams.get('patient_number');
    const birthDate = urlParams.get('birth_date');
    
    if (patientNumber) {
        const patientNumberInput = document.getElementById('patient_number');
        if (patientNumberInput) {
            patientNumberInput.value = patientNumber;
        }
    }
    
    if (birthDate) {
        const birthDateInput = document.getElementById('birth_date');
        if (birthDateInput) {
            birthDateInput.value = birthDate;
        }
    }
    
    if (patientNumber || birthDate) {
        console.log('患者情報が事前入力されました:', { patientNumber, birthDate });
    }
}

/**
 * 現在の情報を更新
 */
function updateCurrentInfo() {
    // 現在の日付を表示
    const currentDateElement = document.getElementById('currentDate');
    if (currentDateElement) {
        const now = new Date();
        currentDateElement.textContent = now.toLocaleDateString('ja-JP', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            weekday: 'long'
        });
    }
    
    // 受付状況を確認
    checkReceptionStatus();
    checkWebReceptionStatus();
}

/**
 * 受付状況を確認
 */
function checkReceptionStatus() {
    const statusElement = document.getElementById('receptionStatus');
    if (!statusElement) return;
    
    const now = new Date();
    const hour = now.getHours();
    const minute = now.getMinutes();
    const currentTime = hour * 60 + minute;
    const receptionStart = 9 * 60 + 15; // 09:15
    
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

/**
 * Web予約受付状況を確認
 */
function checkWebReceptionStatus() {
    const statusElement = document.getElementById('webReceptionStatus');
    if (!statusElement) return;
    
    const now = new Date();
    const weekday = now.getDay(); // 0=日曜日, 1=月曜日, ...
    const hour = now.getHours();
    
    if (weekday === 0) { // 日曜日
        statusElement.textContent = '❌ 休診日';
        statusElement.className = 'status-indicator closed';
    } else if (weekday === 6) { // 土曜日
        if (hour < 12) {
            statusElement.textContent = '🟢 Web予約受付中（12:00まで）';
            statusElement.className = 'status-indicator open';
        } else {
            statusElement.textContent = '❌ Web予約受付終了';
            statusElement.className = 'status-indicator closed';
        }
    } else { // 平日（月〜金）
        if (hour >= 12 && hour < 16) {
            statusElement.textContent = '🟢 Web予約受付中（12:00-16:00）';
            statusElement.className = 'status-indicator open';
        } else if (hour < 12) {
            statusElement.textContent = '⏰ Web予約受付開始まで待機中（12:00開始）';
            statusElement.className = 'status-indicator waiting';
        } else {
            statusElement.textContent = '❌ Web予約受付終了（16:00まで）';
            statusElement.className = 'status-indicator closed';
        }
    }
}

/**
 * 再試行
 */
function retrySubmission() {
    const statusDiv = document.getElementById('bookingStatus');
    statusDiv.style.display = 'none';
    
    // フォーカスを送信ボタンに移動
    document.getElementById('submitBtn').focus();
}

/**
 * フォームをリセット
 */
function resetForm() {
    const form = document.getElementById('bookingForm');
    const statusDiv = document.getElementById('bookingStatus');
    
    form.reset();
    statusDiv.style.display = 'none';
    
    // 日付フィールドを再初期化
    setupValidation();
    
    // フォーカスを予約希望日フィールドに移動
    document.getElementById('booking_date').focus();
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
