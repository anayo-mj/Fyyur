#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import os
import json
import sys
from xml.dom import NotFoundErr
import dateutil.parser
from datetime import datetime
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from sqlalchemy import distinct
from forms import *
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# TODO: connect to a local postgresql database

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))

    # TODO: implement any missing fields, as a database migration using Flask-Migrate
    genres = db.Column(db.String(120), nullable=False)
    website_link = db.Column(db.String(120))
    seeking_talent =db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.Text)
    #past_shows = db.Column(db.Integer, default=0)
    upcoming_shows = db.Column(db.Integer, default=0)
    shows = db.relationship('Shows', backref='venue', lazy=True)

    def __repr__(self):
      return f"<Venue ID: {self.id}, Venue name:{self.name}>"

class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))

    # TODO: implement any missing fields, as a database migration using Flask-Migrate
    website_link = db.Column(db.String(120))
    seeking_venue =db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.Text)
    shows = db.relationship('Shows', backref='artist', lazy=True)
    
    def __repr__(self):
      return f"<Venue ID: {self.id}, Venue name:{self.name}>"

# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.

class Shows(db.Model):
  __tablename__ = 'shows'

  id = db.Column(db.Integer, primary_key=True)
  artist_id = db.Column(db.Integer, db.ForeignKey(Artist.id), nullable=False)
  venue_id = db.Column(db.Integer, db.ForeignKey(Venue.id), nullable=False)
  start_time = db.Column(db.DateTime, nullable=False)


#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
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

