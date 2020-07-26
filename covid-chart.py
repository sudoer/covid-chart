#!/usr/bin/env python3

import argparse
import csv
import datetime
import dateutil.parser
import json
import matplotlib.pyplot as plt
import matplotlib.dates
import os
import pandas
import re
import requests
import sys
import tkinter as tk  # sudo apt-get install python3-tk
from collections import defaultdict


debug = False


def main():

    parser = argparse.ArgumentParser(description="COVID-19 grapher")

    # DATA SOURCE OPTIONS

    parser.add_argument(
        "--source", dest="source", default="jhu", help="jhu or wake", required=False
    )
    parser.add_argument(
        "--jhu-data-dir",
        dest="jhu-data-dir",
        default="COVID-19",
        help="name of JHU git directory",
        required=False,
    )

    # DATA SELECTION OPTIONS

    parser.add_argument(
        "--new",
        dest="new",
        action="store_true",
        default=False,
        help="new cases",
        required=False,
    )
    parser.add_argument(
        "--deaths",
        dest="deaths",
        action="store_true",
        default=False,
        help="graph deaths rather than cases",
        required=False,
    )
    parser.add_argument(
        "--country",
        dest="country",
        default=None,
        help="country (JHU data only)",
        required=False,
    )
    parser.add_argument(
        "--state",
        dest="state",
        default=None,
        help="US state (JHU data only)",
        required=False,
    )
    parser.add_argument(
        "--county",
        dest="county",
        default=None,
        help="US county (JHU data only)",
        required=False,
    )
    parser.add_argument(
        "--start-date",
        dest="start-date",
        default=None,
        help="start date of chart, but not of data (YYYY-MM-DD)",
        required=False,
    )
    parser.add_argument(
        "--end-date",
        dest="end-date",
        default=None,
        help="end-date of chart and data (YYYY-MM-DD)",
        required=False,
    )

    # CHART OPTIONS

    parser.add_argument(
        "--avg",
        dest="avg",
        type=int,
        default=None,
        help="size of sliding average",
        required=False,
    )
    parser.add_argument(
        "--log",
        dest="log",
        action="store_true",
        default=False,
        help="logarithmic scale",
        required=False,
    )

    # OUTPUT OPTIONS

    parser.add_argument(
        "--summary",
        dest="summary",
        default=False,
        action="store_true",
        help="print summary of latest information to stdout",
        required=False,
    )
    parser.add_argument(
        "--locations",
        dest="locations",
        default=False,
        action="store_true",
        help="print list of valid combinations of country, state, county",
        required=False,
    )
    parser.add_argument(
        "--bulk",
        dest="bulk",
        action="store_true",
        default=False,
        help="output option: save all data as PNGs using default filenames",
        required=False,
    )
    parser.add_argument(
        "--out",
        dest="out",
        default=None,
        help="output option: save one graph to file with this filename",
        required=False,
    )

    # IMAGE FORMATTING OPTIONS

    parser.add_argument(
        "--inches",
        dest="inches",
        type=str,
        default=None,
        help="size in inches (WWxHH)",
        required=False,
    )
    parser.add_argument(
        "--dpi",
        dest="dpi",
        type=int,
        default=None,
        help="dots per inch",
        required=False,
    )

    # DEBUG

    parser.add_argument(
        "--debug",
        dest="debug",
        action="store_true",
        default=False,
        help="print extra debug info",
        required=False,
    )

    args = vars(parser.parse_args())
    global debug
    debug = args.pop("debug")

    read_data_and_generate_charts(args)


