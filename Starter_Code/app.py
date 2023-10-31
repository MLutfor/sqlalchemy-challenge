# Import the dependencies.
from flask import Flask, jsonify
import datetime as dt
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
        f"Welcome to the website!<br/>"
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation - Precipitation data for the last 12 months<br/>"
        f"/api/v1.0/stations - List of stations<br/>"
        f"/api/v1.0/tobs - Temperature observations for the most active station (last 12 months)<br/>"
        f"/api/v1.0/start_date - Temperature statistics (TMIN, TAVG, TMAX) from the start date to the latest date<br/>"
        f"/api/v1.0/start_date/end_date - Temperature statistics (TMIN, TAVG, TMAX) within the specified date range"
    )

@app.route("/api/v1.0/precipitation")
def precipitation():
    """Return the last 12 months of precipitation data as JSON."""
    last_date = session.query(func.max(Measurement.date)).scalar()
    last_date = dt.datetime.strptime(last_date, '%Y-%m-%d')
    one_year_ago = last_date - dt.timedelta(days=365)
    
    prcp_data = session.query(Measurement.date, Measurement.prcp).filter(Measurement.date >= one_year_ago).all()
    
    prcp_dict = {date: prcp for date, prcp in prcp_data}
    
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

@app.route("/api/v1.0/tobs")
def tobs():
    """Return the temperature observations for the most active station (last 12 months) as JSON."""
    most_active_station = session.query(Measurement.station, func.count(Measurement.station)) \
        .group_by(Measurement.station) \
        .order_by(func.count(Measurement.station).desc()) \
        .first()
    
    most_active_station_id = most_active_station[0]
    
    last_date = session.query(func.max(Measurement.date)) \
        .filter(Measurement.station == most_active_station_id) \
        .scalar()
    last_date = dt.datetime.strptime(last_date, '%Y-%m-%d')
    one_year_ago = last_date - dt.timedelta(days=365)
    
    tobs_data = session.query(Measurement.date, Measurement.tobs) \
        .filter(Measurement.station == most_active_station_id, Measurement.date >= one_year_ago) \
        .all()
    
    tobs_list = [{"date": date, "temperature": tobs} for date, tobs in tobs_data]
    
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
    """Return JSON list of TMIN, TAVG, and TMAX for the range between the first and last date in the date column."""
    # Create a new session for this request
    session = Session(engine)
    
    # Calculate the minimum and maximum dates in the date column
    first_date = session.query(func.min(Measurement.date)).scalar()
    last_date = session.query(func.max(Measurement.date)).scalar()
    
    # Calculate TMIN, TAVG, and TMAX for the entire date range
    result = session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)) \
        .filter(Measurement.date >= first_date, Measurement.date <= last_date) \
        .first()

    # Format the result
    temperature_stats = {
        "Start Date": first_date,
        "End Date": last_date,
        "TMIN": result[0],
        "TAVG": result[1],
        "TMAX": result[2]
    }
    
    # Close the session
    session.close()
    
    return jsonify(temperature_stats)



if __name__ == "__main__":
    app.run(debug=True)
