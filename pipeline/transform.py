"""Pipeline Script: Transforming pipeline data"""

from datetime import datetime
import pandas as pd
from pandas import DataFrame


def load_data(csv_path: str) -> DataFrame:
    """
    Load data from a .csv file and
    return the data as a DataFrame
    """
    try:
        data = pd.read_csv(csv_path)
        return data

    except FileNotFoundError:
        print("Error loading .csv data: FileNotFound")
        return None


def hhmmss_to_timestamp(time_string: str): #pargma: no cover
    """
    Takes a 'time' string in the form
    'HHMMSS' and returns a valid timestamp
    """
    try:
        hh_value = int(time_string[:2])
        mm_value = int(time_string[2:4])
        ss_value = int(time_string[4:])
        datetime_value = datetime.now().replace(hour=hh_value, minute=mm_value,
                                                second=ss_value, microsecond=0)
        timestamp = datetime_value.timestamp()
        return timestamp

    except ValueError:
        print("Valid 'HHMMSS' time string must be provided")
        return None


def create_timestamp_from_date_and_time(df: DataFrame, new_column_name: str,
                                         date_column_name: str, time_column_name: str) -> DataFrame:
    """
    Takes a DataFrame, the name of a column
    containing dates, and the name of a column
    containing times, and creates a new column
    with datetime timestamps
    """
    try:
        df[date_column_name] = pd.to_datetime(df[date_column_name], format='%Y-%m-%d')

    except ValueError:
        print("Error: invalid values in date column")
        return None

    try:
        df[time_column_name] = pd.to_datetime(df[time_column_name], format='%H%M%S')

    except ValueError:
        print("Error: invalid values in time column")
        return None

    df[new_column_name] = df[date_column_name] + pd.to_timedelta(
        df[time_column_name].dt.strftime('%H:%M:%S'))
    return df


def replace_non_integers_with_none(df: DataFrame, column_name: str) -> DataFrame:
    """
    Replaces values with None if they aren't
    a positive or negative integer
    """
    df[column_name] = df[column_name].apply(lambda x: int(x)
                                            if str(x).lstrip('-').isdigit()
                                            else None)

    return df


def check_values_in_column_have_three_characters(df: DataFrame, column_name: str, drop_row: bool) -> DataFrame:
    """
    Checks that values in the specified column
    have a length of 3 characters. Optionally drops
    rows if the value is not 3 characters long;
    otherwise, replaces the value with None
    """
    df[column_name] = df[column_name].apply(lambda x: str(x).strip().upper()
                                            if len(str(x).strip()) == 3
                                            else None)

    if drop_row:
        df.dropna(subset=[column_name], inplace=True)

    return df


def generate_list_of_valid_cancel_codes(cancel_codes_url: str) -> DataFrame:
    """
    Loads a DataFrame from the given URL and
    extracts a list of known cancel codes
    from the DataFrame
    """
    cancel_codes_df = pd.read_html(cancel_codes_url, flavor="bs4", attrs={"class": "wikitable"})[0]
    valid_codes_list = cancel_codes_df["Code"].tolist()
    return valid_codes_list


def determine_if_cancel_code_is_valid(service_df: DataFrame, valid_codes_list: list) -> DataFrame:
    """
    Determines if a value is a valid cancel code,
    based on the list; otherwise, the value is
    replaced with None
    """
    service_df["cancel_code"] = service_df["cancel_code"].apply(lambda x: str(x).strip().upper()
                                                                if str(x).strip().upper() in valid_codes_list
                                                                else None)
    return service_df


if __name__ == "__main__": #pragma: no cover

    input_csv_path = "service_data.csv"

    service_df = load_data(input_csv_path)

    service_df = create_timestamp_from_date_and_time(service_df,
                                                     "scheduled_arrival_datetime",
                                                     "scheduled_arrival_date",
                                                     "scheduled_arrival_time")
    
    service_df = create_timestamp_from_date_and_time(service_df,
                                                     "origin_run_datetime",
                                                     "origin_run_date",
                                                     "origin_run_time")
        
    # Works to replace a lateness value with None if the service was cancelled at origin
    service_df = replace_non_integers_with_none(service_df, "arrival_lateness")
    
    service_df = check_values_in_column_have_three_characters(service_df, "origin_crs", True)
    service_df = check_values_in_column_have_three_characters(service_df, "planned_final_crs", True)
    service_df = check_values_in_column_have_three_characters(service_df, "destination_reached_crs", True)
    service_df = check_values_in_column_have_three_characters(service_df, "cancellation_station_crs", False)

    cancel_codes_url = "https://wiki.openraildata.com/index.php/Delay_Attribution_Guide"
    valid_cancel_codes = generate_list_of_valid_cancel_codes(cancel_codes_url)
    service_df = determine_if_cancel_code_is_valid(service_df, valid_cancel_codes)

    output_csv_path = "transformed_service_data.csv"

    service_df.to_csv(output_csv_path)