def read_data_and_generate_charts(args):

    all_loc_data = None
    location_key = None

    # DATA SOURCES

    source = args.pop("source")
    if source == "wake":
        location_key = join_location_key("US", "North Carolina", "Wake")
        all_loc_data = get_wake_data(location_key)
    elif source == "jhu":
        # We'll set location_key here, assuming we're going to make a single chart.
        location_key = join_location_key(args["country"], args["state"], args["county"])
        all_loc_data = get_jhu_data(args.pop("jhu-data-dir"))
    else:
        exit_on_error("unknown source '%s'" % source)

    if debug:
        print(json.dumps(all_loc_data))

    # CHART FILTERS AND OPTIONS

    new = args.pop("new")
    deaths = args.pop("deaths")
    out = args.pop("out")
    country_filter = args.pop("country")
    state_filter = args.pop("state")
    county_filter = args.pop("county")

    # TEXT SUMMARY

    if args.pop("summary"):
        summary(all_loc_data, location_key, args["end-date"])
    elif args.pop("locations"):
        for location_string in sorted(
            ["%s;%s;%s" % loc for loc in all_loc_data.keys()]
        ):
            print(location_string)

    # BULK PROCESSING OF ALL CHARTS

    elif args.pop("bulk"):
        filtered_index = 0
        all_locations = all_loc_data.keys()
        for unfiltered_index, location_key in enumerate(all_locations, 1):
            country, state, county = split_location_key(location_key)
            if country_filter and country != country_filter:
                continue
            if state_filter and state != state_filter:
                continue
            if county_filter and county != county_filter:
                continue
            filtered_index += 1
            prefix = "#%d (location %d of %d)" % (
                filtered_index,
                unfiltered_index,
                len(all_locations),
            )
            generate_chart(
                all_loc_data,
                location_key,
                True,
                True,
                args,
                out,
                bulk=True,
                prefix=prefix,
            )
            generate_chart(
                all_loc_data,
                location_key,
                True,
                False,
                args,
                out,
                bulk=True,
                prefix=prefix,
            )
            generate_chart(
                all_loc_data,
                location_key,
                False,
                True,
                args,
                out,
                bulk=True,
                prefix=prefix,
            )
            generate_chart(
                all_loc_data,
                location_key,
                False,
                False,
                args,
                out,
                bulk=True,
                prefix=prefix,
            )
            summary_fullpath = build_full_file_path(out, location_key, "summary.txt")
            print("%s %s" % (prefix, summary_fullpath))
            summary(all_loc_data, location_key, args["end-date"], summary_fullpath)

    # SINGLE CHART

    else:
        generate_chart(all_loc_data, location_key, new, deaths, args, out)


def get_location_string(location_key):
    country, state, county = split_location_key(location_key)
    if county:
        location_string = "%s, %s [%s]" % (county, state, country)
    elif state:
        location_string = "%s [%s]" % (state, country)
    else:
        location_string = "%s [all]" % country
    return location_string


def join_location_key(country, state, county):
    return "%s|%s|%s" % (country or "*", state or "*", county or "*")


def split_location_key(key):
    country, state, county = key.split("|")
    country = None if country == "*" else country
    state = None if state == "*" else state
    county = None if county == "*" else county
    return country, state, county


def build_full_file_path(top_dir, location_key, filename):
    country, state, county = split_location_key(location_key)
    country = re.sub("[^0-9a-zA-Z]+", "_", (country or "").lower()).strip("_")
    state = re.sub("[^0-9a-zA-Z]+", "_", (state or "").lower()).strip("_")
    county = re.sub("[^0-9a-zA-Z]+", "_", (county or "").lower()).strip("_")
    return "/".join(
        [x for x in filter(None, (top_dir, country, state, county, filename))]
    )


def get_location_dataframe(datadict, location_index):
    location_data = datadict.get(location_index)
    if not location_data:
        return None
    return pandas.DataFrame(
        data={
            "dates": [
                datetime.date.fromisoformat(date_str) for date_str in location_data
            ],
            "cases": [location_data[date_str]["cases"] for date_str in location_data],
            "deaths": [location_data[date_str]["deaths"] for date_str in location_data],
        }
    )


