from flask import Flask, render_template, request, jsonify
from Recommender import AnimeRecommender
import pandas as pd
import os

app = Flask(__name__, static_folder='static', template_folder='templates')
# Inicializar el recomendador
print("Cargando sistema de recomendación...")

recommender = AnimeRecommender(
    anime_path="C:/Users/USUARIO/Documents/Github/anime_recommender/assets/anime.csv",
    ratings_path="C:/Users/USUARIO/Documents/Github/anime_recommender/assets/rating.csv"
)

@app.route('/')
def index():
    """Página principal con el formulario de recomendaciones"""
    genres = recommender.get_available_genres()
    themes = recommender.get_available_themes()
    types = recommender.get_available_types()
    
    return render_template('index.html', 
                         genres=genres, 
                         themes=themes, 
                         types=types)

@app.route('/search_anime')
def search_anime():
    """Endpoint para buscar animes por nombre"""
    query = request.args.get('q', '')
    if not query:
        return jsonify([])
    
    results = recommender.buscar_anime_por_nombre(query)
    return jsonify(results)

@app.route('/recommend', methods=['POST'])
def get_recommendations():
    """Endpoint para generar recomendaciones"""
    try:
        # Obtener parámetros del formulario
        genres = request.form.getlist('genres[]')
        themes = request.form.getlist('themes[]')
        anime_type = request.form.get('type', '')
        max_episodes = request.form.get('max_episodes', type=int)
        min_score = request.form.get('min_score', 7.0, type=float)
        favorites = request.form.getlist('favorites[]')
        n_recommendations = request.form.get('n_recommendations', 10, type=int)
        
        # Convertir favorites a enteros de manera segura
        favorites = []
        for fav in request.form.getlist('favorites[]'):
            try:
                favorites.append(int(fav))
            except (ValueError, TypeError):
                continue
        
        # Generar recomendaciones
        recommendations = recommender.recomendar_anime(
            genres_preferred=genres,
            themes_preferred=themes,
            anime_type=anime_type if anime_type else None,
            max_episodes=max_episodes,
            min_score=min_score,
            favoritos=favorites,
            n_recommendations=n_recommendations
        )
        
        # Convertir a formato JSON de manera segura
        results = []
        for _, row in recommendations.iterrows():
            results.append({
                'mal_id': int(row['mal_id']),
                'title': str(row['title']),
                'type': str(row['type']),
                'genres': str(row['genres']),
                'score': float(row['score']),
                'episodes': int(row['episodes']) if pd.notna(row['episodes']) else 0,
                'popularity': int(row['popularity']) if pd.notna(row['popularity']) else 0,
                'match_score': float(row['match_score'])
            })
        
        return jsonify({
            'success': True,
            'recommendations': results,
            'count': len(results)
        })
        
    except Exception as e:
        print(f"Error en recomendaciones: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/anime_info/<int:mal_id>')
def get_anime_info(mal_id):
    """Obtiene información detallada de un anime"""
    anime = recommender.df_anime_clean[recommender.df_anime_clean['mal_id'] == mal_id]
    if anime.empty:
        return jsonify({'error': 'Anime no encontrado'}), 404
    
    anime_data = anime.iloc[0]
    
    # Convertir todos los valores numéricos a tipos nativos de Python
    return jsonify({
        'title': str(anime_data['title']),
        'title_english': str(anime_data['title_english']) if pd.notna(anime_data['title_english']) else 'N/A',
        'synopsis': str(anime_data['synopsis']),
        'genres': str(anime_data['genres']),
        'type': str(anime_data['type']),
        'episodes': int(anime_data['episodes']) if pd.notna(anime_data['episodes']) else 0,
        'score': float(anime_data['score']) if pd.notna(anime_data['score']) else 0.0,
        'popularity': int(anime_data['popularity']) if pd.notna(anime_data['popularity']) else 0,
        'studios': str(anime_data['studios']),
        'source': str(anime_data.get('source', 'N/A')),
        'rating': str(anime_data.get('rating', 'N/A'))
    })
    
@app.route('/debug_favorites', methods=['POST'])
def debug_favorites():
    """Endpoint para debuguear el manejo de favoritos"""
    try:
        favorites = request.form.getlist('favorites[]')
        favorites = [int(fav) for fav in favorites if fav.isdigit()]
        
        print(f"Favoritos recibidos: {favorites}")
        print(f"Cantidad: {len(favorites)}")
        
        # Verificar si existen en el dataset
        for fav_id in favorites:
            exists = fav_id in recommender.df_anime_clean['mal_id'].values
            anime_name = recommender.df_anime_clean[recommender.df_anime_clean['mal_id'] == fav_id]['title'].iloc[0] if exists else "NO ENCONTRADO"
            print(f"  - ID {fav_id}: {anime_name} ({'EXISTE' if exists else 'NO EXISTE'})")
        
        return jsonify({
            'success': True,
            'favorites_received': favorites,
            'count': len(favorites)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)