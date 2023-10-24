"""Function to facilitate the daily trains analysis."""
import os
import time
import datetime as dt
from xml.etree import ElementTree

import folium
import requests
from selenium import webdriver
import imageio as io
import pandas as pd
import schedule

import src.daily_trains_config as cfg


def retrieve_current_train_positions(save_dir, verbose=True):
    """Function to retrieve the current train position from the Irish Rail API
    and parse the returned XML into a pandas DataFrame. Saves and returns the
    DataFrame."""

    # Determine start time.
    start_time = dt.datetime.now()
    if verbose:
        print("Retrieving trains at", start_time)

    # Send request to Irish Rail API for real time train positions.
    req = requests.get(cfg.IRISH_RAIL_REAL_TIME_TRAINS)

    # Response is in XML format so need to handle that.
    trains = ElementTree.fromstring(req.content)

    # Extract information for each train.
    train_codes = []
    train_statuses = []
    train_lats = []
    train_lons = []
    train_directions = []
    for train in trains:
        train_code = train.find(
            "{" + f"{cfg.IRISH_RAIL_API_BASE}" + "}TrainCode"
        ).text
        train_codes.append(train_code)

        train_status = train.find(
            "{" + f"{cfg.IRISH_RAIL_API_BASE}" + "}TrainStatus"
        ).text
        train_statuses.append(train_status)

        train_lat = train.find(
            "{" + f"{cfg.IRISH_RAIL_API_BASE}" + "}TrainLatitude"
        ).text
        train_lats.append(train_lat)

        train_lon = train.find(
            "{" + f"{cfg.IRISH_RAIL_API_BASE}" + "}TrainLongitude"
        ).text
        train_lons.append(train_lon)

        train_direction = train.find(
            "{" + f"{cfg.IRISH_RAIL_API_BASE}" + "}Direction"
        ).text
        train_directions.append(train_direction)

    # Create DataFrame, including time of query and save.
    trains_df = pd.DataFrame(
        data={
            "train_code": train_codes,
            "train_status": train_statuses,
            "train_latitude": train_lats,
            "train_longitude": train_lons,
            "train_direction": train_directions,
        }
    )
    trains_df["datetime"] = start_time

    trains_df.to_csv(save_dir + f"trains_{start_time}.csv")

    return trains_df


def schedule_train_locator(end_time, frequency, time_unit, **kwargs):
    """Function to schedule multiple repeated calls to the Irish Rail API at
    specified intervals until a set time is reached."""

    # Must be a valid time unit.
    if time_unit not in ["s", "m", "h", "d"]:
        raise ValueError("time unit must be one of 's', 'm', 'h' or 'd'")

    # Depending on time unit do task at specified interval.
    if time_unit == "s":
        schedule.every(frequency).seconds.until(end_time).do(
            retrieve_current_train_positions, **kwargs
        )
    elif time_unit == "m":
        schedule.every(frequency).minutes.until(end_time).do(
            retrieve_current_train_positions, **kwargs
        )
    elif time_unit == "h":
        schedule.every(frequency).hours.until(end_time).do(
            retrieve_current_train_positions, **kwargs
        )
    elif time_unit == "h":
        schedule.every(frequency).days.until(end_time).do(
            retrieve_current_train_positions, **kwargs
        )

    # Start the schedule running.
    while dt.datetime.now() < pd.to_datetime(end_time):
        schedule.run_pending()
        time.sleep(0.1)


def combine_train_datasets(data_folder):
    """Takes all the data returned from the scheduler and combines into a
    composite DataFrame."""

    trains_df = pd.DataFrame()
    for file in os.listdir(data_folder):
        if file.endswith(".csv"):
            train_df = pd.read_csv(data_folder + file, index_col="Unnamed: 0")
            trains_df = pd.concat([trains_df, train_df], ignore_index=True)
        else:
            continue

    trains_df["datetime"] = pd.to_datetime(trains_df["datetime"])

    return trains_df