def summary(datadict, location_key, end_date_str, outfile=None):
    country, state, county = split_location_key(location_key)
    output = ""
    output += "country: %s\n" % (country or "ALL")
    output += "state: %s\n" % (state or "ALL")
    output += "county: %s\n" % (county or "ALL")
    df = get_location_dataframe(datadict, location_key)
    if df is None:
        output += "no matching data\n"
    else:
        end_date = parse_date("yesterday")
        if end_date_str:
            end_date = parse_date(end_date_str)
        data = df[df.dates <= end_date]
        output += "date: %s\n" % data.dates.iat[-1].strftime("%Y-%m-%d")
        output += "cases: %s\n" % data.cases.iat[-1]
        output += "deaths: %s\n" % data.deaths.iat[-1]
    if outfile:
        with open(outfile, "w") as file_obj:
            print(output, file=file_obj)
    else:
        print(output)


def generate_chart(
    datadict, location_key, new, deaths, format_opts, out, bulk=False, prefix=""
):

    df = get_location_dataframe(datadict, location_key)
    if df is None:
        return False

    # display size
    if format_opts["inches"]:
        x_inches, y_inches = format_opts["inches"].split("x")
        fig = plt.figure(figsize=(int(x_inches), int(y_inches)))
    else:
        fig = plt.figure()

    if format_opts["dpi"]:
        fig.set_dpi(format_opts["dpi"])

    ax = fig.add_subplot(1, 1, 1)

    # X axis is a date
    ax.xaxis_date()
    # X axis labels
    plt.xticks(rotation=45)
    fmt_mmdd = matplotlib.dates.DateFormatter("%m/%d")
    ax.xaxis.set_major_formatter(fmt_mmdd)

    # Y axis can be linear or logarithmic
    if format_opts["log"]:
        ax.set_yscale("log")
    ax.ticklabel_format(axis="y", style="plain")

    # And a corresponding grid
    ## ax.grid(which="both")
    ax.grid(which="minor", alpha=0.2)
    ax.grid(which="major", alpha=0.5)

    # Which data do we graph
    series = df.cases
    if deaths:
        series = df.deaths
    if new:
        series = series.diff()

    # Show moving average if we're looking at NEW cases/deaths.
    moving_average = format_opts["avg"]
    if moving_average is None and new:
        moving_average = 7

    # Colors
    series_color = "blue"
    avg_color = "orange"
    if deaths:
        series_color = "darkred"
        avg_color = "black"

    # Title and labels
    basic_label = "%s %s" % (
        "new" if new else "cumulative",
        "deaths" if deaths else "cases",
    )
    title = "%s %s" % (get_location_string(location_key), basic_label)
    series_label = basic_label
    if moving_average:
        series_label += " (%s-day average)" % moving_average
    plt.suptitle(title, fontsize=18)
    subtitle = datetime.datetime.now().strftime("generated on %Y-%m-%d at %H:%M:%S")
    plt.title(subtitle, fontsize=10)
    ax.set_ylabel(series_label)

    # Charts of NEW cases/deaths should be bar charts.
    # It emphasizes the volume under the curve.
    bar_chart = False
    if new:
        bar_chart = True
    if format_opts["log"]:
        bar_chart = False

    if bar_chart:
        plt.bar(
            df.dates,
            series,
            width=0.8,
            bottom=None,
            align="center",
            label=series_label,
            color=series_color,
        )
    else:
        plt.plot_date(
            df.dates,
            series,
            xdate=True,
            ydate=False,
            label=series_label,
            marker=".",
            color=series_color,
        )
    if moving_average:
        plt.plot_date(
            df.dates,
            series.rolling(window=moving_average).mean(),
            xdate=True,
            ydate=False,
            label="%d-day average" % moving_average,
            marker=None,
            linestyle="solid",
            linewidth=2,
            color=avg_color,
        )

    # X limits
    # By default, start with the first recorded data.
    start_date = min(df.dates)
    if format_opts["start-date"]:
        start_date = parse_date(format_opts["start-date"])
    # By default, stop with today's data (even though it is sometimes partial).
    end_date = parse_date("today")
    if format_opts["end-date"]:
        end_date = parse_date(format_opts["end-date"])
    ax.set_xlim([start_date, end_date])

    # Y limits
    ylim = ax.get_ylim()
    ax.set_ylim([0, ylim[1]])

    if bulk:
        png_filename = "%s-%s.png" % (
            "new" if new else "cumulative",
            "deaths" if deaths else "cases",
        )
        png_fullpath = build_full_file_path(out, location_key, png_filename)
        dirname = os.path.dirname(png_fullpath)
        os.makedirs(dirname, exist_ok=True)
        print("%s %s" % (prefix, png_fullpath))
        plt.savefig(png_fullpath)
    elif not out:
        print("showing chart: %s" % title)
        plt.show()
    else:
        print("saving %s" % out)
        plt.savefig(out)
    plt.close("all")


