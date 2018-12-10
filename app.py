#!/usr/bin/env python2.7

"""
Columbia W4111 Intro to databases
Example webserver

To run locally

	python app.py

Go to http://localhost:8111 in your browser


A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""
from __future__ import print_function
import os
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response, url_for, flash, session
from werkzeug.security import check_password_hash, generate_password_hash
import sys
# from forms import RegistrationForm, LoginForm

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)
app.config['SECRET_KEY'] = '5791628bb0b13ce0c676dfde280ba245'

# XXX: The Database URI should be in the format of: 
#
#     postgresql://USER:PASSWORD@<IP_OF_POSTGRE_SQL_SERVER>/<DB_NAME>
#
# For example, if you had username ewu2493, password foobar, then the following line would be:
#
#     DATABASEURI = "postgresql://ewu2493:foobar@<IP_OF_POSTGRE_SQL_SERVER>/postgres"
#
# For your convenience, we already set it to the class database

# Use the DB credentials you received by e-mail
DB_USER = "ho2271"
DB_PASSWORD = "d1d6s4ad"

DB_SERVER = "w4111.cisxo09blonu.us-east-1.rds.amazonaws.com"

DATABASEURI = "postgresql://"+DB_USER+":"+DB_PASSWORD+"@"+DB_SERVER+"/w4111"

# This line creates a database engine that knows how to connect to the URI above
engine = create_engine(DATABASEURI)

@app.before_request
def before_request():
  """
  This function is run at the beginning of every web request 
  (every time you enter an address in the web browser).
  We use it to setup a database connection that can be used throughout the request

  The variable g is globally accessible
  """
  try:
	g.conn = engine.connect()
  except:
	print("uh oh, problem connecting to database")
	import traceback; traceback.print_exc()
	g.conn = None

@app.teardown_request
def teardown_request(exception):
  """
  At the end of the web request, this makes sure to close the database connection.
  If you don't the database could run out of memory!
  """
  try:
	g.conn.close()
  except Exception as e:
	pass

@app.route('/')
def home():
	"""
	request is a special object that Flask provides to access web request information:

	request.method:   "GET" or "POST"
	request.form:     if the browser submitted a form, this contains the data in the form
	request.args:     dictionary of URL arguments e.g., {a:1, b:2} for http://localhost?a=1&b=2

	See its API: http://flask.pocoo.org/docs/0.10/api/#incoming-request-data
	"""

	# DEBUG: this is debugging code to see what request looks like
 	print(request.args)

  # return render_template("index.html", **context)
	return render_template("home.html")


#This is the movie-index page
@app.route('/movies')
def movie_index():
  cmd = 'SELECT * FROM movie ORDER BY RANDOM() LIMIT 12'
  movies =[]
  result = g.conn.execute(text(cmd))
  for movie in result:
	movies.append(movie)
  print(type(movies), file=sys.stderr)
  return render_template("./movies/index.html", movies = movies, title= "Recommended movies for you.")


#This is the movie-show page
@app.route('/movies/<int:id>')
def movie_show(id):
  # cmd = 'SELECT movie.mov_id, movie.name AS mov_name, movie.language, movie.runtime, movie.release_date, genre.name AS genre_name,  act.cast_id, act.role, mov_cast.name AS cast_name, mov_cast.gender  FROM movie, belong_to, mov_cast, act, genre WHERE movie.mov_id = :name  AND movie.mov_id = act.mov_id AND belong_to.mov_id = movie.mov_id AND act.cast_id = mov_cast.cast_id AND genre.genre_id = belong_to.genre_id'
  cmd1 = 'SELECT * FROM movie WHERE movie.mov_id = %s'
  cmd2 = 'SELECT genre.name FROM movie, genre, belong_to WHERE movie.mov_id = %s AND movie.mov_id = belong_to.mov_id AND belong_to.genre_id = genre.genre_id'
  cmd3 = 'SELECT act.cast_id, act.role, mov_cast.name FROM movie, mov_cast, act WHERE movie.mov_id = %s AND movie.mov_id = act.mov_id AND act.cast_id = mov_cast.cast_id'
  cmd4 = 'SELECT link.web_id, link.mov_id FROM link WHERE link.mov_id = %s'
  cmd5 = 'SELECT director.director_id, director.name FROM movie, direct, director WHERE movie.mov_id = %s AND movie.mov_id = direct.mov_id AND direct.director_id = director.director_id'
  cmd6 = 'SELECT rate.grade, rate.review, user_most_like.user_id, user_most_like.name FROM rate, user_most_like WHERE rate.mov_id = %s AND rate.review is not Null AND user_most_like.user_id = rate.user_id'
  if 'user_id' in session:
	cmd7 = 'SELECT rate.grade, rate.review FROM movie, rate, user_most_like WHERE movie.mov_id = rate.mov_id AND rate.user_id = user_most_like.user_id AND user_most_like.user_id = %s AND movie.mov_id = %s'
	selected_user_movie_rateInfos = g.conn.execute(cmd7, (session['user_id'], id,))
	selected_user_movie_rateInfo= []
	for tmp in selected_user_movie_rateInfos:
	  selected_user_movie_rateInfo.append(tmp)
	if len(selected_user_movie_rateInfo) == 0:
	  selected_user_movie_rateInfo = None

  else:
	selected_user_movie_rateInfo = None


  selected_movie_info = g.conn.execute(cmd1, (id,)).fetchone()
  selected_movie_genre = g.conn.execute(cmd2, (id,))
  selected_movie_castInfo = g.conn.execute(cmd3, (id,))
  selected_movie_link = g.conn.execute(cmd4, (id,)).fetchone()
  selected_movie_directorInfo = g.conn.execute(cmd5, (id,))
  selected_movie_rateInfos = g.conn.execute(cmd6, (id,))
  selected_movie_rateInfo = []
  for tmp in selected_movie_rateInfos:
	selected_movie_rateInfo.append(tmp)

  # print(type(selected_movie), file=sys.stderr)

  return render_template("./movies/show.html", selected_movie_info = selected_movie_info, selected_movie_genre=selected_movie_genre, selected_movie_castInfo=selected_movie_castInfo, selected_movie_link=selected_movie_link, selected_movie_directorInfo=selected_movie_directorInfo, selected_movie_rateInfo=selected_movie_rateInfo, selected_user_movie_rateInfo=selected_user_movie_rateInfo)

#This is review-add route
@app.route('/movies/<int:id>/rates',methods=['GET', 'POST'])
def rate_add(id):
  if 'user_id' not in session:
	flash('Please login first before add reviews!','danger')
	return redirect(url_for('login'))
  else:
	if request.method == 'GET':
	  cmd1 = 'SELECT movie.name FROM movie WHERE movie.mov_id = %s limit 10'
	  selected_movie_info = g.conn.execute(cmd1, (id,)).fetchone()
	  return render_template("./rates/add.html", id = id, selected_movie_info=selected_movie_info)
	else:
	  grade = request.form['grade']
	  review = request.form['review']
	  user_id = session['user_id']
	  mov_id = id
	  cmd2 = 'INSERT INTO rate(mov_id, user_id, grade, review) VALUES (%s, %s, %s, %s);'
	  g.conn.execute(cmd2, (mov_id, user_id, grade, review))
	  return redirect(url_for('movie_show', id=mov_id))

#This is review-edit route
@app.route('/movies/<int:id>/rates/edit',methods=['GET', 'POST'])
def rate_edit(id):
  if 'user_id' not in session:
	flash('Please login first before edit reviews!','danger')
	return redirect(url_for('login'))
  else:
	if request.method == 'GET':
	  cmd1 = 'SELECT movie.name, rate.grade, rate.review FROM movie, rate, user_most_like WHERE movie.mov_id = %s AND rate.mov_id = movie.mov_id AND user_most_like.user_id = rate.user_id'
	  selected_rate_info = g.conn.execute(cmd1, (id,)).fetchone()
	  return render_template("./rates/edit.html", id = id, selected_rate_info=selected_rate_info)
	else:
	  grade = request.form['grade']
	  review = request.form['review']
	  user_id = session['user_id']
	  mov_id = id
	  cmd2 = 'UPDATE rate SET grade = %s, review = %s WHERE rate.user_id = %s AND rate.mov_id =%s;'
	  g.conn.execute(cmd2, (grade, review, user_id, mov_id,))
	  return redirect(url_for('movie_show', id=mov_id))

#This is review-delete route
@app.route('/movies/<int:id>/rates/delete',methods=['POST'])
def rate_delete(id):
  if 'user_id' not in session:
	flash('Please login first before delete reviews!','danger')
	return redirect(url_for('login'))
  else:
	cmd = 'DELETE FROM rate WHERE user_id = %s AND mov_id = %s'
	g.conn.execute(cmd, (session['user_id'], id, ))
	return redirect(url_for('movie_show', id=id))


#This is actor-show route
@app.route('/actors/<int:id>')
def actor_show(id):
  cmd1 = 'SELECT * FROM mov_cast WHERE mov_cast.cast_id = %s'
  cmd2 = 'SELECT movie.mov_id, movie.name, act.role FROM movie, mov_cast, act WHERE mov_cast.cast_id = %s AND movie.mov_id = act.mov_id AND mov_cast.cast_id = act.cast_id'
  selected_actor_info = g.conn.execute(cmd1, (id,)).fetchone()
  selected_actor_movieInfo = g.conn.execute(cmd2, (id,))
  return render_template("./actors/show.html", selected_actor_info = selected_actor_info, selected_actor_movieInfo = selected_actor_movieInfo)

#This is director-show route
@app.route('/directors/<int:id>')
def director_show(id):
  cmd1 = 'SELECT * FROM director WHERE director.director_id = %s'
  cmd2 = 'SELECT movie.mov_id, movie.name FROM movie, direct WHERE direct.director_id = %s AND movie.mov_id = direct.mov_id'
  selected_director_info = g.conn.execute(cmd1, (id,)).fetchone()
  selected_director_movieInfo = g.conn.execute(cmd2, (id,))
  return render_template("./directors/show.html", selected_director_info = selected_director_info, selected_director_movieInfo=selected_director_movieInfo)


#This is user-show route
@app.route('/users/<int:id>')
def user_show(id):
  cmd1 = 'SELECT * FROM user_most_like WHERE user_most_like.user_id = %s'
  cmd2 = 'SELECT user_most_like.user_id, user_most_like.genre_id, genre.name FROM user_most_like, genre WHERE user_most_like.user_id = %s AND user_most_like.genre_id = genre.genre_id'
  cmd3 = 'SELECT movie.mov_id, movie.name, rate.grade, rate.review FROM rate, movie WHERE rate.user_id = %s AND movie.mov_id = rate.mov_id'
  selected_user_info = g.conn.execute(cmd1, (id,)).fetchone()
  selected_user_genreInfo = g.conn.execute(cmd2, (id,)).fetchone()
  selected_user_rateInfo = g.conn.execute(cmd3, (id,))
  return render_template("./users/show.html", selected_user_info=selected_user_info, selected_user_genreInfo=selected_user_genreInfo, selected_user_rateInfo=selected_user_rateInfo)

# This is the search path
@app.route('/search',methods=['POST'])
def search():
  if request.method == 'POST':
	#search_for = request.form['search_for']
	search_content = request.form['search_content']
	search_content = '%'+search_content+'%'
	movie_results = []
	actor_results = []
	director_results = []
	cmd = "SELECT mov_id, name FROM movie WHERE movie.name ILIKE %s limit 10"
	search_result = g.conn.execute(cmd, (search_content))
	for result in search_result:
		movie_results.append(result)
	cmd = "SELECT cast_id, name FROM mov_cast WHERE mov_cast.name ILIKE %s limit 10"
	search_result = g.conn.execute(cmd, (search_content))
	for result in search_result:
		actor_results.append(result)
	cmd = "SELECT director_id, name FROM director WHERE director.name ILIKE %s limit 10"
	search_result = g.conn.execute(cmd, (search_content))
	for result in search_result:
		director_results.append(result)
	search_content = search_content[1:-1]
	return render_template("search_result.html", movie_results = movie_results, actor_results=actor_results, director_results=director_results, search_content=search_content)
 
  return redirect('/')

# query movies by genres
@app.route('/genre', methods=['GET','POST'])
def genre():
	if request.method == 'GET':
		results = None
		search_content = None
		return render_template("/genre.html", results=results, search_content=search_content)

	if request.method == 'POST':
		results = []
		search_content = request.form.getlist('genre')[0]
		earch_content = '%'+search_content+'%'
		print(search_content)

		# get movies based on genre name
		cmd = """select movie.name, movie.mov_id, movie.language, movie.runtime, movie.release_date, movie.revenue, movie.poster_path
		from movie, belong_to, genre 
		where movie.mov_id=belong_to.mov_id and belong_to.genre_id = genre.genre_id and genre.name = %s limit 12;"""

		search_result = g.conn.execute(cmd, (search_content))
		
		for result in search_result:
			results.append(result)

		print(results)
		return render_template("./movies/index.html", movies = results, title= "Top movies in ", search_content = search_content)
		
# add ratings or movies into database
@app.route('/add', methods=['GET','POST'])
def add():
	if request.method == 'GET':
		pass
	if request.method == 'POST':
		if "new_movie" in request.form:
			name = request.form.get('name')
			mov_id = request.form.get('mov_id')
			language = request.form.get('language')
			runtime = request.form.get('runtime')
			release_date = request.form.get('release_date')
			revenue = request.form.get('revenue')

			print(name, mov_id, language, runtime, release_date, revenue)

			cmd = 'INSERT INTO movie(name, mov_id, language, runtime, release_date, revenue) VALUES (%s, %s, %s, %s, %s, %s);'
			g.conn.execute(cmd, (name, mov_id, language, runtime, release_date, revenue, ))
		else:
			print("DID NOT GET THE FORM VALUE")
	return render_template("/add.html")

@app.route("/register", methods=['GET', 'POST'])
def register():
  if request.method == 'POST':
	  # print(request.form, file=sys.stderr)
	  username = request.form['username']
	  password = request.form['password']
	  error = None

	  if not username:
		  error = 'Username is required.'
	  elif not password:
		  error = 'Password is required.'

	  elif g.conn.execute(
		  'SELECT user_id FROM user_most_like WHERE username = %s', (username,)
	  ).fetchone() is not None:
		  error = 'User {} is already registered.'.format(username)

	  if error is None:
		  g.conn.execute(
			  'INSERT INTO user_most_like (user_id, username, password) VALUES (DEFAULT, %s, %s)',
			  (username, generate_password_hash(password),)
		  )
		  flash('User {} successfully registered.'.format(username),'success')
		  return redirect(url_for('login'))

	  flash(error,'danger')

  return render_template('register.html', title='Sign up')


@app.route("/login", methods=['GET', 'POST'])
def login():
	print(session)
	if request.method == 'POST':
		username = request.form['username']
		password = request.form['password']
		error = None
		user = g.conn.execute(
			'SELECT * FROM user_most_like WHERE username = %s', (username,)
		).fetchone()

		if user is None:
			error = 'Incorrect username.'
		elif not check_password_hash(user['password'], password):
			error = 'Incorrect password.'
		# elif not user['password'] == password:
		#     error = 'Incorrect password.'

		if error is None:
			session.clear()
			session['user_id'] = user['user_id']
			session['username'] = user['username']

			return redirect(url_for('movie_index'))

		flash(error,'danger')

	return render_template('login.html',title='Login')

@app.route('/logout')
def logout():
	session.clear()
	return redirect(url_for('movie_index'))


if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8112, type=int)
  def run(debug, threaded, host, port):
	"""
	This function handles command line parameters.
	Run the server using

		python server.py

	Show the help text using

		python server.py --help

	"""

	HOST, PORT = host, port
	print("running on %s:%d" % (HOST, PORT))
	app.run(host=HOST, port=PORT, debug=True, threaded=threaded)


  run()
