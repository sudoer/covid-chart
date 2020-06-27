#!/usr/bin/env python3

import argparse
import csv
import datetime
import json
import requests
import matplotlib.pyplot as plt
import matplotlib.dates
import os
import pandas
import dateutil.parser
import tkinter as tk  # sudo apt-get install python3-tk


def main():

    parser = argparse.ArgumentParser(description="Wake County COVID-19 grapher")
    parser.add_argument(
        "--avg",
        dest="avg",
        type=int,
        default=7,
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
    parser.add_argument(
        "--new",
        dest="new",
        action="store_true",
        default=False,
        help="new cases",
        required=False,
    )
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
    parser.add_argument(
        "--country",
        dest="country",
        default="US",
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
        help="start-date (YYYY-MM-DD)",
        required=False,
    )
    parser.add_argument(
        "--end-date",
        dest="end-date",
        default=None,
        help="start-date (YYYY-MM-DD)",
        required=False,
    )
    parser.add_argument(
        "--out",
        dest="out",
        default=None,
        help="save to file instead of opening window",
        required=False,
    )
    args = vars(parser.parse_args())
    print(json.dumps(args))

    if args["source"] == "wake":
        triplets = get_wake_data()
        location = "Wake County"
    elif args["source"] == "jhu":
        location = get_location(args["country"], args["state"], args["county"])
        triplets = get_jhu_data(
            args["jhu-data-dir"], args["country"], args["state"], args["county"]
        )
    else:
        raise Exception("unknown source '%s'", args['source'])

    series = list(zip(*triplets))

    df = pandas.DataFrame(data={"dates": series[0], "cases": series[1], "deaths": series[2]})
    df.diff = df.cases.diff()

    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    if args["log"]:
        ax.set_yscale("log")

    # And a corresponding grid
    ax.grid(which="both")

    # Or if you want different settings for the grids:
    ax.grid(which="minor", alpha=0.2)
    ax.grid(which="major", alpha=0.5)

    # format axis labels
    plt.xticks(rotation=45)
    fmt_mmdd = matplotlib.dates.DateFormatter("%m/%d")
    ax.xaxis.set_major_formatter(fmt_mmdd)

    series = df.cases
    if args["new"]:
        series = df.diff

    plt.plot_date(
        df.dates,
        series,
        xdate=True,
        ydate=False,
        label="%s cases" % "new" if args["new"] else "cumulative",
        marker=".",
        color="blue",
    )
    if args["avg"]:
        plt.plot_date(
            df.dates,
            series.rolling(window=args["avg"]).mean(),
            xdate=True,
            ydate=False,
            label="%d-day average" % args["avg"],
            marker=None,
            linestyle="solid",
            linewidth=2,
            color="orange",
        )

    title = "%s %s cases" % (location, "new" if args["new"] else "cumulative",)
    if args["avg"]:
        title = title + " (%s-day average)" % args["avg"]
    ax.set_title(title)
    ylabel = "%s cases" % ("new" if args["new"] else "cumulative")
    ax.set_ylabel(ylabel)

    # By default, start with the first recorded data.
    xmin = min(df.dates)
    if args["start-date"]:
        xmin = dateutil.parser.parse(args["start-date"])
    # By default, stop with yesterday's data (today's data is partial).
    xmax = max(df.dates) + datetime.timedelta(days=1)
    if args["end-date"]:
        xmax = dateutil.parser.parse(args["end-date"])

    ax.set_xlim([xmin, xmax])

    ylim = ax.get_ylim()
    ax.set_ylim([0, ylim[1]])

    if args["out"]:
        plt.savefig(args["out"])
    else:
        plt.show()


def get_location(country, state, county=None):
    if county:
        location = "%s, %s (%s)" % (county, state, country)
    elif state:
        location = "%s (%s)" % (state, country)
    else:
        location = "%s (all)" % country
    return location


def get_jhu_data(git_root, filter_country, filter_state, filter_county=None):

    dir_name = git_root + "/csse_covid_19_data/csse_covid_19_daily_reports"

    # Formats vary by date:

    # COVID-19/csse_covid_19_data/csse_covid_19_daily_reports/02-10-2020.csv
    # Province/State,Country/Region,Last Update,Confirmed,Deaths,Recovered
    # "Chicago, IL",US,2020-02-09T19:03:03,2,0,2
    # "San Benito, CA",US,2020-02-03T03:53:02,2,0,0

    # COVID-19/csse_covid_19_data/csse_covid_19_daily_reports/03-10-2020.csv
    # Province/State,Country/Region,Last Update,Confirmed,Deaths,Recovered,Latitude,Longitude
    # Washington,US,2020-03-10T22:13:11,267,23,1,47.4009,-121.4905
    # New York,US,2020-03-10T17:13:27,173,0,0,42.1657,-74.9481

    # COVID-19/csse_covid_19_data/csse_covid_19_daily_reports/04-10-2020.csv
    # FIPS,Admin2,Province_State,Country_Region,Last_Update,Lat,Long_,Confirmed,Deaths,Recovered,Active,Combined_Key
    # 45001,Abbeville,South Carolina,US,2020-04-10 22:54:07,34.22333378,-82.46170658,7,0,0,0,"Abbeville, South Carolina, US"
    # 22001,Acadia,Louisiana,US,2020-04-10 22:54:07,30.295064899999996,-92.41419698,94,4,0,0,"Acadia, Louisiana, US"


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

    results = []
    for file_name in sorted(os.listdir(dir_name)):
        if file_name.endswith(".csv"):
            date = datetime.datetime.strptime(file_name.split(".")[0], "%m-%d-%Y")
            total_cases = 0
            total_deaths = 0
            csv_filename = os.path.join(dir_name, file_name)
            with open(csv_filename) as csv_file_obj:

                csv_dict_reader = csv.DictReader(csv_file_obj)
                for row in csv_dict_reader:

                    csv_country = get_val_by_column_names(row, country_col)
                    csv_state = get_val_by_column_names(row, state_col)
                    csv_county = get_val_by_column_names(row, county_col)
                    csv_cases = get_val_by_column_names(row, cases_col, number=True)
                    csv_deaths = get_val_by_column_names(row, deaths_col, number=True)

                    if csv_country is not None and csv_country != filter_country:
                        continue

                    if filter_state is not None and csv_state != filter_state:
                        continue

                    if filter_county is not None and csv_county != filter_county:
                        continue

                    total_cases += int(csv_cases)
                    total_deaths += int(csv_deaths)

            if total_cases or total_deaths:
                results.append([date, total_cases, total_deaths])

    return results


def get_wake_data():

    # This POST was basically copied from the "view cases by day" graph on https://covid19.wakegov.com/
    # I am pretty sure it could be trimmed a bit... it looks like overkill.
    rsp = requests.post(
        "https://wabi-us-gov-virginia-api.analysis.usgovcloudapi.net/public/reports/querydata",
        params={"synchronous": True,},
        headers={
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
        },
        data=json.dumps(
            {
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
                                                {
                                                    "Name": "c",
                                                    "Entity": "Confirmed Cases",
                                                },
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
                                                            "SourceRef": {
                                                                "Source": "c1"
                                                            }
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
                                                                "SourceRef": {
                                                                    "Source": "c1"
                                                                }
                                                            },
                                                            "Property": "Date",
                                                        }
                                                    },
                                                }
                                            ],
                                        },
                                        "Binding": {
                                            "Primary": {
                                                "Groupings": [{"Projections": [0, 1]}]
                                            },
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
                            "Sources": [
                                {"ReportId": "52d29698-2a1e-4f66-b0da-4260ef93d895"}
                            ],
                        },
                    }
                ],
                "cancelQueries": [],
                "modelId": 318337,
            }
        ),
    )
    raw = json.loads(rsp.content)
    print(json.dumps(raw))
    result_set = raw["results"][0]["result"]["data"]["dsr"]["DS"][0]["PH"][0]["DM0"]
    results = [i["C"] for i in result_set]
    print(json.dumps(results))
    return [
        [datetime.datetime.fromtimestamp(r[0] / 1000), r[1]]
        for r in results
        if len(r) == 2
    ]


if __name__ == "__main__":
    main()