def exit_on_error(string):
    print(string)
    sys.exit(1)


def parse_date(date_string):
    today = datetime.date.today()
    if date_string.lower() == "today":
        return today
    if date_string.lower() == "yesterday":
        return today - datetime.timedelta(days=1)
    if date_string.lower() == "tomorrow":
        return today + datetime.timedelta(days=1)
    dt = dateutil.parser.parse(date_string)
    if dt:
        return dt.date()
    return None


def get_jhu_data(git_root):

    dir_name = git_root + "/csse_covid_19_data/csse_covid_19_daily_reports"

    # Formats have changed over time:

    # first seen in COVID-19/csse_covid_19_data/csse_covid_19_daily_reports/01-22-2020.csv
    # Province/State,Country/Region,Last Update,Confirmed,Deaths,Recovered
    # "Chicago, IL",US,2020-02-09T19:03:03,2,0,2
    # "San Benito, CA",US,2020-02-03T03:53:02,2,0,0

    # first seen in COVID-19/csse_covid_19_data/csse_covid_19_daily_reports/03-01-2020.csv
    # Province/State,Country/Region,Last Update,Confirmed,Deaths,Recovered,Latitude,Longitude
    # Washington,US,2020-03-10T22:13:11,267,23,1,47.4009,-121.4905
    # New York,US,2020-03-10T17:13:27,173,0,0,42.1657,-74.9481

    # first seen in COVID-19/csse_covid_19_data/csse_covid_19_daily_reports/03-22-2020.csv
    # FIPS,Admin2,Province_State,Country_Region,Last_Update,Lat,Long_,Confirmed,Deaths,Recovered,Active,Combined_Key
    # 45001,Abbeville,South Carolina,US,2020-04-10 22:54:07,34.22333378,-82.46170658,7,0,0,0,"Abbeville, South Carolina, US"
    # 22001,Acadia,Louisiana,US,2020-04-10 22:54:07,30.295064899999996,-92.41419698,94,4,0,0,"Acadia, Louisiana, US"

    # first seen in COVID-19/csse_covid_19_data/csse_covid_19_daily_reports/05-29-2020.csv
    # FIPS,Admin2,Province_State,Country_Region,Last_Update,Lat,Long_,Confirmed,Deaths,Recovered,Active,Combined_Key,Incidence_Rate,Case-Fatality_Ratio
    # 45001,Abbeville,South Carolina,US,2020-06-22 04:33:20,34.22333378,-82.46170658,88,0,0,88,"Abbeville, South Carolina, US",358.78827414685856,0.0

    country_col = ["Country/Region", "Country_Region"]
    state_col = ["Province/State", "Province_State"]
    county_col = ["Admin2"]
    cases_col = ["Confirmed"]
    deaths_col = ["Deaths"]

    def get_val_by_column_names(row, col_names, number=False):
        for col_name in col_names:
            if col_name in row:
                val = row[col_name]
                if number:
                    try:
                        val = int(val)
                    except ValueError:
                        val = 0
                return val
        if number:
            return 0
        return None

    # store all results in a multi-level dictionary, format:
    # results['US|North Carolina|Wake']['2020-07-03'] = { 'cases': 5000, 'deaths': 20 }
    results = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    for file_name in sorted(os.listdir(dir_name)):
        if file_name.endswith(".csv"):
            file_prefix = file_name.split(".")[0]
            csv_datetime = datetime.datetime.strptime(file_prefix, "%m-%d-%Y")
            if not csv_datetime:
                continue
            date_str = csv_datetime.strftime("%Y-%m-%d")
            csv_filename = os.path.join(dir_name, file_name)
            with open(csv_filename) as csv_file_obj:

                csv_dict_reader = csv.DictReader(csv_file_obj)
                for row in csv_dict_reader:

                    csv_country = get_val_by_column_names(row, country_col)
                    csv_state = get_val_by_column_names(row, state_col)
                    csv_county = get_val_by_column_names(row, county_col)
                    csv_cases = get_val_by_column_names(row, cases_col, number=True)
                    csv_deaths = get_val_by_column_names(row, deaths_col, number=True)

                    # Save values at all appropriate levels
                    location_keys = [
                        join_location_key(None, None, None),
                        join_location_key(csv_country, None, None),
                        join_location_key(csv_country, csv_state, None),
                        join_location_key(csv_country, csv_state, csv_county),
                    ]
                    # Do not add values to the same level twice.
                    for location_key in set(location_keys):
                        # location_key = join_location_key(*country_state_county)
                        results[location_key][date_str]["cases"] += csv_cases
                        results[location_key][date_str]["deaths"] += csv_deaths
                        if debug:
                            print(
                                "date=%s, location=%s, cases=%d, deaths=%d"
                                % (date_str, location_key, csv_cases, csv_deaths)
                            )

    return results


