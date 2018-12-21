# Movie Recommender
### 1. Overview
This is a Movie Recommendation System mainly based on Flask, PostgreSQL and Spark. It mainly has two parts:
- The web server part uses Flask and PostgreSQL as backend, bootstrap and jQuery as frontend.
- The recommendation part uses three methods to do the recommendation. 1. find highest weighted mean of movie ratings 2. do TF-IDF on movie overviews and find top movies with highest cosine-similarity(content based) 3. Spark ALS algorithm(a kind of collaborative filtering user-user recommendation).

### 2. Dataset
We use [Netflix Prize data](https://www.kaggle.com/netflix-inc/netflix-prize-data) to do the algorithm analysis. After analyzing the features of each algorithms, we choose to use [MovieLens dataset](https://www.kaggle.com/rounakbanik/the-movies-dataset) since it has more movie information.

### 3. Software Package Installation

 - Spark: Download .sh installation script and install manually.
 - Postgres: brew install postgresql.
 - finspark : `$ pip install findspark`

All packages list below can be installed directly by Anaconda.

 - Flask: `$ pip install flask`
 - sqlalchemy: `$ pip install sqlalchemy`
 - pandas: `$ pip install pandas`
 - sklearn: `$ pip install sklearn`
 - numpy: `$ pip install numpy`

### 4. Directory
 - algorithm_analysis: The seven recommendation algorithms we compared in our project. 
 - data_preprocessing: preprocess data and insert table into database.
 - templates: web pages.
 - app.py: flask backend.
 - recomEngine.py: three recommendation algorithms used in our web application.

### 5. Steps to run our application

1. Use `$ pg_ctl -D /usr/local/var/postgres start` command to start postgres server, try `$ psql -U <database_name> <user_name>` command to connect it and create your own postgres database, username and password. Revise these three in 'database.ini' and 'app.py' files.
2. Download dataset first and use jupyter notebook to run 'preprocessing_csvs.ipynb' file to process the datasets, use 'db_operations.ipynb' file to insert table into database.
3. run our application: `$ python app.py`.