// static/scripts/profile/settings.js

document.addEventListener('DOMContentLoaded', function() {
  // --- КОД ДЛЯ ТАБОВ --- (остается без изменений)
  const tabButtons = document.querySelectorAll('.tab-button');
  const tabContents = document.querySelectorAll('.tab-content');
  if (tabButtons.length > 0 && tabContents.length > 0) {
    tabButtons.forEach(button => {
      button.addEventListener('click', () => {
        tabButtons.forEach(btn => btn.classList.remove('active-tab'));
        tabContents.forEach(content => content.classList.remove('active-content'));
        button.classList.add('active-tab');
        const targetTabId = button.getAttribute('data-tab-target');
        const targetTabContent = document.querySelector(targetTabId);
        if (targetTabContent) {
          targetTabContent.classList.add('active-content');
        }
      });
    });
  }

  // --- КОД ДЛЯ КАСТОМНОГО МОДАЛЬНОГО ОКНА EMAIL ---
  const triggerChangeEmailButton = document.getElementById('triggerChangeEmailModal');
  const changeEmailModalOverlay = document.getElementById('changeEmailModalOverlay');
  const changeEmailModalItself = document.getElementById('changeEmailModal');
  const modalBackButton = document.getElementById('modalBackButton');

  const emailStep1 = document.getElementById('emailStep1');
  const emailStep2 = document.getElementById('emailStep2');

  const newEmailForm = document.getElementById('newEmailForm');
  const verifyEmailCodeForm = document.getElementById('verifyEmailCodeForm');
  const sendVerificationCodeBtn = document.getElementById('sendVerificationCodeBtn');
  const submitVerificationCodeBtn = document.getElementById('submitVerificationCodeBtn');
  
  const newEmailInput = document.getElementById('new_email_input');
  const verificationCodeInput = document.getElementById('verification_code_input');
  
  const alertContainer = document.getElementById('emailChangeAlertContainer');
  const currentEmailDisplay = document.getElementById('current_email_display'); // Отображение текущего email на странице
  const sentToEmailDisplay = document.getElementById('sentToEmailDisplay'); // Куда отправлен код (в модалке)
  const hiddenNewEmailForVerification = document.getElementById('hidden_new_email_for_verification');
  const emailToVerifyPlaceholder = document.getElementById('emailToVerifyPlaceholder'); // Для текста на первом шаге

  const resendCodeLink = document.getElementById('resendCodeLink');


  function showStep(stepToShow) {
    if (stepToShow === 1) {
      if(emailStep1) emailStep1.classList.remove('is-hidden');
      if(emailStep2) emailStep2.classList.add('is-hidden');
      if(modalBackButton) modalBackButton.classList.add('is-hidden');
      if(newEmailInput) newEmailInput.focus();
      if(emailToVerifyPlaceholder && currentEmailDisplay) { // Обновляем плейсхолдер на первом шаге
        emailToVerifyPlaceholder.textContent = currentEmailDisplay.value;
      }
    } else if (stepToShow === 2) {
      if(emailStep1) emailStep1.classList.add('is-hidden');
      if(emailStep2) emailStep2.classList.remove('is-hidden');
      if(modalBackButton) modalBackButton.classList.remove('is-hidden');
      if(verificationCodeInput) verificationCodeInput.focus();
    }
    showAlert(''); // Очищаем алерты при смене шага
  }

  function openChangeEmailModal() {
    if (changeEmailModalOverlay) {
      showStep(1); // Всегда начинаем с первого шага
      changeEmailModalOverlay.classList.remove('is-hidden');
      changeEmailModalOverlay.classList.add('is-visible');
      document.body.classList.add('modal-open-custom');
      console.log('Custom Email Modal: Opened');
    }
  }

  function closeChangeEmailModal() {
    if (changeEmailModalOverlay) {
      changeEmailModalOverlay.classList.remove('is-visible');
      document.body.classList.remove('modal-open-custom');
      console.log('Custom Email Modal: Closed');

      // Сброс форм и возврат к первому шагу при закрытии
      if(newEmailForm) newEmailForm.reset();
      if(verifyEmailCodeForm) verifyEmailCodeForm.reset();
      showStep(1); // Убедимся, что при следующем открытии будет первый шаг
      showAlert('');
    }
  }

  if (triggerChangeEmailButton) {
    triggerChangeEmailButton.addEventListener('click', openChangeEmailModal);
  }

  if (modalBackButton) {
    modalBackButton.addEventListener('click', () => {
      showStep(1);
    });
  }

  if (changeEmailModalOverlay && changeEmailModalItself) {
    changeEmailModalOverlay.addEventListener('click', function(event) {
      if (event.target === changeEmailModalOverlay) {
        closeChangeEmailModal();
      }
    });
  }

  document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape' && changeEmailModalOverlay && changeEmailModalOverlay.classList.contains('is-visible')) {
      closeChangeEmailModal();
    }
  });

  function showAlert(message, type = 'danger') {
    if (alertContainer) {
        alertContainer.innerHTML = ''; // Очищаем предыдущие
        if (message) { // Показываем только если есть сообщение
            const alertDiv = document.createElement('div');
            alertDiv.className = `custom-alert custom-alert-${type}`;
            alertDiv.textContent = message;
            
            // Можно добавить кнопку закрытия для алерта, если нужно
            // const closeButton = document.createElement('button');
            // closeButton.className = 'custom-alert-close';
            // closeButton.innerHTML = '×';
            // closeButton.onclick = () => alertDiv.remove();
            // alertDiv.appendChild(closeButton);
            
            alertContainer.appendChild(alertDiv);
        }
    } else {
        console.warn('Custom Email Modal: Alert container not found.');
    }
  }

  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
  }
  const csrftoken = getCookie('csrftoken');

  const sendCodeUrl = newEmailForm ? newEmailForm.dataset.sendCodeUrl : null;
  const verifyUrl = verifyEmailCodeForm ? verifyEmailCodeForm.dataset.verifyUrl : null;

  // --- Обработка формы отправки email (Шаг 1) ---
  if (newEmailForm && sendCodeUrl) {
      newEmailForm.addEventListener('submit', function (event) {
          event.preventDefault();
          showAlert(''); // Очищаем предыдущие ошибки
          const newEmail = newEmailInput.value;
          
          // Простая валидация email на клиенте (можно улучшить)
          if (!newEmail || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(newEmail)) {
              showAlert('Please enter a valid email address.', 'danger');
              newEmailInput.focus();
              return;
          }

          sendVerificationCodeBtn.disabled = true;
          sendVerificationCodeBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Continuing...';
          
          fetch(sendCodeUrl, {
              method: 'POST',
              headers: {
                  'Content-Type': 'application/x-www-form-urlencoded',
                  'X-CSRFToken': csrftoken
              },
              body: new URLSearchParams({'new_email': newEmail})
          })
          .then(response => response.json())
          .then(data => {
              if (data.status === 'success') {
                  // showAlert(data.message, 'success'); // Можно не показывать сообщение, а сразу переходить
                  if(sentToEmailDisplay) sentToEmailDisplay.textContent = newEmail;
                  if(hiddenNewEmailForVerification) hiddenNewEmailForVerification.value = newEmail;
                  showStep(2); // Переключаемся на второй шаг
              } else {
                  showAlert(data.message || 'Could not send verification code. Please try again.', 'danger');
              }
          })
          .catch(error => {
              console.error('Custom Email Modal: Error sending verification code:', error);
              showAlert('An error occurred. Please try again.', 'danger');
          })
          .finally(() => {
              sendVerificationCodeBtn.disabled = false;
              sendVerificationCodeBtn.innerHTML = 'Continue';
          });
      });
  }

  // --- Обработка формы верификации кода (Шаг 2) ---
  if (verifyEmailCodeForm && verifyUrl) {
      verifyEmailCodeForm.addEventListener('submit', function (event) {
          event.preventDefault();
          showAlert(''); // Очищаем предыдущие ошибки
          const verificationCode = verificationCodeInput.value;
          const emailForVerification = hiddenNewEmailForVerification.value;

          if (!verificationCode || verificationCode.length !== 6) {
              showAlert('Please enter a 6-digit verification code.', 'danger');
              verificationCodeInput.focus();
              return;
          }

          submitVerificationCodeBtn.disabled = true;
          submitVerificationCodeBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Verifying...';
          
          fetch(verifyUrl, {
              method: 'POST',
              headers: {
                  'Content-Type': 'application/x-www-form-urlencoded',
                  'X-CSRFToken': csrftoken
              },
              body: new URLSearchParams({
                  'verification_code': verificationCode,
                  'new_email': emailForVerification
              })
          })
          .then(response => response.json())
          .then(data => {
              if (data.status === 'success') {
                  showAlert(data.message, 'success');
                  if (currentEmailDisplay && data.new_email) {
                      currentEmailDisplay.value = data.new_email; // Обновляем email на основной странице
                  }
                  setTimeout(() => {
                      closeChangeEmailModal();
                  }, 2000); // Закрываем модалку после успеха
              } else {
                  showAlert(data.message || 'Invalid verification code.', 'danger');
                  if(verificationCodeInput) {
                      verificationCodeInput.focus();
                      verificationCodeInput.select();
                  }
              }
          })
          .catch(error => {
              console.error('Custom Email Modal: Error verifying code:', error);
              showAlert('An error occurred. Please try again.', 'danger');
          })
          .finally(() => {
              submitVerificationCodeBtn.disabled = false;
              submitVerificationCodeBtn.innerHTML = 'Done';
          });
      });
  }

  // Ссылка "Didn't receive an email?" (пока просто заглушка)
  if (resendCodeLink) {
    resendCodeLink.addEventListener('click', function(event) {
      event.preventDefault();
      // Здесь должна быть логика повторной отправки кода.
      // Она может быть похожа на newEmailForm.submit, но возможно с другим URL или параметром.
      // Например, можно вызвать отправку кода для email из hiddenNewEmailForVerification.value
      const emailToResend = hiddenNewEmailForVerification.value;
      if (emailToResend) {
          showAlert(`Resending code to ${emailToResend}... (feature not implemented yet)`, 'info');
          // TODO: Реализовать фактическую повторную отправку кода.
          // Это может быть такой же fetch, как и при первой отправке.
          // Возможно, понадобится временно заблокировать ссылку.
          console.log(`Request to resend code to: ${emailToResend}`);
          // Пример:
          // fetch(sendCodeUrl, { ... body: new URLSearchParams({'new_email': emailToResend, 'resend': 'true'}) ... })
          //  .then(...)
          //  .catch(...);
      } else {
          showAlert('Email not specified for resending code.', 'danger');
      }
    });
  }

  if (!changeEmailModalOverlay) {
    console.warn('Custom Email Modal: Modal overlay element #changeEmailModalOverlay not found.');
  }
});