# 🎌 Anime Recommender

Sistema de recomendación de anime con **Machine Learning** (basado en contenido) y una **interfaz web con Flask**. Le indicas tus géneros, temas y animes favoritos, y te devuelve una lista de series parecidas con un porcentaje de coincidencia.

---

## 📑 Tabla de contenidos

1. [Características](#-características)
2. [Cómo funciona](#-cómo-funciona)
3. [Estructura del proyecto](#-estructura-del-proyecto)
4. [Requisitos](#-requisitos)
5. [Instalación](#-instalación)
6. [Configuración de los datasets](#-configuración-de-los-datasets)
7. [Uso](#-uso)
   - [A) Aplicación web](#a-aplicación-web)
   - [B) API REST (endpoints)](#b-api-rest-endpoints)
   - [C) Como librería de Python](#c-como-librería-de-python)
8. [Parámetros de recomendación](#-parámetros-de-recomendación)
9. [Solución de problemas](#-solución-de-problemas)
10. [Limitaciones y mejoras futuras](#-limitaciones-y-mejoras-futuras)

---

## ✨ Características

- 🔍 **Búsqueda de animes por nombre**, con puntuación de coincidencia sobre título original, inglés, japonés y sinónimos.
- ⭐ **Recomendaciones a partir de tus favoritos**: promedia sus características y busca los más cercanos.
- 🎭 **Recomendaciones por preferencias** (géneros y temas) cuando no tienes favoritos.
- 🎛️ **Filtros**: tipo (TV, Movie, OVA, ONA, Special), máximo de episodios, puntaje mínimo y número de resultados.
- 📊 **Match score (0–100%)** para cada recomendación.
- 🌐 **Interfaz web** y **endpoints JSON** listos para consumir.
- 🛡️ **Listas de géneros y temas "seguros"** para el formulario (se excluye contenido para adultos).

---

## 🧠 Cómo funciona

Todo el motor vive en la clase `AnimeRecommender` (`Recommender.py`). Al instanciarla se ejecuta este pipeline:

1. **Limpieza del catálogo de animes** (`limpiar_datos_anime`): rellena valores nulos (títulos, sinopsis, temporada inferida por mes, episodios por mediana del tipo, año, etc.), elimina columnas irrelevantes (imágenes, tráiler, productores, horarios de emisión…) y quita duplicados.
2. **Limpieza de ratings** (`limpiar_datos_ratings`): descarta calificaciones `-1`, deja solo animes presentes en ambos datasets, usuarios con **≥ 5** ratings y animes con **≥ 10** ratings.
3. **Ingeniería de características** (`preparar_caracteristicas_ml`):
   - Numéricas estandarizadas con `StandardScaler`: `score`, `episodes`, `popularity`, `rank`, `members`, `favorites`.
   - Géneros y temas con `MultiLabelBinarizer` (one-hot multi-etiqueta).
   - Categóricas con one-hot: `type`, `rating`, `season`, `source`.
4. **Modelo KNN** (`NearestNeighbors`, métrica coseno, `algorithm='brute'`, 25 vecinos) entrenado sobre la matriz de características.
5. **Recomendación** (`recomendar_anime`): construye un *perfil de usuario* y combina tres señales de similitud coseno, normalizadas entre 0 y 1:

| Escenario | Perfil de usuario | Peso perfil | Peso favoritos | Peso KNN |
|---|---|---|---|---|
| **Con favoritos** | Promedio de los vectores de tus favoritos | 0.3 | 0.4 | 0.3 |
| **Sin favoritos** | Vector construido con géneros (+2.0) y temas (+1.5) elegidos | 0.8 | 0.0 | 0.2 |

Después se aplican los filtros (tipo, episodios, puntaje mínimo) y se ordena por similitud combinada y, en caso de empate, por `score`.

> 💡 **Nota:** si envías favoritos, los géneros/temas seleccionados **no se usan** para construir el perfil; solo influyen cuando no hay favoritos.

---

## 📂 Estructura del proyecto

```
anime_recommender/
├── app.py            # Servidor Flask: rutas web y endpoints JSON
├── Recommender.py    # Clase AnimeRecommender (limpieza, features, KNN, recomendación)
├── templates/        # Plantillas HTML (index.html)
├── static/           # Archivos estáticos (CSS, JS, imágenes)
└── assets/           # Datasets CSV: anime.csv y rating.csv
```

---

## 🛠️ Requisitos

- **Python 3.9+**
- Librerías:
  - `flask`
  - `pandas`
  - `numpy`
  - `scikit-learn`
- Los datasets `anime.csv` y `rating.csv` dentro de `assets/`.

### Formato esperado de los datasets

**`anime.csv`** (catálogo, estilo MyAnimeList). Columnas usadas por el código:

`mal_id`, `title`, `title_english`, `title_japanese`, `title_synonyms`, `synopsis`, `type`, `source`, `episodes`, `rating`, `score`, `scored_by`, `rank`, `popularity`, `members`, `favorites`, `season`, `year`, `genres`, `themes`, `demographics`, `studios`, `aired_from`, `aired_to`, y `aired_prop_from_*`.

**`rating.csv`** (calificaciones de usuarios):

`user_id`, `anime_id`, `rating`

---

## 📥 Instalación

```bash
# 1. Clonar el repositorio
git clone https://github.com/noejsl/anime_recommender.git
cd anime_recommender

# 2. Crear y activar un entorno virtual
python -m venv venv

# Linux / macOS
source venv/bin/activate
# Windows (PowerShell)
venv\Scripts\Activate.ps1
# Windows (CMD)
venv\Scripts\activate.bat

# 3. Instalar dependencias
pip install flask pandas numpy scikit-learn
```

*(Opcional)* Crea un `requirements.txt` para facilitar la instalación:

```txt
flask
pandas
numpy
scikit-learn
```

y luego usa `pip install -r requirements.txt`.

---

## ⚙️ Configuración de los datasets

1. Coloca `anime.csv` y `rating.csv` en la carpeta `assets/`.
2. **Importante:** en `app.py` las rutas están escritas de forma absoluta para una máquina Windows concreta:

   ```python
   recommender = AnimeRecommender(
       anime_path="C:/Users/USUARIO/Documents/Github/anime_recommender/assets/anime.csv",
       ratings_path="C:/Users/USUARIO/Documents/Github/anime_recommender/assets/rating.csv"
   )
   ```

   Cámbialas por rutas relativas para que funcione en cualquier equipo:

   ```python
   import os

   BASE_DIR = os.path.dirname(os.path.abspath(__file__))

   recommender = AnimeRecommender(
       anime_path=os.path.join(BASE_DIR, "assets", "anime.csv"),
       ratings_path=os.path.join(BASE_DIR, "assets", "rating.csv"),
   )
   ```

---

## 🚀 Uso

### A) Aplicación web

```bash
python app.py
```

Verás en consola `Cargando sistema de recomendación...` seguido de `Sistema inicializado correctamente`. La primera carga puede tardar (depende del tamaño de los CSV). Luego abre:

👉 **http://localhost:5000**

Desde la interfaz puedes:

1. Buscar y agregar **animes favoritos** (se consultan por nombre).
2. Elegir **géneros** y **temas**.
3. Ajustar **tipo**, **máximo de episodios**, **puntaje mínimo** y **cantidad de resultados**.
4. Pulsar el botón de recomendar y ver la lista con su **match score**.

> El servidor corre con `debug=True` en `0.0.0.0:5000`. Esto es cómodo para desarrollo, pero **no lo uses así en producción** (ver [Limitaciones](#-limitaciones-y-mejoras-futuras)).

### B) API REST (endpoints)

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/` | Página principal con el formulario |
| `GET` | `/search_anime?q=<texto>` | Busca animes por nombre (máx. 10 resultados) |
| `POST` | `/recommend` | Genera recomendaciones |
| `GET` | `/anime_info/<mal_id>` | Detalle de un anime (sinopsis, estudios, etc.) |
| `POST` | `/debug_favorites` | Endpoint de depuración para verificar favoritos |

#### 🔎 Buscar un anime

```bash
curl "http://localhost:5000/search_anime?q=naruto"
```

Respuesta (ejemplo de estructura):

```json
[
  {
    "mal_id": 20,
    "title": "Naruto",
    "title_english": "Naruto",
    "score_match": 150,
    "anime_score": 8.0,
    "genres": "...",
    "type": "TV"
  }
]
```

#### 🎯 Obtener recomendaciones

Los datos se envían como **formulario** (`application/x-www-form-urlencoded`).

**Con favoritos** (usa los `mal_id` obtenidos en la búsqueda):

```bash
curl -X POST http://localhost:5000/recommend \
  -d "favorites[]=20" \
  -d "favorites[]=1535" \
  -d "min_score=7.5" \
  -d "n_recommendations=10"
```

**Solo con preferencias** (sin favoritos):

```bash
curl -X POST http://localhost:5000/recommend \
  -d "genres[]=action" \
  -d "genres[]=fantasy" \
  -d "themes[]=isekai" \
  -d "type=TV" \
  -d "max_episodes=26" \
  -d "min_score=7.0" \
  -d "n_recommendations=5"
```

Respuesta:

```json
{
  "success": true,
  "count": 5,
  "recommendations": [
    {
      "mal_id": 1,
      "title": "...",
      "type": "TV",
      "genres": "...",
      "score": 8.7,
      "episodes": 26,
      "popularity": 43,
      "match_score": 1.0
    }
  ]
}
```

> `match_score` va de `0.0` a `1.0` (multiplícalo por 100 para el porcentaje).

#### 📖 Detalle de un anime

```bash
curl http://localhost:5000/anime_info/20
```

Devuelve: `title`, `title_english`, `synopsis`, `genres`, `type`, `episodes`, `score`, `popularity`, `studios`, `source`, `rating`.

#### 🐞 Depurar favoritos

```bash
curl -X POST http://localhost:5000/debug_favorites \
  -d "favorites[]=20" -d "favorites[]=99999"
```

Imprime en consola si cada ID existe en el dataset limpio y responde con la cantidad recibida.

### C) Como librería de Python

También puedes usar el motor sin Flask:

```python
from Recommender import AnimeRecommender

rec = AnimeRecommender(
    anime_path="assets/anime.csv",
    ratings_path="assets/rating.csv",
)

# 1) Buscar un anime por nombre
resultados = rec.buscar_anime_por_nombre("fullmetal alchemist")
for r in resultados[:3]:
    print(r["mal_id"], r["title"], r["score_match"])

# 2) Recomendar a partir de favoritos
df = rec.recomendar_anime(favoritos=[5114], n_recommendations=10)
print(df[["title", "type", "score", "match_score"]])

# 3) Recomendar por géneros y temas
df = rec.recomendar_anime(
    genres_preferred=["action", "adventure"],
    themes_preferred=["isekai"],
    anime_type="TV",
    max_episodes=26,
    min_score=7.5,
    n_recommendations=5,
)
print(df)

# 4) Utilidades para poblar formularios
print(rec.get_available_genres())
print(rec.get_available_themes())
print(rec.get_available_types())

# 5) Vecinos más similares a un anime (índice interno del DataFrame)
idx = rec.df_anime_clean.index[rec.df_anime_clean["mal_id"] == 5114][0]
print(rec.knn_similar_anime(idx, n=10))
```

#### Métodos principales

| Método | Qué hace |
|---|---|
| `buscar_anime_por_nombre(nombre)` | Devuelve hasta 10 animes ordenados por coincidencia y puntaje |
| `recomendar_anime(...)` | Devuelve un `DataFrame` con las recomendaciones y `match_score` |
| `knn_similar_anime(idx, n)` | Lista de `(índice, similitud)` de los vecinos más cercanos |
| `get_available_genres()` | Géneros disponibles (lista segura) |
| `get_available_themes()` | Temas disponibles (lista segura) |
| `get_available_types()` | `TV`, `Movie`, `OVA`, `ONA`, `Special` |

---

## 🎛️ Parámetros de recomendación

| Parámetro | Tipo | Por defecto | Descripción |
|---|---|---|---|
| `genres` / `genres_preferred` | lista | `None` | Géneros preferidos (solo aplican sin favoritos) |
| `themes` / `themes_preferred` | lista | `None` | Temas preferidos (solo aplican sin favoritos) |
| `type` / `anime_type` | str | `None` | `TV`, `Movie`, `OVA`, `ONA` o `Special` |
| `max_episodes` | int | `None` | Máximo de episodios |
| `min_score` | float | `7.0` | Puntaje mínimo del anime |
| `favorites` / `favoritos` | lista de `mal_id` | `[]` | Animes que ya te gustan (se excluyen de los resultados) |
| `n_recommendations` | int | `10` | Cantidad de resultados |

**Géneros disponibles:** action, adventure, comedy, drama, fantasy, sci-fi, romance, slice of life, sports, mystery, supernatural, magic, school, shounen, shoujo, seinen, josei, music, psychological, thriller, horror, historical, martial arts, mecha, military, police, demographics.

**Temas disponibles:** School, Mecha, Music, Historical, Isekai, Samurai, Magic, Super Power, Urban Fantasy, Sports, Team Sports, Racing, Performing Arts, Visual Arts, Otaku Culture, Workplace, Gourmet, Medical, Mythology, Survival.

---

## 🩺 Solución de problemas

| Problema | Causa probable | Solución |
|---|---|---|
| `FileNotFoundError` al iniciar | Rutas absolutas de Windows en `app.py` | Usa rutas relativas (ver [Configuración](#-configuración-de-los-datasets)) |
| `ModuleNotFoundError: No module named 'flask'` (u otro) | Dependencias sin instalar | `pip install flask pandas numpy scikit-learn` |
| `KeyError` sobre una columna al iniciar | El CSV no tiene el formato esperado | Revisa las columnas en [Formato esperado](#formato-esperado-de-los-datasets) |
| Arranque muy lento | El dataset de ratings es grande | Es normal en la primera carga; espera a ver `Sistema inicializado correctamente` |
| `No hay animes que coincidan con los filtros` | Filtros demasiado estrictos | Baja `min_score`, sube `max_episodes` o quita el `type` |
| El puerto 5000 está ocupado | Otro proceso lo usa | Cambia `port=5000` al final de `app.py` |
| Mis géneros no cambian nada | Enviaste favoritos | Con favoritos, el perfil se calcula solo con ellos |

---

## ⚠️ Limitaciones y mejoras futuras

- Las rutas de los datasets están fijas en `app.py` (ver arriba).
- No hay `requirements.txt` ni licencia declarada.
- `debug=True` y `host='0.0.0.0'` exponen el depurador de Flask en la red: para producción usa un servidor WSGI (por ejemplo `gunicorn app:app`) y desactiva el modo debug.
- El endpoint `/debug_favorites` es solo para desarrollo; conviene eliminarlo en producción.
- La búsqueda por nombre recorre el DataFrame fila por fila (`iterrows`), lo que puede ser lento con catálogos grandes.
- El modelo es **basado en contenido**: los ratings de usuarios solo se usan para filtrar el catálogo, no para filtrado colaborativo.
- Ideas: filtrado colaborativo o híbrido, uso de la sinopsis con TF-IDF/embeddings, caché del modelo entrenado (`joblib`), imágenes de portada, tests automatizados y Docker.

---

## 🤝 Contribuir

1. Haz un fork del repositorio.
2. Crea una rama: `git checkout -b feature/mi-mejora`
3. Haz commit de tus cambios: `git commit -m "Agrega mi mejora"`
4. Sube la rama: `git push origin feature/mi-mejora`
5. Abre un Pull Request.

---

## 👤 Autor

Creado por [**noejsl**](https://github.com/noejsl).

## 📄 Licencia

Aún no se ha definido una licencia. Puedes agregar una (por ejemplo MIT) creando un archivo `LICENSE` en la raíz del repositorio.
