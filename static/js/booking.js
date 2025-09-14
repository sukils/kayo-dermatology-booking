// 予約管理アプリ - 予約フォームJavaScript

document.addEventListener('DOMContentLoaded', function() {
    console.log('予約フォームが読み込まれました');
    
    // フォームの初期化
    initializeBookingForm();
    
    // イベントリスナーの設定
    setupFormEventListeners();
    
    // フォームの検証設定
    setupFormValidation();
});

/**
 * 予約フォームの初期化
 */
function initializeBookingForm() {
    // 誕生日のデフォルト値を今日に設定
    const birthDateInput = document.getElementById('birth_date');
    if (birthDateInput) {
        const today = new Date();
        const formattedDate = today.toISOString().split('T')[0];
        birthDateInput.value = formattedDate;
    }
    
    // 患者番号のフォーカス
    const patientNumberInput = document.getElementById('patient_number');
    if (patientNumberInput) {
        patientNumberInput.focus();
    }
    
    // 受付時間のチェック
    checkCurrentBookingAvailability();
    
    // URLパラメータから患者情報を事前入力
    prefillPatientInfo();
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
    
    // 事前入力された場合は、フォームの状態を更新
    if (patientNumber || birthDate) {
        console.log('患者情報が事前入力されました:', { patientNumber, birthDate });
    }
}

/**
 * フォームイベントリスナーの設定
 */
function setupFormEventListeners() {
    const form = document.getElementById('bookingForm');
    if (form) {
        form.addEventListener('submit', handleFormSubmit);
    }
    
    // 入力フィールドのリアルタイム検証
    const patientNumberInput = document.getElementById('patient_number');
    if (patientNumberInput) {
        patientNumberInput.addEventListener('input', validatePatientNumber);
        patientNumberInput.addEventListener('blur', validatePatientNumber);
    }
    
    const birthDateInput = document.getElementById('birth_date');
    if (birthDateInput) {
        birthDateInput.addEventListener('change', validateBirthDate);
        birthDateInput.addEventListener('blur', validateBirthDate);
    }
}

/**
 * フォーム検証の設定
 */
function setupFormValidation() {
    // 患者番号の検証
    const patientNumberInput = document.getElementById('patient_number');
    if (patientNumberInput) {
        patientNumberInput.setAttribute('pattern', '[0-9]+');
        patientNumberInput.setAttribute('title', '患者番号は数字のみ入力してください');
    }
    
    // 誕生日の検証
    const birthDateInput = document.getElementById('birth_date');
    if (birthDateInput) {
        const today = new Date();
        const maxDate = new Date(today.getFullYear() + 1, today.getMonth(), today.getDate());
        birthDateInput.setAttribute('max', maxDate.toISOString().split('T')[0]);
    }
}

/**
 * フォーム送信の処理
 */
async function handleFormSubmit(event) {
    event.preventDefault();
    
    console.log('予約フォームが送信されました');
    
    // フォームデータの取得
    const formData = getFormData();
    
    // フォームデータの検証
    if (!validateFormData(formData)) {
        return;
    }
    
    // 送信ボタンの無効化
    const submitButton = document.querySelector('button[type="submit"]');
    if (submitButton) {
        submitButton.disabled = true;
        submitButton.textContent = '🔄 予約処理中...';
    }
    
    // 予約状況の表示
    showBookingStatus('processing', '予約処理中', '予約システムに接続しています...');
    
    try {
        // APIに予約リクエストを送信
        const response = await executeBooking(formData);
        
        if (response.success) {
            // 成功時の処理
            showBookingStatus('success', '予約完了！', response.message, response.details || '');
            showSuccess('予約が完了しました！');
            
            // フォームのリセット
            resetForm();
            
            // 自動ページ遷移は削除（通知モーダルで操作させる）
            
        } else {
            // 失敗時の処理
            showBookingStatus('error', '予約失敗', response.message);
            showNotification(response.message, 'error');
        }
        
    } catch (error) {
        // エラー時の処理
        console.error('予約処理エラー:', error);
        showBookingStatus('error', 'エラーが発生', '予約処理中にエラーが発生しました。再度お試しください。');
        handleError(error, '予約処理');
        
    } finally {
        // 送信ボタンの再有効化
        if (submitButton) {
            submitButton.disabled = false;
            submitButton.textContent = '🚀 予約を実行';
        }
    }
}

