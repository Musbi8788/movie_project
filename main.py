from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests
import os

headers = {"accept": "application/json",
           "Authorization": os.environ.get('AUTH')
           }


Api_Key = os.environ.get('Movie_API')
IMAGES_Url = "https://image.tmdb.org/t/p/w500"



#Create a form for the search bar
class AddForm(FlaskForm):
    title = StringField('Movie Title', validators=[DataRequired()])
    submit = SubmitField('Add Movie')

#Create a form for editing or update
class MovieForm(FlaskForm):
    rating = StringField('Your Rating Out of  10 eg 8.1', validators=[DataRequired()])
    review  = StringField('Your Review',validators=[DataRequired()])
    submit = SubmitField('Done')

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('S_KEY')
Bootstrap(app)

##CREATE DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movies.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


##CREATE TABLE
class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(500), nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True) #I comment cs i'm not using it now
    review = db.Column(db.String(250), nullable=True)
    img_url = db.Column(db.String(250), nullable=False)

with app.app_context():
    db.create_all()

# Example on how to create database
# After adding the new_movie the code needs to be commented out/deleted.
# So you are not trying to add the same movie twice.
#     new_movie = Movie(
#         title="Phone Booth",
#         year=2002,
#         description="Publicist Stuart Shepard finds himself trapped in a phone booth, pinned down by an extortionist's sniper rifle. Unable to leave or receive outside help, Stuart's negotiation with the caller leads to a jaw-dropping climax.",
#         rating=7.3,
#         ranking=10,
#         review="My favourite character was the caller.",
#         img_url="https://image.tmdb.org/t/p/w500/tjrX2oWRCM3Tvarz38zlZM7Uc10.jpg"
#     )
#     db.session.add(new_movie)
#     db.session.commit()

#Home page
@app.route("/")
def home():
    # This line creates a list of all the movies sorted by rating
    all_movies = Movie.query.order_by(Movie.rating).all()

    # This line loops through all the movies
    for i in range(len(all_movies)):
        # This line gives each movie a new ranking reversed from their order in all_movies
        all_movies[i].ranking = len(all_movies) - i

    db.session.commit()
    return render_template("index.html", movies=all_movies)

#Edit page
@app.route("/edit", methods=["GET", "POST"])
def edit():
    form = MovieForm()
    movie_id = request.args.get("id")
    movie = Movie.query.get(movie_id)

    if form.validate_on_submit():
        movie.rating = float(form.rating.data)
        movie.review = form.review.data
        # print(movie.rating, movie.review)
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("edit.html", movie=movie, form=form)

#Delete Button
@app.route("/delete")
def delete():
    movie_id = request.args.get("id")
    movie_to_delete = Movie.query.get(movie_id)
    db.session.delete(movie_to_delete)
    db.session.commit()
    return redirect(url_for('home'))

#Add and Select page
@app.route("/add", methods=["GET","POST"])
def add():
    new_form  = AddForm()
    if new_form.validate_on_submit():
        movie_title = new_form.title.data

        # Send requests
        Movie_Url = f"https://api.themoviedb.org/3/search/movie?query={movie_title}&include_adult=false&language=en-US&page=1"
        # params = {
        #     "query":movie_title,
        #     "api_key":Api_Key
        # }

        response = requests.get(Movie_Url,headers=headers)
        results = response.json()["results"]

        #Get the movies details
        # for result in results:
        #     movies_id = result["id"]
        #     movies_title = result["title"]

        return render_template("select.html", results=results)
    return render_template("add.html", new_form=new_form)

#Search or Find page
@app.route("/find")
def find_movie():

    movie_api_id = request.args.get("id")
    # print(movie_api_id)
    if movie_api_id:
        # Get the movies details
        Movie_id_url = f"https://api.themoviedb.org/3/movie/{movie_api_id}"


        # The language parameter is optional, if you were making the website for a different audience
        # e.g. Hindi speakers then you might choose "hi-IN"

        response = requests.get(Movie_id_url, headers=headers)
        # print(response)
        data = response.json()

        ##Add new data into the database
        new_movie = Movie(
            title = data["title"],
            # The data in release_date includes month and day, we will want to get rid of.
            year=data["release_date"].split("-")[0],
            img_url = f'{IMAGES_Url}{data["backdrop_path"]}' ,
            description = data["overview"] ,
        )

        #the hardest bug a struggle with new_movie.id
        db.session.add(new_movie)
        db.session.commit()
        return redirect(url_for("edit", id=new_movie.id))

if __name__ == '__main__':
    app.run(debug=True)