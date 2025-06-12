// Функция получения CSRF-токена
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
        const cookies = document.cookie.split(";");
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.startsWith(name + "=")) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Функция переключения вкладок
function showTab(tabId) {
    // Скрываем все вкладки
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active'); // Удаляем класс active у всех вкладок
    });

    // Убираем активный класс у всех кнопок
    document.querySelectorAll('.games-tabs button').forEach(btn => {
        btn.classList.remove('active');
    });

    // Показываем выбранную вкладку
    const activeTab = document.getElementById(tabId);
    if (activeTab) {
        activeTab.classList.add('active'); // Добавляем класс active к выбранной вкладке
    }

    // Устанавливаем активный класс на соответствующую кнопку
    const activeButton = document.querySelector(`.games-tabs button[onclick*="${tabId}"]`);
    if (activeButton) {
        activeButton.classList.add('active'); // Добавляем класс active к кнопке
    }
}

// Добавление комментария
document.addEventListener("DOMContentLoaded", function () {
    const cancelButton = document.querySelector(".cancel-comment");
    const commentForm = document.getElementById("comment-form");

    if (cancelButton) {
        cancelButton.addEventListener("click", function (event) {
            event.preventDefault();
            // Сброс значений всех полей
            document.getElementById("comment-title").value = "";
            document.getElementById("comment-text").value = "";
        });
    }

    const commentFormSubmit = document.getElementById("comment-form");

    if (commentFormSubmit) {
        commentFormSubmit.addEventListener("submit", function (event) {
            event.preventDefault();

            const title = document.getElementById("comment-title").value;
            const content = document.getElementById("comment-text").value;
            const objectId = document.getElementById("object-id").value;
            const commentType = document.getElementById("comment-type").value;

            const csrftoken = getCookie("csrftoken");

            // Проверка на пустые поля
            if (!title || !content) {
                alert("Заполните все поля!");
                return;
            }

            fetch(`/user/add_comment/${commentType}/${objectId}/`, {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrftoken,
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    title: title,
                    content: content,
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Добавляем новый комментарий в DOM
                    addCommentToDOM(data.comment); // Передаем новый комментарий в функцию
                    // Сбрасываем поля ввода
                    document.getElementById("comment-title").value = "";
                    document.getElementById("comment-text").value = "";
                } else {
                    alert("Ошибка: " + data.error);
                }
            })
            .catch(error => {
                console.error("Ошибка:", error);
            });
        });
    }

    function addCommentToDOM(comment) {
        const commentsList = document.getElementById("commentsList");
        const commentDiv = document.createElement("div");
        commentDiv.className = "comment";
        commentDiv.id = `comment-${comment.id}`;
        
        const likeIcon = comment.liked ? "/static/imgs/icons/red_like_comment.svg" : "/static/imgs/icons/like_comment.svg"; // Устанавливаем иконку в зависимости от состояния лайка
    
        commentDiv.innerHTML = `
            <img src="${comment.user.avatar}" alt="avatar">
            <div class="comment-content">
                <div class="comment-info">
                    <div class="comment-meta">
                        <div class="username-date">
                            <h2>${comment.user.username}</h2>
                            <span class="comment-date">${comment.created_at}</span>
                        </div>
                        <h3>${comment.title}</h3>
                    </div>
                    <span class="user-rating">
                        <img src="/static/imgs/icons/btn-star-small.svg" alt="Star btn">
                        10
                    </span>
                </div>
                <span class="comment-text">${comment.content}</span>
                <div class="reactions-to-comment">
                    <div class="likes">
                        <button class="like-btn" data-id="${comment.id}">
                            <img src="${likeIcon}" alt="Like Button">
                        </button>
                        <span class="like-count">${comment.like_count}</span> <!-- Элемент для количества лайков -->
                    </div>
                    <button class="reply-comment">
                        <img src="/static/imgs/icons/reply.svg" alt="Reply btn">
                        Reply
                    </button>
                </div>
                <button class="show-replies">0 replies</button>
                <div class="reply-form" style="display: none;">
                    <input type="text" class="reply-title" placeholder="Title" required>
                    <textarea class="reply-text" placeholder="Text" required></textarea>
                    <button class="publish-reply">Publish</button>
                </div>
            </div>
        `;
        
        commentsList.prepend(commentDiv);
    }

    // Обработка нажатия на кнопку "Like"
    document.addEventListener("click", function (event) {
        if (event.target.closest(".like-btn")) { // Используем closest для обработки клика на изображении
            const likeButton = event.target.closest(".like-btn");
            const commentId = likeButton.getAttribute("data-id");
            const likeCountSpan = likeButton.nextElementSibling; // Получаем элемент с количеством лайков
            const csrftoken = getCookie("csrftoken");

            fetch(`/user/like_comment/${commentId}/`, {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrftoken,
                    "Content-Type": "application/json",
                },
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Обновляем количество лайков
                    likeCountSpan.innerText = data.like_count;

                    // Меняем иконку лайка в зависимости от состояния
                    const likeIcon = likeButton.querySelector("img");
                    if (data.liked) {
                        likeIcon.src = "/static/imgs/icons/red_like_comment.svg"; // Красная иконка, если лайк установлен
                    } else {
                        likeIcon.src = "/static/imgs/icons/like_comment.svg"; // Обычная иконка, если лайк убран
                    }
                } else {
                    alert("Ошибка: " + data.error);
                }
            })
            .catch(error => {
                console.error("Ошибка:", error);
            });
        }
    });

});