/**
 * フォームデータの取得
 */
function getFormData() {
    const patientNumber = document.getElementById('patient_number').value.trim();
    const birthDate = document.getElementById('birth_date').value;
    const bookingTime = document.getElementById('booking_time').value;
    
    return {
        patient_number: patientNumber,
        birth_date: birthDate,
        booking_time: bookingTime
    };
}

/**
 * フォームデータの検証
 */
function validateFormData(data) {
    // 患者番号の検証
    if (!data.patient_number) {
        showNotification('患者番号を入力してください', 'error');
        document.getElementById('patient_number').focus();
        return false;
    }
    
    if (!/^\d+$/.test(data.patient_number)) {
        showNotification('患者番号は数字のみ入力してください', 'error');
        document.getElementById('patient_number').focus();
        return false;
    }
    
    // 誕生日の検証
    if (!data.birth_date) {
        showNotification('誕生日を選択してください', 'error');
        document.getElementById('birth_date').focus();
        return false;
    }
    
    const selectedDate = new Date(data.birth_date);
    const today = new Date();
    
    if (selectedDate > today) {
        showNotification('誕生日は今日以前の日付を選択してください', 'error');
        document.getElementById('birth_date').focus();
        return false;
    }
    
    return true;
}

/**
 * 患者番号の検証
 */
function validatePatientNumber() {
    const input = this;
    const value = input.value.trim();
    
    if (value && !/^\d+$/.test(value)) {
        input.setCustomValidity('患者番号は数字のみ入力してください');
        input.classList.add('invalid');
    } else {
        input.setCustomValidity('');
        input.classList.remove('invalid');
    }
}

/**
 * 誕生日の検証
 */
function validateBirthDate() {
    const input = this;
    const value = input.value;
    
    if (value) {
        const selectedDate = new Date(value);
        const today = new Date();
        
        if (selectedDate > today) {
            input.setCustomValidity('誕生日は今日以前の日付を選択してください');
            input.classList.add('invalid');
        } else {
            input.setCustomValidity('');
            input.classList.remove('invalid');
        }
    }
}

/**
 * 予約の実行
 */
async function executeBooking(formData) {
    const response = await fetch('/api/booking', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData)
    });
    
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return await response.json();
}

/**
 * 予約状況の表示
 */
function showBookingStatus(type, title, message, details = '') {
    const statusElement = document.getElementById('bookingStatus');
    if (!statusElement) return;
    
    // 既存のクラスをクリア
    statusElement.className = 'booking-status';
    
    // 新しいクラスを追加
    statusElement.classList.add(type);
    
    // 内容を更新
    const statusIcon = document.getElementById('statusIcon');
    const statusTitle = document.getElementById('statusTitle');
    const statusMessage = document.getElementById('statusMessage');
    const statusDetails = document.getElementById('statusDetails');
    
    if (statusIcon) {
        statusIcon.textContent = getStatusIcon(type);
    }
    
    if (statusTitle) {
        statusTitle.textContent = title;
    }
    
    if (statusMessage) {
        statusMessage.textContent = message;
    }
    
    if (statusDetails && details) {
        statusDetails.innerHTML = details;
    }
    
    // 表示
    statusElement.style.display = 'block';
    
    // スクロールして表示
    statusElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
    
    // 成功時は特別な通知を表示
    if (type === 'success') {
        showSuccessNotification(title, message, details);
    }
}

/**
 * ステータスアイコンの取得
 */
