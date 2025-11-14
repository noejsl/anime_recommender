// Variables globales
let favorites = [];

// Inicialización cuando el DOM está listo
document.addEventListener('DOMContentLoaded', function() {
    initializeEventListeners();
});

function initializeEventListeners() {
    // Búsqueda de animes
    const searchBtn = document.getElementById('searchBtn');
    const animeSearch = document.getElementById('animeSearch');
    
    searchBtn.addEventListener('click', handleSearch);
    animeSearch.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            handleSearch();
        }
    });

    // Formulario de recomendaciones
    const form = document.getElementById('recommendationForm');
    form.addEventListener('submit', handleFormSubmit);

    // Modal
    const modal = document.getElementById('animeModal');
    const closeModal = document.getElementById('closeModal');
    
    closeModal.addEventListener('click', () => {
        modal.classList.add('hidden');
    });

    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.classList.add('hidden');
        }
    });
}

// Manejar búsqueda de animes
async function handleSearch() {
    const searchInput = document.getElementById('animeSearch');
    const query = searchInput.value.trim();
    
    if (!query) {
        alert('Por favor ingresa un nombre de anime');
        return;
    }

    const resultsContainer = document.getElementById('searchResults');
    resultsContainer.innerHTML = '<div class="loading"><div class="spinner"></div><p>Buscando animes...</p></div>';

    try {
        const response = await fetch(`/search_anime?q=${encodeURIComponent(query)}`);
        const results = await response.json();
        
        displaySearchResults(results);
    } catch (error) {
        console.error('Error en la búsqueda:', error);
        resultsContainer.innerHTML = '<div class="error">Error al buscar animes</div>';
    }
}

// Mostrar resultados de búsqueda
function displaySearchResults(results) {
    const resultsContainer = document.getElementById('searchResults');
    
    if (results.length === 0) {
        resultsContainer.innerHTML = '<div class="no-results">No se encontraron animes</div>';
        return;
    }

    resultsContainer.innerHTML = results.map(anime => `
        <div class="search-result-item">
            <div class="anime-info">
                <div class="anime-title">${anime.title}</div>
                <div class="anime-details">
                    <span>Score: ${anime.anime_score.toFixed(2)}</span>
                    <span>Type: ${anime.type}</span>
                    <span>Genres: ${anime.genres}</span>
                </div>
            </div>
            <button class="add-favorite-btn" onclick="addToFavorites(${anime.mal_id}, '${anime.title.replace(/'/g, "\\'")}')">
                <i class="fas fa-plus"></i> Agregar
            </button>
        </div>
    `).join('');
}

// Agregar a favoritos
function addToFavorites(malId, title) {
    if (!favorites.some(fav => fav.id === malId)) {
        favorites.push({ id: malId, title: title });
        updateFavoritesList();
        
        // Limpiar búsqueda
        document.getElementById('animeSearch').value = '';
        document.getElementById('searchResults').innerHTML = '';
        
        // Mostrar mensaje de éxito
        showNotification(`"${title}" agregado a favoritos`, 'success');
    } else {
        showNotification('Este anime ya está en tus favoritos', 'warning');
    }
}

// Remover de favoritos
function removeFromFavorites(malId) {
    favorites = favorites.filter(fav => fav.id !== malId);
    updateFavoritesList();
}

// Actualizar lista de favoritos
function updateFavoritesList() {
    const favoritesList = document.getElementById('favoritesList');
    const favoritesInputs = document.querySelectorAll('input[name="favorites[]"]');
    
    // Remover inputs existentes
    favoritesInputs.forEach(input => input.remove());
    
    if (favorites.length === 0) {
        favoritesList.innerHTML = '<div class="no-favorites">No hay animes favoritos agregados</div>';
        return;
    }

    favoritesList.innerHTML = favorites.map(fav => `
        <div class="favorite-item">
            ${fav.title}
            <button class="remove-favorite" onclick="removeFromFavorites(${fav.id})">
                <i class="fas fa-times"></i>
            </button>
            <input type="hidden" name="favorites[]" value="${fav.id}">
        </div>
    `).join('');
}

