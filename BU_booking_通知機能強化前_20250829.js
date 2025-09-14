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
            showBookingStatus('success', '予約完了！', response.message);
            showSuccess('予約が完了しました！');
            
            // フォームのリセット
            resetForm();
            
            // 3秒後にメインページに戻る
            setTimeout(() => {
                window.location.href = '/';
            }, 3000);
            
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
        statusDetails.textContent = details;
    }
    
    // 表示
    statusElement.style.display = 'block';
    
    // スクロールして表示
    statusElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
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

// グローバル関数として公開
window.showBookingStatus = showBookingStatus;
window.resetForm = resetForm;