function getStatusIcon(type) {
    switch (type) {
        case 'success':
            return '✅';
        case 'error':
            return '❌';
        case 'processing':
            return '🔄';
        default:
            return 'ℹ️';
    }
}

/**
 * フォームのリセット
 */
function resetForm() {
    const form = document.getElementById('bookingForm');
    if (form) {
        form.reset();
        
        // 誕生日を今日に設定
        const birthDateInput = document.getElementById('birth_date');
        if (birthDateInput) {
            const today = new Date();
            const formattedDate = today.toISOString().split('T')[0];
            birthDateInput.value = formattedDate;
        }
    }
}

/**
 * 現在の予約受付可能時間のチェック
 */
function checkCurrentBookingAvailability() {
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
    let message = '';
    
    if (currentTime >= morningStart && currentTime < morningEnd) {
        isAvailable = true;
        message = '午前受付中です';
    } else if (currentTime >= afternoonStart && currentTime < afternoonEnd) {
        isAvailable = true;
        message = '午後受付中です';
    } else if (currentTime < morningStart) {
        message = `次回受付開始: ${Math.floor(morningStart / 60)}:${String(morningStart % 60).padStart(2, '0')}`;
    } else if (currentTime >= morningEnd && currentTime < afternoonStart) {
        message = `次回受付開始: ${Math.floor(afternoonStart / 60)}:${String(afternoonStart % 60).padStart(2, '0')}`;
    } else {
        message = '本日の受付は終了しました';
    }
    
    // 受付状況の表示
    updateFormAvailabilityStatus(isAvailable, message);
}

/**
 * フォームの受付状況表示を更新
 */
function updateFormAvailabilityStatus(isAvailable, message) {
    // 受付状況表示要素があれば更新
    const statusElement = document.getElementById('form-availability-status');
    if (statusElement) {
        statusElement.textContent = message;
        statusElement.className = isAvailable ? 'status-available' : 'status-unavailable';
    }
    
    // 予約実行ボタンの状態を更新
    const submitButton = document.querySelector('button[type="submit"]');
    if (submitButton) {
        if (isAvailable) {
            submitButton.disabled = false;
            submitButton.style.opacity = '1';
            submitButton.style.cursor = 'pointer';
        } else {
            submitButton.disabled = true;
            submitButton.style.opacity = '0.6';
            submitButton.style.cursor = 'not-allowed';
        }
    }
}

/**
 * 入力フィールドのリアルタイム検証
 */
function setupRealTimeValidation() {
    const inputs = document.querySelectorAll('.form-input, .form-select');
    
    inputs.forEach(input => {
        input.addEventListener('input', function() {
            this.classList.remove('invalid');
        });
        
        input.addEventListener('blur', function() {
            validateField(this);
        });
    });
}

/**
 * 個別フィールドの検証
 */
function validateField(field) {
    const value = field.value.trim();
    
    if (field.hasAttribute('required') && !value) {
        field.classList.add('invalid');
        return false;
    }
    
    if (field.id === 'patient_number' && value && !/^\d+$/.test(value)) {
        field.classList.add('invalid');
        return false;
    }
    
    field.classList.remove('invalid');
    return true;
}

/**
 * 成功通知の表示（予約番号を強調表示）
 */
function showSuccessNotification(title, message, details = '') {
    // ブラウザ通知の許可を確認
    if (Notification.permission === 'granted') {
        showBrowserNotification(title, message);
    } else if (Notification.permission !== 'denied') {
        Notification.requestPermission().then(permission => {
            if (permission === 'granted') {
                showBrowserNotification(title, message);
            }
        });
    }
    
    // 画面中央に大きな成功通知を表示
    showModalNotification(title, message, details);
    
    // 音声通知（可能な場合）
    playSuccessSound();
}

/**
 * ブラウザ通知の表示
 */
