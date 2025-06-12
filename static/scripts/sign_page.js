document.addEventListener("DOMContentLoaded", function () {
  const regModal = document.getElementById("reg");
  const openReg = document.getElementById("open-reg");
  const closeButton = document.querySelector(".close-modal"); // Находим крестик

  if (openReg && regModal) {
    openReg.addEventListener("click", function () {
      regModal.classList.add("--show");
    });
  }

  // Закрытие модалки (крестик)
  if (closeButton) {
    closeButton.addEventListener("click", function (event) {
      event.stopPropagation();
      regModal.classList.remove("--show");
    });
  }

  // Закрытие по клику вне формы (по фону)
  regModal.addEventListener("click", function (event) {
    if (event.target === regModal) {
      regModal.classList.remove("--show");
    }
  });
});
