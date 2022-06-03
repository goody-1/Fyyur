#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import sys
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from itsdangerous import exc
from forms import *

from sqlalchemy.ext.hybrid import hybrid_property
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db, compare_type=True)

# TODO: connect to a local postgresql database

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))

    # TODO: implement any missing fields, as a database migration using Flask-Migrate

    genres = db.Column(db.PickleType)
    website = db.Column(db.String(300))
    seeking_talent = db.Column(db.Boolean)
    seeking_description = db.Column(db.Text)
    shows = db.relationship('Show', backref="venue", lazy=True, passive_deletes=True)

    @hybrid_property
    def past_shows(self):
      past_shows = Show.query.filter(
        Show.venue_id == self.id).filter(Show.start_time < datetime.utcnow()).all()
      return past_shows

    @hybrid_property
    def past_shows_count(self):
      past_shows_count = db.session.query(db.func.count()).filter(
        Show.venue_id == self.id).filter(Show.start_time < datetime.utcnow()).scalar()
      return past_shows_count

    @hybrid_property
    def upcoming_shows(self):
      upcoming_shows = Show.query.filter(
        Show.venue_id == self.id).filter(Show.start_time > datetime.utcnow()).all()
      return upcoming_shows

    @hybrid_property
    def upcoming_shows_count(self):
      upcoming_shows_count = db.session.query(db.func.count()).filter(
        Show.venue_id == self.id).filter(Show.start_time > datetime.utcnow()).scalar()
      return upcoming_shows_count


class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.PickleType)
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))

    # TODO: implement any missing fields, as a database migration using Flask-Migrate
    website = db.Column(db.String(300))
    seeking_venue = db.Column(db.Boolean)
    seeking_description = db.Column(db.Text)
    shows = db.relationship('Show', backref="artist", lazy=True, passive_deletes=True)


    @hybrid_property
    def past_shows(self):
      past_shows = Show.query.filter(
        Show.artist_id == self.id).filter(Show.start_time < datetime.utcnow()).all()
      return past_shows

    @hybrid_property
    def past_shows_count(self):
      past_shows_count = db.session.query(db.func.count()).filter(
        Show.artist_id == self.id).filter(Show.start_time < datetime.utcnow()).scalar()
      return past_shows_count

    @hybrid_property
    def upcoming_shows(self):
      upcoming_shows = Show.query.filter(
        Show.artist_id == self.id).filter(Show.start_time > datetime.utcnow()).all()
      return upcoming_shows

    @hybrid_property
    def upcoming_shows_count(self):
      upcoming_shows_count = db.session.query(db.func.count()).filter(
        Show.artist_id == self.id).filter(Show.start_time > datetime.utcnow()).scalar()
      return upcoming_shows_count

# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.

class Show(db.Model):
    __tablename__ = 'Show'

    id = db.Column(db.Integer, primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id', ondelete='CASCADE'), nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id', ondelete='CASCADE'), nullable=False)

    start_time = db.Column(db.DateTime, default=datetime.utcnow)

    # Usefulness of hybrid property
    # https://docs.sqlalchemy.org/en/13/orm/mapped_sql_expr.html#using-a-hybrid
    # I needed this to be able to use 'self.artist_id', avoiding 'self not defined'
    # I can also call 'artist_name' or 'venue_name' for instance as an attribute instead of a function
    @hybrid_property
    def artist_name(self):
      artist_name = Artist.query.filter(Artist.id == self.artist_id).all()[0].name
      return artist_name

    @hybrid_property
    def venue_name(self):
      venue_name = Venue.query.filter(Venue.id == self.venue_id).all()[0].name
      return venue_name

    @hybrid_property
    def artist_image_link(self):
      artist_image_link = Artist.query.filter(Artist.id == self.artist_id).all()[0].image_link
      return artist_image_link

    @hybrid_property
    def venue_image_link(self):
      venue_image_link = Venue.query.filter(Venue.id == self.venue_id).first().image_link
      return venue_image_link


#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  if isinstance(value, str):
    date = dateutil.parser.parse(value)
  else:
    date = value
  if format == 'full':
    format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
    format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------
def areas():
  """
  Get the grouping of venues into areas
  """
  cities = []
  states = []
  areas = {}

  # Collect all cities and states in the Venue database
  for venue in Venue.query.all():
    cities.append(venue.city)
    states.append(venue.state)

  # Connect / zip each city with corresponding state
  cities_states = list(zip(cities, states))
  # Make the list unique
  cities_states = list(set(cities_states))

  # For each tuple of cities_states, group all venues belonging to that category
  for i in range(len(cities_states)):
    areas[cities_states[i]] = []
    for venue in Venue.query.all():
      if venue.city == cities_states[i][0] and venue.state == cities_states[i][1]:
        areas[cities_states[i]].append(venue)

  # Create
  new_areas = []

  for key, value in areas.items():
      mod_area = {}
      mod_area['city'] = key[0]
      mod_area['state'] = key[1]
      mod_area['venues'] = value
      new_areas.append(mod_area)

  return new_areas