def create_maps(
    trains_df,
    datetime,
    location,
    zoom_start,
    palette,
    train_lines,
    train_stations,
    save_dir,
):
    """Creates a Folium map that has a uniquely colored marker icon for each
    train in the dataset and also has layers for the railway lines and railway
    stations that come from GeoJSON files Ordnance Survey Ireland."""

    # Create save directory.
    os.makedirs(save_dir, exist_ok=True)

    # Create basic map.
    m = folium.Map(location=location, zoom_start=zoom_start)

    # Select all trains for the specified point in time.
    trains = trains_df.loc[trains_df["datetime"].eq(datetime), :]

    # Loop over these trains creating a marker and adding it to the Folium map.
    for _, train in trains.iterrows():
        train_lat = train["train_latitude"]
        train_lon = train["train_longitude"]
        train_code = train["train_code"]
        train_direction = train["train_direction"]
        folium.Marker(
            location=[train_lat, train_lon],
            popup=train_code + ": " + train_direction,
            icon=folium.Icon(
                icon_color=palette[train_code],
                color="black",
                prefix="fa",
                icon="train",
            ),
        ).add_to(m)

    # Add the GeoJson Layer from OSI for the railway network.
    rail_network = folium.GeoJson(train_lines, name="railway_network")
    rail_network.add_to(m)

    # Add the GeoJson Layer from OSI for the railway stations.
    # Use small black circular markers for each station.
    rail_stations = folium.GeoJson(
        train_stations,
        name="railway_stations",
        marker=folium.CircleMarker(
            radius=1,
            color="black",
        ),
    )
    rail_stations.add_to(m)

    folium.LayerControl().add_to(m)

    # Add a title to the map indicating what the time was that the train
    # locations correspond to.
    title_html = """
        <h3 align="left" style="font-size:22px"><b>{}</b></h3>
    """.format(
        "Datetime: " + str(datetime)
    )
    m.get_root().html.add_child(folium.Element(title_html))

    # Save Folium map.
    m.save(save_dir + f"trains_{datetime}.html")


def get_screenshots_of_maps(maps_dir):
    """In order to make a gif we need png images of each snapshot in time. This
    function open each .html Folium map in a browser and takes a .png
    screenshot."""

    # Create directory to save pngs.
    os.makedirs(maps_dir + "pngs/", exist_ok=True)

    # Loop over folium maps, open each in browser and take a screenshot.
    for folium_map in os.listdir(maps_dir):
        if folium_map.endswith(".html"):
            # Create path to file.
            file_path = "file://{path}/{maps_dir}/{map_file}".format(
                path=os.getcwd(), maps_dir=maps_dir, map_file=folium_map
            )
            ffox = webdriver.Firefox()
            ffox.get(file_path)

            # Allow file to load and then take screenshot.
            time.sleep(2)
            ffox.save_screenshot(
                maps_dir + f"pngs/{folium_map.replace('.html', '.png')}"
            )
            ffox.quit()
        else:
            continue


def create_gif_from_screen_shots(pngs_dir):
    """Take all screenshotted pngs in the pngs directory and create a GIF from
    them."""

    # Create save directory.
    os.makedirs(pngs_dir + "gif/", exist_ok=True)

    # Loop over screenshotted pngs adding all to a list.
    image_list = []
    for png in list(sorted(os.listdir(pngs_dir))):
        if png.endswith(".png"):
            image_list.append(io.imread(pngs_dir + png))
        else:
            continue

    # Some weird discrepancy in shapes for the Dublin region one so only take
    # images of the majority shape.
    shapes = [x.shape for x in image_list]
    majority_shape = max(set(shapes), key=shapes.count)
    image_list = [x for x in image_list if x.shape == majority_shape]

    # Create gif from image list.
    io.mimwrite(pngs_dir + "gif/trains.gif", image_list, fps=2)
