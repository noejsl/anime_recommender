import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, MultiLabelBinarizer
from sklearn.neighbors import NearestNeighbors
import ast

class AnimeRecommender:
    def __init__(self, anime_path, ratings_path):
        self.df_anime = pd.read_csv(anime_path)
        self.df_ratings = pd.read_csv(ratings_path)
        self.df_anime_clean = None
        self.df_ratings_clean = None
        self.X_features = None
        self.mlb_genres = None
        self.mlb_themes = None
        self.knn_model = None
        
        # Inicializar el sistema
        self._initialize_system()
    
    def _initialize_system(self):
        """Inicializa todo el sistema de recomendación"""
        print("Inicializando sistema de recomendación...")
        
        # Limpiar datos
        self.df_anime_clean = self.limpiar_datos_anime(self.df_anime)
        self.df_ratings_clean, self.df_anime_clean = self.limpiar_datos_ratings(
            self.df_ratings, self.df_anime_clean
        )
        
        # Preparar características
        self.X_features, self.mlb_genres, self.mlb_themes = self.preparar_caracteristicas_ml(
            self.df_anime_clean
        )
        
        # Entrenar modelo KNN
        self.knn_model = NearestNeighbors(
            n_neighbors=25, 
            metric='cosine', 
            algorithm='brute'
        )
        self.knn_model.fit(self.X_features)
        
        print("Sistema inicializado correctamente")
    
    def limpiar_datos_anime(self, df_anime):
        """Limpieza completa del dataset de animes"""
        df = df_anime.copy()
        
        # Rellenar valores faltantes en columnas de texto
        df['title_english'] = df['title_english'].fillna(df['title'])
        df['title_japanese'] = df['title_japanese'].fillna(df['title'])
        df['title_synonyms'] = df['title_synonyms'].fillna('')
        df['synopsis'] = df['synopsis'].fillna('Sin descripción')

        # Columnas categóricas (listas o strings) vacías
        for col in ['genres', 'themes', 'demographics', 'studios']:
            df[col] = df[col].fillna('')

        df['aired_prop_from_month'] = df['aired_prop_from_month'].fillna(1)

        # Rellenar estación del año si falta
        def infer_season(month):
            if pd.isna(month):
                return 'Unknown'
            month = int(month)
            if month in [12, 1, 2]:
                return 'winter'
            elif month in [3, 4, 5]:
                return 'spring'
            elif month in [6, 7, 8]:
                return 'summer'
            elif month in [9, 10, 11]:
                return 'fall'
            return 'Unknown'

        df['season'] = df['season'].fillna(
            df['aired_prop_from_month'].apply(infer_season)
        )

        # Manejo de valores numéricos
        df['episodes'] = df.groupby('type')['episodes'].transform(
            lambda x: x.fillna(x.median() if not x.isnull().all() else 1)
        )
        
        # Rellenamos el año
        df['year'] = df['year'].fillna(
            pd.to_datetime(df['aired_from'], errors='coerce').dt.year.fillna(2000)
        )

        # Reemplazar valores nulos en score, scored_by y rank con 0
        df[['score', 'scored_by', 'rank']] = df[['score', 'scored_by', 'rank']].fillna(0)

        # Eliminar columnas irrelevantes o redundantes
        cols_to_drop = [
            'background', 'explicit_genres', 'aired_prop_from_day', 'aired_prop_from_month', 
            'aired_prop_from_year', 'aired_prop_to_day', 'aired_prop_to_month', 
            'aired_prop_to_year', 'broadcast_day', 'broadcast_time', 'broadcast_timezone', 
            'broadcast_string', 'producers', 'licensors'
        ] + [col for col in df.columns if col.startswith(('image_', 'trailer_'))]

        cols_to_drop = [col for col in cols_to_drop if col in df.columns]
        df = df.drop(columns=cols_to_drop)

        # Rellenar otros valores faltantes
        df['type'] = df['type'].fillna(df['type'].mode()[0] if len(df['type'].mode()) > 0 else 'TV')
        df['episodes'] = df['episodes'].fillna(df['episodes'].median())
        df['rating'] = df['rating'].fillna(df['rating'].mode()[0] if len(df['rating'].mode()) > 0 else 'PG-13')

        # Eliminar columnas y duplicados
        if 'aired_from' in df.columns:
            df = df.drop(columns=['aired_from'])
        if 'aired_to' in df.columns:
            df = df.drop(columns=['aired_to'])
            
        df = df.drop_duplicates()

        return df

    def limpiar_datos_ratings(self, df_ratings, df_anime):
        """Limpieza completa del dataset de ratings"""
        
        # Identificar animes comunes
        animes_en_ratings = set(df_ratings['anime_id'])
        animes_en_catalogo = set(df_anime['mal_id'])
        animes_comunes = animes_en_ratings.intersection(animes_en_catalogo)
        
        # Crear copia para limpieza
        df_ratings_clean = df_ratings.copy()

        # Aplicar filtros
        df_ratings_clean = df_ratings_clean[df_ratings_clean['rating'] != -1]
        df_ratings_clean = df_ratings_clean[df_ratings_clean['anime_id'].isin(animes_comunes)]

        # Filtrar usuarios activos
        min_ratings_per_user = 5
        user_counts = df_ratings_clean.groupby('user_id').size()
        active_users = user_counts[user_counts >= min_ratings_per_user].index
        df_ratings_clean = df_ratings_clean[df_ratings_clean['user_id'].isin(active_users)]

        # Filtrar animes populares
        min_ratings_per_anime = 10
        anime_counts = df_ratings_clean.groupby('anime_id').size()
        popular_animes = anime_counts[anime_counts >= min_ratings_per_anime].index
        df_ratings_clean = df_ratings_clean[df_ratings_clean['anime_id'].isin(popular_animes)]

        # Eliminar duplicados
        df_ratings_clean = df_ratings_clean.drop_duplicates(subset=['user_id', 'anime_id'], keep='last')

        # Filtrar df_anime para solo incluir animes con ratings
        animes_en_ratings_clean = set(df_ratings_clean['anime_id'])
        df_anime_clean = df_anime[df_anime['mal_id'].isin(animes_en_ratings_clean)].copy()

        return df_ratings_clean, df_anime_clean

    def preparar_caracteristicas_ml(self, df_anime_clean):
        """Prepara las características para el modelo de machine learning"""
        
        def parse_lista(elementos_str):
            if isinstance(elementos_str, str) and elementos_str:
                try:
                    # Intentar evaluar como lista
                    elementos = ast.literal_eval(elementos_str)
                    if isinstance(elementos, list):
                        return [elem.strip().lower() for elem in elementos if elem.strip()]
                except:
                    return [elem.strip().lower() for elem in elementos_str.split(',') if elem.strip()]
            return []

        df = df_anime_clean.copy()
        df['genres_parsed'] = df['genres'].apply(parse_lista)
        df['themes_parsed'] = df['themes'].apply(parse_lista)

        # Características numéricas
        numeric_features = ['score', 'episodes', 'popularity', 'rank', 'members', 'favorites']
        numeric_features = [feat for feat in numeric_features if feat in df.columns]
        
        for feature in numeric_features:
            df[feature] = df[feature].fillna(df[feature].median())
        
        scaler = StandardScaler()
        df_numeric = pd.DataFrame(
            scaler.fit_transform(df[numeric_features]),
            columns=[f"{feat}_norm" for feat in numeric_features],
            index=df.index
        )

        # One-Hot para géneros y temas
        mlb_genres = MultiLabelBinarizer()
        df_genres = pd.DataFrame(
            mlb_genres.fit_transform(df['genres_parsed']),
            columns=[f"genre_{g}" for g in mlb_genres.classes_],
            index=df.index
        ).astype(int)

        mlb_themes = MultiLabelBinarizer()
        df_themes = pd.DataFrame(
            mlb_themes.fit_transform(df['themes_parsed']),
            columns=[f"theme_{t}" for t in mlb_themes.classes_],
            index=df.index
        ).astype(int)

        # One-Hot para categorías simples
        categorical_features = ['type', 'rating', 'season', 'source']
        categorical_features = [feat for feat in categorical_features if feat in df.columns]
        
        df_categorical = pd.get_dummies(
            df[categorical_features].fillna('Unknown').astype(str), 
            prefix=categorical_features
        ).astype(int)

        # Combinar todo
        X_features_final = pd.concat([df_numeric, df_genres, df_themes, df_categorical], axis=1)

        return X_features_final, mlb_genres, mlb_themes

    def buscar_anime_por_nombre(self, nombre_busqueda):
        """Busca animes por nombre con coincidencia"""
        nombre_busqueda = nombre_busqueda.lower().strip()
        
        resultados = []
        
        for idx, anime in self.df_anime_clean.iterrows():
            score = 0
            titulo = str(anime['title']).lower()
            titulo_english = str(anime['title_english']).lower() if pd.notna(anime['title_english']) else ""
            titulo_japanese = str(anime['title_japanese']).lower() if pd.notna(anime['title_japanese']) else ""
            titulo_synonyms = str(anime['title_synonyms']).lower() if pd.notna(anime['title_synonyms']) else ""
            
            # Coincidencia exacta en título principal
            if nombre_busqueda == titulo:
                score += 100
            elif nombre_busqueda in titulo:
                score += 50
            
            # Coincidencia en título inglés
            if titulo_english and nombre_busqueda == titulo_english:
                score += 90
            elif titulo_english and nombre_busqueda in titulo_english:
                score += 40
            
            # Coincidencia en título japonés
            if titulo_japanese and nombre_busqueda in titulo_japanese:
                score += 30
            
            # Coincidencia en sinónimos
            if titulo_synonyms and nombre_busqueda in titulo_synonyms:
                score += 20
            
            # Búsqueda por palabras
            palabras_busqueda = nombre_busqueda.split()
            if len(palabras_busqueda) > 1:
                coincidencias_palabras = 0
                for palabra in palabras_busqueda:
                    if (palabra in titulo or 
                        (titulo_english and palabra in titulo_english) or
                        (titulo_synonyms and palabra in titulo_synonyms)):
                        coincidencias_palabras += 1
                
                if coincidencias_palabras == len(palabras_busqueda):
                    score += 60
                elif coincidencias_palabras > 0:
                    score += coincidencias_palabras * 10
            
            if score > 0:
                resultados.append({
                    'mal_id': anime['mal_id'],
                    'title': anime['title'],
                    'title_english': anime['title_english'] if pd.notna(anime['title_english']) else "N/A",
                    'score_match': score,
                    'anime_score': anime['score'],
                    'genres': anime['genres'],
                    'type': anime['type']
                })
        
        # Ordenar por score de coincidencia y luego por popularidad/score
        resultados.sort(key=lambda x: (-x['score_match'], -x['anime_score']))
        return resultados[:10]

    def knn_similar_anime(self, idx, n=15):
        """Encuentra animes similares usando KNN"""
        try:
            distances, indices = self.knn_model.kneighbors(
                [self.X_features.loc[idx].values], 
                n_neighbors=n+1
            )
            distances = distances[0]
            indices = indices[0]
            
            # Excluir el mismo anime
            if indices.size > 0 and indices[0] == idx:
                indices = indices[1:]
                distances = distances[1:]
                
            similarities = (1.0 - distances)
            return list(zip(indices, similarities))
        except Exception as e:
            return []

    
    def recomendar_anime(self, genres_preferred=None, themes_preferred=None, 
                        anime_type=None, max_episodes=None, min_score=7.0, 
                        favoritos=None, n_recommendations=10):
        """Genera recomendaciones basadas en preferencias"""
        
        favoritos = favoritos or []
        valid_fav_ids = set(self.df_anime_clean['mal_id'])
        favoritos = [f for f in favoritos if f in valid_fav_ids]
        
        print(f"Recomendacion iniciada - Favoritos: {len(favoritos)}, Generos: {genres_preferred}")
        
        # Filtrar animes que NO están en favoritos
        filtered_anime = self.df_anime_clean[~self.df_anime_clean['mal_id'].isin(favoritos)].copy()
        X_filtered = self.X_features.loc[filtered_anime.index]
        
        # Construir perfil de usuario
        user_profile = np.zeros(self.X_features.shape[1], dtype=float)
        
        # Definir fav_idx
        fav_idx = []
        if favoritos:
            fav_idx = self.df_anime_clean[self.df_anime_clean['mal_id'].isin(favoritos)].index
        
        # Estrategia de recomendación
        if favoritos and len(fav_idx) > 0:
            X_favs = self.X_features.loc[fav_idx]
            user_profile = X_favs.mean(axis=0).values
        else:
            # Filtrar géneros inapropiados
            safe_genres = ['action', 'adventure', 'comedy', 'drama', 'fantasy', 'sci-fi', 
                        'romance', 'slice of life', 'sports', 'mystery', 'supernatural',
                        'magic', 'school', 'shounen', 'shoujo', 'seinen', 'josei',
                        'music', 'psychological', 'thriller', 'horror', 'historical',
                        'martial arts', 'mecha', 'military', 'police', 'demographics']
            
            if genres_preferred:
                for g in genres_preferred:
                    if g.lower() in safe_genres:  # Solo agregar géneros seguros
                        col = f"genre_{g.lower().strip()}"
                        if col in self.X_features.columns:
                            user_profile[self.X_features.columns.get_loc(col)] += 2.0
                
            # Filtrar temas inapropiados - usar solo temas seguros
            safe_themes = ['school', 'mecha', 'music', 'historical', 'isekai', 'samurai',
                        'magic', 'super power', 'urban fantasy', 'sports', 'team sports',
                        'racing', 'performing arts', 'visual arts', 'otaku culture',
                        'workplace', 'gourmet', 'medical', 'mythology', 'survival']
            
            if themes_preferred:
                for t in themes_preferred:
                    if t.lower() in safe_themes:  # Solo agregar temas seguros
                        col = f"theme_{t.lower().strip()}"
                        if col in self.X_features.columns:
                            user_profile[self.X_features.columns.get_loc(col)] += 1.5
        
        # Evitar vector nulo
        if np.allclose(user_profile, 0):
            pop_col = next((c for c in self.X_features.columns if c.startswith('popularity')), None)
            if pop_col:
                user_profile[self.X_features.columns.get_loc(pop_col)] = 1.0
            else:
                user_profile = self.X_features.mean(axis=0).values
        
        # Normalizar
        norm = np.linalg.norm(user_profile)
        if norm > 0:
            user_profile /= norm
        
        # Calcular similitudes
        from sklearn.metrics.pairwise import cosine_similarity
        
        # 1. Similitud con perfil de usuario
        profile_sim = cosine_similarity(X_filtered.values, user_profile.reshape(1, -1)).ravel()
        filtered_anime['profile_similarity'] = profile_sim
        
        # 2. Similitud con favoritos
        if favoritos and len(fav_idx) > 0:
            fav_sim_matrix = cosine_similarity(X_filtered.values, self.X_features.loc[fav_idx].values)
            filtered_anime['favorite_similarity'] = fav_sim_matrix.mean(axis=1)
        else:
            filtered_anime['favorite_similarity'] = 0.0
        
        # 3. Similitud KNN
        knn_scores = {}
        if favoritos and len(fav_idx) > 0:
            for fav_id in favoritos:
                try:
                    fav_idx_single = self.df_anime_clean.index[self.df_anime_clean['mal_id'] == fav_id][0]
                    vecinos = self.knn_similar_anime(fav_idx_single, n=15)
                    for idx, sim in vecinos:
                        knn_scores[idx] = max(knn_scores.get(idx, 0.0), float(sim))
                except IndexError:
                    continue
                            
        filtered_anime['knn_similarity'] = filtered_anime.index.map(lambda i: knn_scores.get(i, 0.0))
        
        # Normalizar similitudes de manera segura
        for col in ['profile_similarity', 'favorite_similarity', 'knn_similarity']:
            arr = filtered_anime[col].values.astype(float)
            if len(arr) > 0 and not np.all(arr == arr[0]):  # Solo normalizar si hay variación
                lo, hi = arr.min(), arr.max()
                if hi - lo > 1e-10:  # Evitar división por cero
                    filtered_anime[col] = (arr - lo) / (hi - lo)
                else:
                    filtered_anime[col] = 0.0
            else:
                # Si todos los valores son iguales, establecer a un valor bajo
                filtered_anime[col] = 0.1
        
        # Combinación final con pesos
        if favoritos and len(fav_idx) > 0:
            w_profile, w_fav, w_knn = 0.3, 0.4, 0.3
        else:
            w_profile, w_fav, w_knn = 0.8, 0.0, 0.2
        
        filtered_anime['combined_similarity'] = (
            filtered_anime['profile_similarity'] * w_profile +
            filtered_anime['favorite_similarity'] * w_fav +
            filtered_anime['knn_similarity'] * w_knn
        )
        
        #Asegurar que combined_similarity esté entre 0 y 1
        combined_arr = filtered_anime['combined_similarity'].values
        if len(combined_arr) > 0:
            combined_min, combined_max = combined_arr.min(), combined_arr.max()
            if combined_max - combined_min > 1e-10:
                filtered_anime['combined_similarity'] = (combined_arr - combined_min) / (combined_max - combined_min)
            else:
                filtered_anime['combined_similarity'] = 0.5  # Valor medio si no hay variación
        
        # Aplicar filtros
        if anime_type:
            filtered_anime = filtered_anime[filtered_anime['type'] == anime_type]
        
        if max_episodes:
            filtered_anime = filtered_anime[filtered_anime['episodes'] <= max_episodes]
        
        if min_score:
            filtered_anime = filtered_anime[filtered_anime['score'] >= min_score]
        
        # Verificar resultados
        if len(filtered_anime) == 0:
            print("No hay animes que coincidan con los filtros")
            return pd.DataFrame()
        
        # Ordenar resultados
        filtered_anime = filtered_anime.sort_values(['combined_similarity', 'score'], ascending=[False, False])
        
        # Obtener top recomendaciones
        result = filtered_anime.head(n_recommendations)
        result_df = result[['mal_id', 'title', 'type', 'genres', 'score', 'episodes', 'popularity']].copy()
        
        # Asegurar que match_score esté entre 0% y 100%
        match_scores = result['combined_similarity'].values
        match_scores = np.clip(match_scores, 0.0, 1.0)  # Forzar entre 0 y 1
        result_df['match_score'] = match_scores
        
        print(f"Recomendaciones generadas: {len(result_df)}")
        print(f"Rango de match scores: {result_df['match_score'].min()}% - {result_df['match_score'].max()}%")
        
        return result_df
    def get_available_genres(self):
        """Obtiene la lista de géneros disponibles (solo los seguros)"""
        all_genres = [g.replace('genre_', '') for g in self.X_features.columns if g.startswith('genre_')]
        
        # Géneros seguros (sin contenido inapropiado)
        safe_genres = [
            'action', 'adventure', 'comedy', 'drama', 'fantasy', 'sci-fi', 
            'romance', 'slice of life', 'sports', 'mystery', 'supernatural',
            'magic', 'school', 'shounen', 'shoujo', 'seinen', 'josei',
            'music', 'psychological', 'thriller', 'horror', 'historical',
            'martial arts', 'mecha', 'military', 'police', 'demographics'
        ]
        
        # Filtrar solo los géneros seguros que existen en el dataset
        available_safe_genres = [g for g in safe_genres if g in all_genres]
        
        return sorted(available_safe_genres)

    def get_available_themes(self):
        """Obtiene la lista de temas disponibles (solo los seguros)"""
        safe_themes = [
            'School', 'Mecha', 'Music', 'Historical', 'Isekai', 'Samurai',
            'Magic', 'Super Power', 'Urban Fantasy', 'Sports', 'Team Sports',
            'Racing', 'Performing Arts', 'Visual Arts', 'Otaku Culture',
            'Workplace', 'Gourmet', 'Medical', 'Mythology', 'Survival'
        ]
        return safe_themes
    def get_available_types(self):
        """Obtiene los tipos de anime disponibles"""
        return ['TV', 'Movie', 'OVA', 'ONA', 'Special']