@app.route('/venues')
def venues():
  # TODO: replace with real venues data.
  #       num_upcoming_shows should be aggregated based on number of upcoming shows per venue.
  data=areas()
  return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  response={
    "count": 1,
    "data": [{
      "id": 2,
      "name": "The Dueling Pianos Bar",
      "num_upcoming_shows": 0,
    }]
  }
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id

  # data = list(filter(lambda d: d['id'] == venue_id, [data1, data2, data3]))[0]
  return render_template('pages/show_venue.html', venue=Venue.query.filter_by(id=venue_id).order_by('id').first())

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion

  try:
    name = request.form.get('name')
    city = request.form.get('city')
    state = request.form.get('state')
    address = request.form.get('address')
    phone = request.form.get('phone')
    genres = request.form.getlist('genres')
    image_link = request.form.get('image_link')
    facebook_link = request.form.get('facebook_link')
    website = request.form.get('website')
    seeking_talent = True if 'seeking_talent' in request.form else False
    seeking_description = request.form.get('seeking_description')

    venue = Venue(name=name, city=city, state=state, address=address, phone=phone, genres=genres, facebook_link=facebook_link, image_link=image_link, website=website, seeking_talent=seeking_talent, seeking_description=seeking_description)

    db.session.add(venue)
    db.session.commit()

  # on successful db insert, flash success
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  except Exception as e:
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    print(e); print()
    db.session.rollback()
    print(sys.exc_info())
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
    return redirect(url_for('create_venue_submission'))
  finally:
    db.session.close()
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  try:
    venue_name = Venue.query.get(venue_id).name
    print(venue_name)

    Venue.query.filter_by(id=venue_id).delete()

    db.session.commit()
    flash('Venue "{}" was successfully deleted.'.format(venue_name))
    return redirect(url_for('index'))
  except Exception:
    db.session.rollback()
    flash('Something went wrong, venue "{}" could not be deleted.'.format(venue_id))
    print(sys.exc_info())
  finally:
    db.session.close()

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  data = areas()
  return redirect(url_for('venues', areas=data))

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  data = Artist.query.all()

  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  response={
    "count": 1,
    "data": [{
      "id": 4,
      "name": "Guns N Petals",
      "num_upcoming_shows": 0,
    }]
  }
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  # TODO: replace with real artist data from the artist table, using artist_id
  return render_template('pages/show_artist.html', artist=Artist.query.filter_by(id=artist_id).order_by('id').first())

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist = Artist.query.get(artist_id)

  if not artist:
    return redirect(url_for('artist'))
  else:
    form = ArtistForm(obj=artist)

  artist={
    "id": artist_id,
    "name": artist.name,
    "genres": artist.genres,
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "website": artist.website,
    "facebook_link": artist.facebook_link,
    "seeking_venue": artist.seeking_venue,
    "seeking_description": artist.seeking_description,
    "image_link": artist.image_link
  }
  # TODO: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  venue = Venue.query.get(venue_id)

  if not venue:
    return redirect(url_for('venues'))
  else:
    form = VenueForm(obj=venue)

  # genre_list = list(form.genres)
  # print("\n\n***{}".format(genre_list))

  # venue.name=form.name
  # # venue.genres=genre_list
  # venue.address=form.address
  # venue.city=form.city
  # venue.state=form.state
  # venue.phone=form.phone
  # venue.website=form.website_link
  # venue.facebook_link=form.facebook_link
  # venue.seeking_talent=form.seeking_talent
  # venue.seeking_description=form.seeking_description
  # venue.image_link=form.image_link

  venue={
    "id": venue_id,
    "name": venue.name,
    "genres": venue.genres,
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website": venue.website,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "image_link": venue.image_link
  }

  # TODO: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  venue = Venue.query.get(venue_id)

  form = VenueForm()

  if venue and form.validate():
    try:
      venue.name = request.form.get('name')
      venue.city = request.form.get('city')
      venue.state = request.form.get('state')
      venue.address = request.form.get('address')
      venue.phone = request.form.get('phone')
      venue.genres = request.form.getlist('genres')
      venue.seeking_talent = True if 'seeking_talent' in request.form else False
      venue.seeking_description = request.form.get('seeking_description')
      venue.image_link = request.form.get('image_link')
      venue.website = request.form.get('website')
      venue.facebook_link = request.form.get('facebook_link')

      # db.session.add(venue)
      db.session.commit()
      flash('Venue ' + venue.name + ' was successfully updated!')

    except Exception:
      db.session.rollback()
      print(sys.exc_info())
      flash(
          "An error occurred. Venue "
          + request.form.get("name")
          + " could not be updated."
      )
      return redirect(url_for('edit_venue_submission', venue_id=venue_id))
    finally:
        db.session.close()
  else:
    flash("Venue id {} and Venue name {} does not exist".format(venue.id, request.form.get('name')))
    return redirect(url_for('index'))

  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion

  try:
    name = request.form.get('name')
    city = request.form.get('city')
    state = request.form.get('state')
    phone = request.form.get('phone')
    genres = request.form.getlist('genres')
    image_link = request.form.get('image_link')
    facebook_link = request.form.get('facebook_link')
    website = request.form.get('website')
    seeking_venue = True if 'seeking_venue' in request.form else False
    seeking_description = request.form.get('seeking_description')

    artist = Artist(name=name, city=city, state=state,phone=phone, genres=genres, facebook_link=facebook_link, image_link=image_link, website=website, seeking_venue=seeking_venue, seeking_description=seeking_description)

    db.session.add(artist)
    db.session.commit()

    # on successful db insert, flash success
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  except Exception:
    db.session.rollback()
    print(sys.exc_info())
    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
    return redirect(url_for('create_artist_submission'))
  finally:
    db.session.close()
  return redirect(url_for('artists'))


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  data = Show.query.all()
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead

  # on successful db insert, flash success
  flash('Show was successfully listed!')
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Show could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.debug = True
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
