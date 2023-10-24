"""Main script for """
import datetime as dt

import seaborn as sns

import src.daily_trains_functions as df
import src.daily_trains_config as cfg


def main():
    # Set up the scheduled runs of the train locator.
    df.schedule_train_locator(
        end_time=dt.datetime.now() + dt.timedelta(minutes=60),
        frequency=2,
        time_unit="m",
        save_dir="data/",
    )

    # Combine all the retrieved train location datasets.
    trains_df = df.combine_train_datasets(data_folder="data/")

    # Some of the trains do not have valid latitude and longitude values,
    # exclude these.
    trains_df = trains_df.loc[
        trains_df["train_latitude"].ne(0) | trains_df["train_longitude"].ne(0)
    ].reset_index(drop=True)

    # Create colour palette for all unique train codes to track individual
    # trains from one map to the next.
    trains = trains_df["train_code"].unique()
    colors = sns.color_palette("Paired", n_colors=len(trains)).as_hex()
    palette = dict(zip(trains, colors))

    # Create all Ireland maps and ones that specifically focus on Dublin and
    # Cork.
    for focus in ["ireland", "dublin", "cork"]:
        save_dir = eval(f"cfg.{focus.upper()}_MAPS_OUTPUT")
        location = eval(f"cfg.{focus.upper()}_CENTRE_POINT")
        if focus in ["dublin", "cork"]:
            zoom_start = 10
        else:
            zoom_start = 7

        # Create map for each time step.
        for time in trains_df["datetime"].unique():
            df.create_maps(
                trains_df,
                time,
                location,
                zoom_start,
                palette,
                train_lines="data/rail_network/Rail_Network_-_National_250k_Map_Of_Ireland.geojson",
                train_stations="data/rail_network/Railway_Stations_-_National_250k_Map_Of_Ireland.geojson",
                save_dir=save_dir,
            )

        # Get screenshots of each created map and save as png.
        df.get_screenshots_of_maps(save_dir)

        # Convert all pngs into a gif.
        df.create_gif_from_screen_shots(save_dir + "pngs/")


if __name__ == "__main__":
    main()
