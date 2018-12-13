import findspark
findspark.init('/Users/shiyuliu/spark')
from pyspark.ml.evaluation import RegressionEvaluator
from pyspark.ml.recommendation import ALS
from pyspark.ml.regression import LinearRegression
from pyspark.sql import Row
from pyspark.sql import SparkSession
from sqlalchemy import *
from sqlalchemy.pool import NullPool
import numpy as np
import random
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
spark = SparkSession.builder.appName("ALSExample").getOrCreate()



def bulid_als_model(rateInfo):

    # Load data as RDD, then transform it to DataFrame format
    # lines = spark.read.text("/Users/shiyuliu/Desktop/table_rate.csv").rdd
    # parts = lines.map(lambda row: row.value.split(","))
    # ratingsRDD = parts.map(lambda p: Row(mov_id=int(p[0]), user_id=int(p[1]),
    #                                      grade=float(p[2])))
    # ratings = spark.createDataFrame(ratingsRDD)
    ratings = spark.createDataFrame(rateInfo, ['mov_id', 'user_id', 'grade'])
    # ratings.show()

    # using jdbc to load dataframe from postgres
    # jdbcDF = spark.read \
    # .format("jdbc") \
    # .option("url", "jdbc:postgresql:bigdata") \
    # .option("dbtable", "rate") \
    # .option("user", "shiyu") \
    # .option("password", "password") \
    # .load()

    # ratings = jdbcDF.drop('review')
    # ratings.show()

    # Split data to training part and test part
    (training, test) = ratings.randomSplit([0.8, 0.2])
    # Build the recommendation model using ALS on the training data
    # Note we set cold start strategy to 'drop' to ensure we don't get NaN evaluation metrics
    als = ALS(maxIter=2, regParam=0.01, userCol="user_id", itemCol="mov_id", ratingCol="grade",
              coldStartStrategy="drop")
    model = als.fit(training)
    return model
def spark_recommendation(selected_userId, movie_num, model):
    user = spark.createDataFrame([(selected_userId,)],['user_id'])
    userSubsetRecs = model.recommendForUserSubset(user, movie_num)
    selected_movieId = []
    for i in range(0, movie_num):
        selected_movieId.append(userSubsetRecs.select("recommendations").rdd.map(lambda row : row[0]).collect()[0][i]['mov_id'])
    
    return selected_movieId

def weighted_mean_recommendation(df, movie_num):
        # Filter sparse movies
    min_movie_ratings = 100
    filter_movies = (df['mov_id'].value_counts()>min_movie_ratings)
    filter_movies = filter_movies[filter_movies].index.tolist()

    # Filter sparse users
    min_user_ratings = 10
    filter_users = (df['user_id'].value_counts()>min_user_ratings)
    filter_users = filter_users[filter_users].index.tolist()

    # Actual filtering
    df_filterd = df[(df['mov_id'].isin(filter_movies)) & (df['user_id'].isin(filter_users))]
    del filter_movies, filter_users, min_movie_ratings, min_user_ratings
    print('Shape User-Ratings unfiltered:\t{}'.format(df.shape))
    print('Shape User-Ratings filtered:\t{}'.format(df_filterd.shape))

    # Shuffle DataFrame
    df_filterd = df_filterd.sample(frac=1).reset_index(drop=True)

    # Testingsize
    n = 100000

    # Split train- & testset
    df_train = df_filterd[:-n]
    df_test = df_filterd[-n:]

    # Create a user-movie matrix with empty values
    df_p = df_train.pivot_table(index='user_id', columns='mov_id', values='grade')




    ##########WEIGHTED MEAN RATING

    # Number of minimum votes to be considered
    m = 10

    # Mean rating for all movies
    C = df_p.stack().mean()

    # Mean rating for all movies separatly
    R = df_p.mean(axis=0).values

    # Rating count for all movies separatly
    v = df_p.count().values


    # Weighted formula to compute the weighted rating
    weighted_score = (v/ (v+m) *R) + (m/ (v+m) *C)
    # Sort ids to ranking
    weighted_ranking = np.argsort(weighted_score)[::-1]
    # Sort scores to ranking
    weighted_score = np.sort(weighted_score)[::-1]
    # Get movie ids
    weighted_movie_ids = df_p.columns[weighted_ranking]

    top_movie = weighted_movie_ids[:movie_num].values.tolist()
    return top_movie

def tfidf_buildModel(df_table_movie):
    tfidf=TfidfVectorizer(stop_words='english')
    movie_metadata = df_table_movie[['mov_id','overview']]
    movie_metadata=movie_metadata.set_index('mov_id')
    # print('Shape Movie-Metadata:\t{}'.format(movie_metadata.shape))
    movie_metadata.sample(10)
    movie_metadata_sample=movie_metadata
    #presumed to be uninformative in representing the context of a text
    #avoid to make them used in prediction
    #automatically apply a stopwords list for english language
    tfidf_matrix=tfidf.fit_transform(raw_documents=movie_metadata_sample['overview'].dropna())
    # learn vocabulary and idf
    # dropna is a pandas method, means remove the missing values https://pandas.pydata.org/pandas-docs/stable/missing_data.html#missing-data
    similarity = cosine_similarity(tfidf_matrix)
    # cosine similarity between all movie descriptions
    similarity -= np.eye(similarity.shape[0])
    #remove self-similarity
    return similarity
def tfidf_descriptionRecommendation(df_table_movie, df_table_rate, movie_num, userId, similarity):
    movie_metadata = df_table_movie[['mov_id','overview']]
    movie_metadata=movie_metadata.set_index('mov_id')





    this_user_rating=df_table_rate.loc[df_table_rate['user_id']==userId]
    movie_selected=this_user_rating.sort_values(by=['grade'],ascending=False)['mov_id'][:3]
#     movie_selected=this_user_rating.sort_values(by=['grade'],ascending=False)['mov_id'][:3]
    n_chosen = movie_num
    similar_movies=[]
    for i in movie_selected:
        index = movie_metadata.reset_index(drop=True)[movie_metadata.index==i].index[0]
        #find the index of the movie chosen
        #drop=Ture means to avoid the old index being added as a column, This resets the index to the default integer index.

        # Get indices and scores of similar movies
        similar_movies_index = np.argsort(similarity[index])[::-1][:n_chosen]
        #return the indices that would sort the array, from large to small,choose the n_chosen ones
        similar_movies_score = np.sort(similarity[index])[::-1][:n_chosen]
        #return the simlarity scores

        # Get titles of similar movies
        similar_movie_id = movie_metadata.iloc[similar_movies_index].index.tolist()
        #select by pure integer location indexing
        similar_movies+=similar_movie_id
    output_movie_indexes=random.sample(similar_movies, n_chosen)
#     output_movie_indexes=[]
#     for j in range(len(output_movie_titles)):
      
#         output_movie_indexes.append(df_table_movie[df_table_movie['name']==output_movie_titles[j]]['mov_id'].tolist()[0])
    return output_movie_indexes