function showBrowserNotification(title, message) {
    try {
        const notification = new Notification(title, {
            body: message,
            icon: '/static/images/notification-icon.png', // アイコンがあれば
            badge: '/static/images/badge-icon.png', // バッジがあれば
            tag: 'booking-success',
            requireInteraction: true, // ユーザーが操作するまで表示
            actions: [
                {
                    action: 'view',
                    title: '詳細を見る'
                },
                {
                    action: 'close',
                    title: '閉じる'
                }
            ]
        });
        
        // 通知のクリックイベント
        notification.onclick = function() {
            window.focus();
            notification.close();
        };
        
        // 通知のアクションイベント
        notification.onaction = function(event) {
            if (event.action === 'view') {
                window.focus();
                // 予約履歴ページに移動
                window.location.href = '/history';
            }
            notification.close();
        };
        
        // 5秒後に自動で閉じる
        setTimeout(() => {
            notification.close();
        }, 5000);
        
    } catch (error) {
        console.error('ブラウザ通知エラー:', error);
    }
}

/**
 * モーダル通知の表示
 */
function showModalNotification(title, message, details = '') {
    // 既存のモーダルがあれば削除
    const existingModal = document.getElementById('successModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // モーダル要素を作成
    const modal = document.createElement('div');
    modal.id = 'successModal';
    modal.className = 'success-modal-overlay';
    
    // 予約番号を抽出（detailsから）
    let bookingNumber = '';
    if (details) {
        const match = details.match(/予約番号[：:]\s*(\d+)/);
        if (match) {
            bookingNumber = match[1];
        }
    }
    
    modal.innerHTML = `
        <div class="success-modal">
            <div class="success-modal-header">
                <h2>🎉 ${title}</h2>
                <button class="modal-close-btn" onclick="closeSuccessModal()">&times;</button>
            </div>
            <div class="success-modal-body">
                <div class="success-icon">✅</div>
                <p class="success-message">${message}</p>
                ${details ? `<div class="success-details">${details}</div>` : ''}
                ${bookingNumber ? `
                    <div class="booking-number-highlight">
                        <span class="label">予約番号</span>
                        <span class="number">${bookingNumber}</span>
                    </div>
                ` : ''}
            </div>
            <div class="success-modal-footer">
                <button class="btn btn-secondary" onclick="goToHistory()">📋 予約履歴を確認</button>
                <button class="btn btn-primary" onclick="closeSuccessModal()">🔄 新規予約</button>
            </div>
        </div>
    `;
    
    // ページに追加
    document.body.appendChild(modal);
    
    // アニメーション効果
    setTimeout(() => {
        modal.classList.add('show');
    }, 100);
    
    // 10秒後に自動で閉じる
    setTimeout(() => {
        if (modal.parentNode) {
            closeSuccessModal();
        }
    }, 10000);
}

/**
 * 成功通知モーダルを閉じる
 */
function closeSuccessModal() {
    const modal = document.getElementById('successModal');
    if (modal) {
        modal.classList.remove('show');
        setTimeout(() => {
            if (modal.parentNode) {
                modal.remove();
            }
        }, 300);
    }
}

/**
 * 予約履歴ページに移動
 */
function goToHistory() {
    window.location.href = '/history';
}

/**
 * 成功音の再生
 */
function playSuccessSound() {
    try {
        // Web Audio APIを使用して成功音を生成
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);
        
        // 成功音の設定（2つの音を連続で再生）
        oscillator.frequency.setValueAtTime(800, audioContext.currentTime);
        oscillator.frequency.setValueAtTime(1000, audioContext.currentTime + 0.1);
        
        gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.3);
        
        oscillator.start(audioContext.currentTime);
        oscillator.stop(audioContext.currentTime + 0.3);
        
    } catch (error) {
        console.error('音声再生エラー:', error);
    }
}

// グローバル関数として公開
window.showBookingStatus = showBookingStatus;
window.resetForm = resetForm;
