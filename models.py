from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.hybrid import hybrid_property

db = SQLAlchemy()
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

