# Import the dependencies.
from flask import Flask, jsonify
import datetime as dt
import pandas as pd
from sqlalchemy import create_engine, func
from sqlalchemy.orm import Session
from sqlalchemy.ext.automap import automap_base

# Database Setup
engine = create_engine("sqlite:///Resources/hawaii.sqlite")
Base = automap_base()
Base.prepare(engine, reflect=True)

Measurement = Base.classes.measurement
Station = Base.classes.station

# Create our session (link) from Python to the DB
session = Session(engine)

# Flask Setup
app = Flask(__name__)

# Flask Routes
@app.route("/")
def welcome():
    """List all available API routes."""    
    
    return (
        f"Welcome to the weather tracking site for Honolulu, Hawaii!<br/><br/>"  # Empty space between lines
        f"Available Routes:<br/><br/>"  # Empty space between lines
        f"/api/v1.0/precipitation - Precipitation data for the last 12 months<br/><br/>"  # Empty space between lines
        f"/api/v1.0/stations - List of stations<br/><br/>"  # Empty space between lines
        f"/api/v1.0/tobs - Temperature observations for the most active station (last 12 months)<br/><br/>"  # Empty space between lines
        f"/api/v1.0/start_date - Temperature statistics (TMIN, TAVG, TMAX) from the start date to the latest date. Minimum start_date to type is 2010-01-01.<br/><br/>"  # Empty space between lines
        f"/api/v1.0/start_date/end_date - Temperature statistics (TMIN, TAVG, TMAX) within the specified date range. Maximum end_date to type is 2017-08-23."
    )


@app.route("/api/v1.0/precipitation")
def precipitation():
    # Load the data from the CSV file
    precipitation_df = pd.read_csv('Resources/One_Year_precipitation_data.csv')
    
    # Convert the DataFrame to a dictionary
    prcp_dict = precipitation_df.set_index('Date')['Precipitation'].to_dict()

    # Close the session
    session.close()

    return jsonify(prcp_dict)

@app.route("/api/v1.0/stations")
def stations():
    """Return a JSON list of stations from the dataset."""
    # Create a new session for this request
    session = Session(engine)
    station_list = session.query(Station.station).all()
    stations = [station[0] for station in station_list]

    # Close the session
    session.close()
    
    return jsonify(stations)

from collections import OrderedDict

@app.route("/api/v1.0/tobs")
def tobs():
    """Return the temperature observations for the most active station within the previous 12 months as JSON."""
    
    # Calculate the date one year ago from the most recent date in the database
    most_recent_date = dt.datetime.strptime(session.query(func.max(Measurement.date)).scalar(), '%Y-%m-%d')
    one_year_ago = most_recent_date - dt.timedelta(days=365)
    
    # Query the station with the most activity within the previous year
    most_active_station = session.query(Measurement.station, func.count(Measurement.station)) \
        .filter(Measurement.date >= one_year_ago) \
        .group_by(Measurement.station) \
        .order_by(func.count(Measurement.station).desc()) \
        .first()
    
    most_active_station_id = most_active_station[0]
    
    # Get the station name of the most active station
    most_active_station_name = session.query(Station.name).filter(Station.station == most_active_station_id).scalar()
    
    # Query temperature observations for the most active station within the previous year
    tobs_data = session.query(Measurement.date, Measurement.tobs) \
        .filter(Measurement.station == most_active_station_id, Measurement.date >= one_year_ago) \
        .all()
    
    tobs_list = {
        "Data": [{"date": date, "temperature": tobs} for date, tobs in tobs_data],
        "Most Active Station": most_active_station_id,
        "Station Name": most_active_station_name
    }
    
    # Close the session
    session.close()

    return jsonify(tobs_list)







@app.route("/api/v1.0/<start>")
def temp_stats_start(start):
    """Return JSON list of TMIN, TAVG, and TMAX for all dates greater than or equal to the start date and less than or equal to the end date."""
    # Create a new session for this request
    session = Session(engine)
    
    # Calculate the maximum date in the dataset
    end_date = session.query(func.max(Measurement.date)).scalar()
    
    # Query temperature statistics for the specified date range
    results = session.query(Measurement.date, func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)) \
        .filter(Measurement.date >= start, Measurement.date <= end_date) \
        .all()
    
    # Close the session
    session.close()
    
    if results:
        temp_stats = [{"Date": result[0], "TMIN": result[1], "TAVG": result[2], "TMAX": result[3]} for result in results]
        return jsonify(temp_stats)
    else:
        return jsonify({"message": "No data available for the specified date range."}), 404  # Return a 404 status code for "Not Found"



@app.route("/api/v1.0/<start>/<end>")
def temp_stats_start_end(start, end):
    """Return JSON list of TMIN, TAVG, and TMAX for dates within the specified date range."""
    # Create a new session for this request
    session = Session(engine)
    
    results = session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)) \
        .filter(Measurement.date >= start, Measurement.date <= end) \
        .all()
    
    # Close the session
    session.close()
    
    if results:
        temp_stats = [{"Start Date": start, "End Date": end,"TMIN": result[0], "TAVG": result[1], "TMAX": result[2]} for result in results]
        return jsonify(temp_stats)
    else:
        return jsonify({"message": "No data available for the specified date range."}), 404  # Return a 404 status code for "Not Found"




if __name__ == "__main__":
    app.run(debug=True)