def get_wake_data(location_key):

    # This POST was basically copied from the "view cases by day" graph on https://covid19.wakegov.com/
    # I am pretty sure it could be trimmed a bit... it looks like overkill.

    case_query = {
        "version": "1.0.0",
        "queries": [
            {
                "Query": {
                    "Commands": [
                        {
                            "SemanticQueryDataShapeCommand": {
                                "Query": {
                                    "Version": 2,
                                    "From": [
                                        {"Name": "c", "Entity": "Confirmed Cases"},
                                        {"Name": "c1", "Entity": "Calendar"},
                                    ],
                                    "Select": [
                                        {
                                            "Measure": {
                                                "Expression": {
                                                    "SourceRef": {"Source": "c"}
                                                },
                                                "Property": "Running Total",
                                            },
                                            "Name": "Confirmed Cases.Count of Event ID running total in Specimen Date",
                                        },
                                        {
                                            "Column": {
                                                "Expression": {
                                                    "SourceRef": {"Source": "c1"}
                                                },
                                                "Property": "Date",
                                            },
                                            "Name": "Calendar.Date",
                                        },
                                    ],
                                    "OrderBy": [
                                        {
                                            "Direction": 1,
                                            "Expression": {
                                                "Column": {
                                                    "Expression": {
                                                        "SourceRef": {"Source": "c1"}
                                                    },
                                                    "Property": "Date",
                                                }
                                            },
                                        }
                                    ],
                                },
                                "Binding": {
                                    "Primary": {"Groupings": [{"Projections": [0, 1]}]},
                                    "DataReduction": {
                                        "DataVolume": 4,
                                        "Primary": {"Window": {"Count": 1000}},
                                    },
                                    "Version": 1,
                                },
                            }
                        }
                    ]
                },
                "CacheKey": '{"Commands":[{"SemanticQueryDataShapeCommand":{"Query":{"Version":2,"From":[{"Name":"c","Entity":"Confirmed Cases"},{"Name":"c1","Entity":"Calendar"}],"Select":[{"Measure":{"Expression":{"SourceRef":{"Source":"c"}},"Property":"Running Total"},"Name":"Confirmed Cases.Count of Event ID running total in Specimen Date"},{"Column":{"Expression":{"SourceRef":{"Source":"c1"}},"Property":"Date"},"Name":"Calendar.Date"}],"OrderBy":[{"Direction":1,"Expression":{"Column":{"Expression":{"SourceRef":{"Source":"c1"}},"Property":"Date"}}}]},"Binding":{"Primary":{"Groupings":[{"Projections":[0,1]}]},"DataReduction":{"DataVolume":4,"Primary":{"Window":{"Count":1000}}},"Version":1}}}]}',
                "QueryId": "",
                "ApplicationContext": {
                    "DatasetId": "bd7fc819-b88a-41d0-a830-7a8dac4576ff",
                    "Sources": [{"ReportId": "52d29698-2a1e-4f66-b0da-4260ef93d895"}],
                },
            }
        ],
        "cancelQueries": [],
        "modelId": 318337,
    }

    # SET-UP

    results = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))

    url = "https://wabi-us-gov-virginia-api.analysis.usgovcloudapi.net/public/reports/querydata"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:76.0) Gecko/20100101 Firefox/76.0",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.5",
        "ActivityId": "227c0d27-d110-4ceb-81e1-917410272b35",
        "RequestId": "3edeb143-cc51-c79f-783a-8824a6eebb22",
        "X-PowerBI-ResourceKey": "52058879-6138-46ea-849c-4134a23b838e",
        "Content-Type": "application/json;charset=UTF-8",
        "Origin": "https://app.powerbigov.us",
        "DNT": "1",
        "Connection": "keep-alive",
        "Referer": "https://app.powerbigov.us/view?r=eyJrIjoiNTIwNTg4NzktNjEzOC00NmVhLTg0OWMtNDEzNGEyM2I4MzhlIiwidCI6ImM1YTQxMmQxLTNhYmYtNDNhNC04YzViLTRhNTNhNmNjMGYyZiJ9",
    }

    # CASES

    rsp = requests.post(
        url, params={"synchronous": True}, headers=headers, data=json.dumps(case_query)
    )
    raw = json.loads(rsp.content)

    ## print(json.dumps(raw))
    result_set = raw["results"][0]["result"]["data"]["dsr"]["DS"][0]["PH"][0]["DM0"]
    for i in result_set:
        result_list = i["C"]
        if len(result_list) == 2:
            data_datetime = datetime.datetime.fromtimestamp(result_list[0] / 1000)
            date_str = data_datetime.strftime("%Y-%m-%d")
            cases = result_list[1]
            results[location_key][date_str]["cases"] += int(cases)
            results[location_key][date_str]["deaths"] += 0

    # DEATHS

    death_query = case_query.copy()
    death_query["queries"][0]["Query"]["Commands"][0]["SemanticQueryDataShapeCommand"][
        "Query"
    ]["From"][0] = {"Name": "d", "Entity": "Deaths"}
    death_query["queries"][0]["Query"]["Commands"][0]["SemanticQueryDataShapeCommand"][
        "Query"
    ]["Select"][0] = {
        "Measure": {"Expression": {"SourceRef": {"Source": "d"}}, "Property": "Deaths"},
        "Name": "Deaths.Deaths",
    }

    rsp = requests.post(
        url, params={"synchronous": True}, headers=headers, data=json.dumps(death_query)
    )
    raw = json.loads(rsp.content)

    ## print(json.dumps(raw))
    result_set = raw["results"][0]["result"]["data"]["dsr"]["DS"][0]["PH"][0]["DM0"]
    cumulative_deaths = 0
    for i in result_set:
        result_list = i["C"]
        if len(result_list) == 2:
            data_datetime = datetime.datetime.fromtimestamp(result_list[0] / 1000)
            date_str = data_datetime.strftime("%Y-%m-%d")
            deaths = int(result_list[1])
            cumulative_deaths += deaths
            results[location_key][date_str]["cases"] += 0
            results[location_key][date_str]["deaths"] += cumulative_deaths

    return results


if __name__ == "__main__":
    main()