// Manejar envío del formulario
async function handleFormSubmit(e) {
    e.preventDefault();
    
    const form = e.target;
    const formData = new FormData(form);
    
    // DEBUG: Mostrar favoritos en consola
    const favoritesInputs = document.querySelectorAll('input[name="favorites[]"]');
    const favoriteIds = Array.from(favoritesInputs).map(input => input.value);
    console.log('Favoritos a enviar:', favoriteIds);
    
    // Mostrar loading
    const loading = document.getElementById('loading');
    const resultsContainer = document.getElementById('resultsContainer');
    
    loading.classList.remove('hidden');
    resultsContainer.innerHTML = '';

    try {
        const response = await fetch('/recommend', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();
        
        if (data.success) {
            console.log('Recomendaciones recibidas:', data.recommendations);
            displayRecommendations(data.recommendations);
        } else {
            throw new Error(data.error || 'Error desconocido');
        }
    } catch (error) {
        console.error('Error:', error);
        resultsContainer.innerHTML = `
            <div class="error-message">
                <i class="fas fa-exclamation-triangle"></i>
                <h3>Error al generar recomendaciones</h3>
                <p>${error.message}</p>
                <p>Favoritos enviados: ${favoriteIds.join(', ')}</p>
            </div>
        `;
    } finally {
        loading.classList.add('hidden');
    }
}

// Función para probar con favoritos específicos
function testWithPopularAnimes() {
    // Agregar algunos animes populares como prueba
    const testAnimes = [
        { id: 1, title: "Naruto" },
        { id: 20, title: "One Piece" },
        { id: 1535, title: "Death Note" },
        { id: 16498, title: "Attack on Titan" }
    ];
    
    // Limpiar favoritos actuales
    favorites = [];
    
    // Agregar animes de prueba
    testAnimes.forEach(anime => {
        if (!favorites.some(fav => fav.id === anime.id)) {
            favorites.push(anime);
        }
    });
    
    updateFavoritesList();
    showNotification('Animes de prueba agregados. Ahora genera recomendaciones!', 'success');
    
    console.log('🧪 Animes de prueba agregados:', favorites.map(f => f.title));
}

// Mostrar recomendaciones
function displayRecommendations(recommendations) {
    const resultsContainer = document.getElementById('resultsContainer');
    const resultsCount = document.getElementById('resultsCount');
    
    resultsCount.textContent = recommendations.length;
    
    if (recommendations.length === 0) {
        resultsContainer.innerHTML = `
            <div class="no-results">
                <i class="fas fa-search"></i>
                <h3>No se encontraron recomendaciones</h3>
                <p>Intenta ajustar tus criterios de búsqueda</p>
            </div>
        `;
        return;
    }

    resultsContainer.innerHTML = recommendations.map(anime => `
        <div class="anime-card" onclick="showAnimeDetails(${anime.mal_id})">
            <div class="anime-header">
                <div class="anime-title-main">${anime.title}</div>
                <div class="anime-match">Match: ${(anime.match_score * 100).toFixed(1)}%</div>
            </div>
            
            <div class="anime-details-grid">
                <div class="detail-item">
                    <span class="detail-label">Tipo</span>
                    <span class="detail-value">${anime.type}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Score</span>
                    <span class="detail-value">${anime.score.toFixed(2)}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Episodios</span>
                    <span class="detail-value">${anime.episodes}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Popularidad</span>
                    <span class="detail-value">#${anime.popularity}</span>
                </div>
            </div>
            
            <div class="genres-list">
                ${typeof anime.genres === 'string' ? anime.genres.split(',').map(genre => `
                    <span class="genre-tag">${genre.trim()}</span>
                `).join('') : ''}
            </div>
        </div>
    `).join('');
}

// Mostrar detalles del anime
async function showAnimeDetails(malId) {
    const modal = document.getElementById('animeModal');
    const modalTitle = document.getElementById('modalTitle');
    const modalBody = document.getElementById('modalBody');
    
    modalBody.innerHTML = '<div class="loading"><div class="spinner"></div><p>Cargando detalles...</p></div>';
    modal.classList.remove('hidden');

    try {
        const response = await fetch(`/anime_info/${malId}`);
        const anime = await response.json();
        
        modalTitle.textContent = anime.title;
        modalBody.innerHTML = `
            <div class="modal-synopsis">
                <h4>Sinopsis</h4>
                <p>${anime.synopsis || 'Sin descripción disponible'}</p>
            </div>
            
            <div class="modal-details">
                <div class="detail-item">
                    <span class="detail-label">Título Inglés</span>
                    <span class="detail-value">${anime.title_english || 'N/A'}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Tipo</span>
                    <span class="detail-value">${anime.type}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Episodios</span>
                    <span class="detail-value">${anime.episodes}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Score</span>
                    <span class="detail-value">${anime.score.toFixed(2)}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Popularidad</span>
                    <span class="detail-value">#${anime.popularity}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Rating</span>
                    <span class="detail-value">${anime.rating}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Fuente</span>
                    <span class="detail-value">${anime.source}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Estudios</span>
                    <span class="detail-value">${anime.studios}</span>
                </div>
            </div>
            
            <div class="genres-section">
                <h4>Géneros</h4>
                <div class="genres-list">
                    ${typeof anime.genres === 'string' ? anime.genres.split(',').map(genre => `
                        <span class="genre-tag">${genre.trim()}</span>
                    `).join('') : ''}
                </div>
            </div>
        `;
    } catch (error) {
        console.error('Error:', error);
        modalBody.innerHTML = '<div class="error">Error al cargar los detalles del anime</div>';
    }
}

// Mostrar notificación
function showNotification(message, type = 'info') {
    // Crear elemento de notificación
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <i class="fas fa-${getNotificationIcon(type)}"></i>
            <span>${message}</span>
        </div>
    `;
    
    // Estilos para la notificación
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${getNotificationColor(type)};
        color: white;
        padding: 15px 20px;
        border-radius: 8px;
        box-shadow: var(--shadow);
        z-index: 1001;
        transform: translateX(100%);
        transition: transform 0.3s ease;
    `;
    
    document.body.appendChild(notification);
    
    // Animación de entrada
    setTimeout(() => {
        notification.style.transform = 'translateX(0)';
    }, 100);
    
    // Remover después de 3 segundos
    setTimeout(() => {
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }, 3000);
}

function getNotificationIcon(type) {
    const icons = {
        success: 'check-circle',
        warning: 'exclamation-triangle',
        error: 'exclamation-circle',
        info: 'info-circle'
    };
    return icons[type] || 'info-circle';
}

function getNotificationColor(type) {
    const colors = {
        success: '#10b981',
        warning: '#f59e0b',
        error: '#ef4444',
        info: '#6366f1'
    };
    return colors[type] || '#6366f1';
}

// Utilidad para formatear texto
function formatText(text) {
    return text ? text.charAt(0).toUpperCase() + text.slice(1) : 'N/A';
}