@app.route('/venues')
def venues():
  # TODO: replace with real venues data.
  #       num_upcoming_shows should be aggregated based on number of upcoming shows per venue.
  data = []
  display_venue = db.session.query(distinct(Venue.city), Venue.state).all()
  thisday = datetime.now()

  for area in display_venue:
    city = area[0]
    state = area[1]

    venue_data = {'city':city, 'state':state, 'venues':[]}
    venues_discovered = Venue.query.filter_by(city=city, state=state).all()
    for venue in venues_discovered:
      venue_id = venue.id
      venue_name = venue.name
      upcoming_shows = (
        Shows.query.filter_by(venue_id=venue_id).filter(Shows.start_time > thisday).all()
      )
      venue_details = {
        'id': venue_id,
        'name': venue_name,
        'num_upcoming_shows': len(upcoming_shows)
      }
      venue_data['venues'].append(venue_details)
    data.append(venue_data)
  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on venues with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  search_return = Venue.query.filter(Venue.name.ilike('%{}%'.format(request.form['search_term']))).all()
  render_result={
    "count": len(search_return),
    "data": []
  }
  for venue in search_return:
    render_result['data'].append({
      'id': venue.id,
      'name': venue.name,
      'num_upcoming_shows': venue.upcoming_shows
    })
  return render_template('pages/search_venues.html', results=render_result, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  data={}
  try:
    venue_requested = Venue.query.get(venue_id)
    
    if venue_requested is None:
      return not_found_error(404)
    
    genres = []
    for option in venue_requested.genres:
      genres.append(option.genre)
    
    shows = Shows.query.filter_by(venue_id=venue_id)

    thisday = datetime.now()

    on_past_shows = shows.filter(Shows.start_time < thisday).all()
    past_shows = []
    for show in on_past_shows:
      artist = Artist.query.get(show.artist_id)
      show_data = {
        'artist_id': artist.id,
        'artist_name': artist.name,
        'artist_image_link': artist.image_link,
        'start_time': str(show.start_time)
      }
      past_shows.append(show_data)
    
    on_upcoming_shows = shows.filter(Shows.start_time >= thisday).all()
    upcoming_shows = []
    for show in on_upcoming_shows:
      artist = Artist.query.get(show.artist_id)
      show_data = {
        'artist_id': artist.id,
        'artist_name': artist.name,
        'artist_image_link': artist.image_link,
        'start_time': str(show.start_time)
      }
      upcoming_shows.append(show_data)
    
    data = {
      "id": venue_requested.id,
      "name": venue_requested.name,
      "genres": genres,
      "address": venue_requested.address,
      "city": venue_requested.city,
      "state": venue_requested.state,
      "phone": venue_requested.phone,
      "website": venue_requested.website,
      "facebook_link": venue_requested.facebook_link,
      "seeking_talent": venue_requested.seeking_talent,
      "seeking_description": venue_requested.seeking_description,
      "image_link": venue_requested.image_link,
      "past_shows": past_shows,
      "upcoming_shows": upcoming_shows,
      "past_shows_count": len(past_shows),
      "upcoming_shows_count": len(upcoming_shows)
    }
  except:
    print(sys.exc_info())
    flash('Error! Please try again.')
  finally:
    db.session.close()

  
  return render_template('pages/show_venue.html', venue=data)

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
  form = VenueForm(request.form)
  try:
    name=form.name.data    
    city=form.city.data
    state=form.state.data
    address=form.address.data
    phone=form.phone.data
    image_link=form.image_link.data
    facebook_link=form.facebook_link.data
    website_link=form.website_link.data
    genres=form.genres.data

    new_venue = Venue(
      name=name,
      city=city,
      state=state,
      address=address,
      phone=phone,
      image_link=image_link,
      facebook_link=facebook_link,
      website_link=website_link,
      genres=genres
    )
    db.session.add(new_venue)
    db.session.commit()
  
  # on successful db insert, flash success
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  except:
    db.session.rollback()
    print(sys.exc_info())
    flash(' An error occurred, Venue ' + request.form['name'] + ' was NOT listed!')
  finally:
    db.session.close()
    return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  required_venue = Venue.query.get(venue_id).name
  try:
    delete_venue = db.session.query(Venue).filter(Venue.id==venue_id)
    delete_venue.delete()
    db.session.commit()
    flash('The venue ' + required_venue + ' was deleted successfully.')
  except:
    db.session.rollback()
    flash('Error!. This venue was not successfully deleted.')
  finally:
    db.session.close()

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  data= Artist.query.with_entities(Artist.id, Artist.name).all()
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  search_result = Artist.query.filter(Artist.name.ilike('%{}%'.format(request.form['search_term']))).all()
  response={
    "count": len(search_result),
    "data": []
  }
  num_upcoming_shows = 0
  for artist in search_result:
    response['data'].append({
      'id': artist.id,
      'name': artist.name,
      'num_upcoming_shows': num_upcoming_shows
    })
  
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  # TODO: replace with real artist data from the artist table, using artist_id
  
  data={}
  try:
    artist_requested = Artist.query.get(artist_id)
    
    if artist_requested is None:
      return not_found_error(404)
    
    genres = []
    for option in artist_requested.genres:
      genres.append(option.genre)
    
    shows = Shows.query.filter_by(artist_id=artist_id)

    thisday = datetime.now()

    on_past_shows = shows.filter(Shows.start_time < thisday).all()
    past_shows = []
    for show in on_past_shows:
      venue = Venue.query.get(show.venue_id)
      show_data = {
        'venue_id': venue.id,
        'venue_name': venue.name,
        'venue_image_link': venue.image_link,
        'start_time': str(show.start_time)
      }
      past_shows.append(show_data)
    
    on_upcoming_shows = shows.filter(Shows.start_time >= thisday).all()
    upcoming_shows = []
    for show in on_upcoming_shows:
      venue = Venue.query.get(show.venue_id)
      show_data = {
        'venue_id': venue.id,
        'venue_name': venue.name,
        'venue_image_link': venue.image_link,
        'start_time': str(show.start_time)
      }
      upcoming_shows.append(show_data)
    
    data = {
      "id": artist_requested.id,
      "name": artist_requested.name,
      "genres": genres,
      "address": artist_requested.address,
      "city": artist_requested.city,
      "state": artist_requested.state,
      "phone": artist_requested.phone,
      "website_link": artist_requested.website_link,
      "facebook_link": artist_requested.facebook_link,
      "seeking_talent": artist_requested.seeking_talent,
      "seeking_description": artist_requested.seeking_description,
      "image_link": artist_requested.image_link,
      "past_shows": past_shows,
      "upcoming_shows": upcoming_shows,
      "past_shows_count": len(past_shows),
      "upcoming_shows_count": len(upcoming_shows)
    }
  except:
    print(sys.exc_info())
    flash('Error! Please try again.')
  finally:
    db.session.close()

  
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  
  # TODO: populate form with fields from artist with ID <artist_id>
  artist={}
  try:
    artist_edit = Artist.query.get(artist_id)
    print(artist_edit)
    if artist_edit is None:
      return not_found_error(404)
    
    genres = []
    if len(artist_edit.genres) > 0:
      for option in artist_edit.genres:
        genres.append(option.genre)
    
    artist = {
      "id": artist_edit.id,
      "name": artist_edit.name,
      "city": artist_edit.city,
      "state": artist_edit.state,
      "phone": artist_edit.phone,
      "genres": genres,
      "facebook_link": artist_edit.facebook_link,
      "seeking_venue": artist_edit.seeking_venue,
      "seeking_description": artist_edit.seeking_description,
      "image_link": artist_edit.image_link,
    }
  except:
    print(sys.exc_info())
    flash('Please try again.')
  finally:
    db.session.close()

  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  try:
    updating_artist = Artist.query.get(artist_id)

    if updating_artist is None:
      return not_found_error(404)
    
    updating_artist.name = form.name.data
    updating_artist.city = form.city.data
    updating_artist.state = form.state.data
    updating_artist.phone = form.phone.data
    updating_artist.facebook_link = form.facebook_link.data
    updating_artist.genre = form.genres.data
    updating_artist.image_link = form.image_link.data
    updating_artist.website_link = form.website_link.data
    db.session.commit()
    flash('Artist updated successfully')
  except:
    db.session.rollback()
    print(sys.exc_info())
    flash('Artist was NOT updated, try again')
  finally:
    db.session.close()

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue = {}
  # TODO: populate form with values from venue with ID <venue_id>
  # try:
  venue_needed = Venue.query.get(venue_id)
    # if  venue_needed is None:
    #   return not_found_error(404)
    # genres = []
    # if len(venue_needed.genres) > 0:
    #   for option in venue_needed.genres:
    #     genres.append(option.genre)
  venue = {
      'id': venue_needed.id,
      'name': venue_needed.name,
      'genres': venue_needed.genres.split(','),
      'address': venue_needed.address,
      'city': venue_needed.city,
      'state': venue_needed.state,
      'phone': venue_needed.phone,
      'website_link': venue_needed.website_link,
      'facebook_link': venue_needed.facebook_link,
      'seeking_talent': venue_needed.seeking_talent,
      'seeking_description': venue_needed.seeking_description,
      'image_link': venue_needed.image_link,
    }
  # except:
  #   db.session.rollback()
  #   print(sys.exc_info())
  #   flash('Please try again!!!')
  # finally:
  #   db.session.close()
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  edited_venue = Venue.query.get(venue_id)
  edited_venue.name = form.name.data
  edited_venue.city = form.city.data
  edited_venue.state = form.state.data
  edited_venue.address = form.address.data
  edited_venue.phone = form.phone.data
  edited_venue.facebook_link = form.facebook_link.data
  edited_venue.genres = form.genres.data
  edited_venue.image_link = form.image_link.data
  edited_venue.website_link = form.website_link.data

  try:
    db.session.commit()
    flash('You venue ' + request.form['name'] + ' was successfully updated!')
  except:
    db.session.rollback()
    flash('An error occurred. Venue ' + edited_venue.name + ' could not be updated.')
  finally:
    db.session.close()
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
  listing_artist = Artist()
  listing_artist.name=request.form['name']    
  listing_artist.city=request.form['city']
  listing_artist.state=request.form['state']
  listing_artist.phone=request.form['phone']
  listing_artist.image_link=request.form['image_link']
  listing_artist.facebook_link=request.form['facebook_link']
  listing_artist.website_link=request.form['website_link']
  listing_artist.genres=request.form['genres']

  # new_artist = Artist(
  #   name=name,
  #   city=city,
  #   state=state,
  #   phone=phone,
  #   image_link=image_link,
  #   facebook_link=facebook_link,
  #   website_link=website_link,
  #   genres=genres
  # )
   
  try:
    db.session.add(listing_artist)
    db.session.commit()

  # on successful db insert, flash success
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
  except:
    db.session.rollback()
    print(sys.exc_info())
    flash('An error occurred, Artist ' + request.form['name'] + ' was NOT listed!')
  finally:
    db.session.close()
    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  data=[]
  try:  
    shows_available = Shows.query.all()
    for show in shows_available:
      venue_id = show.venue_id
      artist_id= show.artist_id
      artist = Artist.query.get(artist_id)
      
      data.append({
        'venue_id': venue_id,
        'venue_name': Venue.query.get(venue_id).name,
        'artist_id': artist_id,
        'artist_name': artist.name,
        'artist_image_link': artist.image_link,
        'start_time': str(show.start_time)
      })
    # data.append(show_data)
  except:
    db.session.rollback()
    print(sys.exc_info())
    flash('An error occured. Please try again')
  finally:
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
  errors = {
    'artist_id_invalid':False, 'venue_id_invalid':False}
  try:
    artist_id = request.form.get('artist_id')
    venue_id = request.form.get('venue_id')
    start_time = request.form.get('start_time')

    artist_available = Artist.query.get(artist_id)
    if artist_available is None:
      errors['artist_id_invalid'] = True
    
    venue_available = Venue.query.get(venue_id)
    if venue_available is None:
      errors['venue_id_invalid'] = True
    
    if artist_available is not None and venue_available is not None:
      new_show = Shows(
        artist_id = artist_available.id,
        venue_id = venue_available.id,
        start_time=start_time
      )
      db.session.add(new_show)
      db.session.commit()
  
  # on successful db insert, flash success
      flash('Show was successfully listed!')
  # TODO: on unsuccessful db insert, flash an error instead.
  except:
      print(sys.exc_info())
      db.session.rollback()
      flash("Something went wrong! The show was NOT created.")

  finally:
      db.session.close()
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
'''
if __name__ == '__main__':
    app.run()
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
