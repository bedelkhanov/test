// mini_app.js
// Скрипт для работы мини‑приложения. Получает список рубрик и роликов через
// API и отображает их пользователю. При выборе ролика показывает плеер и
// текстовый разбор.

// Helper функция для создания элемента с классами и текстом
function createElement(tag, className, text) {
    const el = document.createElement(tag);
    if (className) el.className = className;
    if (text) el.textContent = text;
    return el;
}

// Получаем элементы
const categoriesContainer = document.getElementById('categories');
const videosContainer = document.getElementById('videos');
const videoDetailContainer = document.getElementById('video-detail');

// Текущий выбранный category ID
let currentCategoryId = null;

// Загрузка рубрик при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    fetchCategories();
});

// Получаем список рубрик из API
async function fetchCategories() {
    try {
        const response = await fetch('/api/categories');
        const categories = await response.json();
        renderCategories(categories);
    } catch (err) {
        console.error('Ошибка при загрузке рубрик:', err);
        categoriesContainer.textContent = 'Не удалось загрузить рубрики.';
    }
}

function renderCategories(categories) {
    categoriesContainer.innerHTML = '';
    const list = createElement('ul', 'space-y-2');
    categories.forEach(cat => {
        const li = createElement('li');
        const button = createElement('button', 'bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-sm px-4 py-2 rounded w-full text-left', cat.name);
        button.addEventListener('click', () => {
            selectCategory(cat.id);
        });
        li.appendChild(button);
        list.appendChild(li);
    });
    categoriesContainer.appendChild(list);
}

async function selectCategory(categoryId) {
    currentCategoryId = categoryId;
    // Очистим детальный просмотр
    videoDetailContainer.innerHTML = '';
    // Загружаем ролики
    await fetchVideos(categoryId);
}

async function fetchVideos(categoryId) {
    videosContainer.innerHTML = 'Загрузка...';
    try {
        const response = await fetch(`/api/videos/${categoryId}`);
        const videos = await response.json();
        renderVideos(videos);
    } catch (err) {
        console.error('Ошибка при загрузке роликов:', err);
        videosContainer.textContent = 'Не удалось загрузить ролики.';
    }
}

function renderVideos(videos) {
    videosContainer.innerHTML = '';
    if (videos.length === 0) {
        videosContainer.textContent = 'В выбранной рубрике пока нет роликов.';
        return;
    }
    const list = createElement('ul', 'space-y-2');
    videos.forEach(video => {
        const li = createElement('li');
        const button = createElement('button', 'bg-blue-100 dark:bg-blue-800 hover:bg-blue-200 dark:hover:bg-blue-700 text-sm px-4 py-2 rounded w-full text-left', video.title);
        button.addEventListener('click', () => {
            selectVideo(video.id);
        });
        li.appendChild(button);
        list.appendChild(li);
    });
    videosContainer.appendChild(list);
}

async function selectVideo(videoId) {
    videoDetailContainer.innerHTML = 'Загрузка…';
    try {
        const response = await fetch(`/api/video/${videoId}`);
        const video = await response.json();
        renderVideoDetail(video);
    } catch (err) {
        console.error('Ошибка при получении видео:', err);
        videoDetailContainer.textContent = 'Не удалось загрузить видео.';
    }
}

function renderVideoDetail(video) {
    videoDetailContainer.innerHTML = '';
    const titleEl = createElement('h2', 'text-xl font-semibold mb-2', video.title);
    const videoEl = document.createElement('video');
    videoEl.src = video.video_url;
    videoEl.controls = true;
    videoEl.className = 'w-full mb-2 rounded';
    // Анализ текста
    const analysisEl = createElement('p', 'text-base', video.analysis);
    videoDetailContainer.appendChild(titleEl);
    videoDetailContainer.appendChild(videoEl);
    videoDetailContainer.appendChild(analysisEl);
}