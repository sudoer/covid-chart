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
import tkinter as tk  # sudo apt-get install python3-tk


def main():

    parser = argparse.ArgumentParser(description='Wake County COVID-19 grapher')
    parser.add_argument('--avg', dest='avg', type=int, default=7, help='size of sliding average', required=False)
    parser.add_argument('--log', dest='log', action='store_true', default=False, help='logarithmic scale', required=False)
    parser.add_argument('--new', dest='new', action='store_true', default=False, help='new cases', required=False)
    parser.add_argument('--source', dest='source', default='jhu', help='jhu or wake', required=False)
    parser.add_argument('--jhu-data-dir', dest='jhu-data-dir', default='COVID-19', help='name of JHU git directory', required=False)
    parser.add_argument('--county', dest='county', default=None, help='US county (JHU data only)', required=False)
    parser.add_argument('--state', dest='state', default=None, help='US state (JHU data only)', required=False)
    parser.add_argument('--country', dest='country', default='US', help='country (JHU data only)', required=False)
    args = vars(parser.parse_args())
    print(json.dumps(args))

    if args['source'] == 'wake':
        pairs = get_wake_data()
        location = 'Wake County'
    if args['source'] == 'jhu':
        location = get_location(args['country'], args['state'], args['county'])
        pairs = get_jhu_data(args['jhu-data-dir'], args['country'], args['state'], args['county'])
    # Remove today's partial-day numbers.
    pairs.pop(-1)
    series = list(zip(*pairs))

    df = pandas.DataFrame(data={
        'dates': series[0],
        'cases': series[1],
    })
    df.diff = df.cases.diff()


    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    if args['log']:
        ax.set_yscale('log')

    # And a corresponding grid
    ax.grid(which='both')

    # Or if you want different settings for the grids:
    ax.grid(which='minor', alpha=0.2)
    ax.grid(which='major', alpha=0.5)

    # format axis labels
    plt.xticks(rotation=45)
    fmt_mmdd = matplotlib.dates.DateFormatter('%m/%d')
    ax.xaxis.set_major_formatter(fmt_mmdd)

    series = df.cases
    if args['new']:
        series = df.diff

    plt.plot_date(df.dates, series,
        xdate=True, ydate=False,
        label='%s cases' % 'new' if args['new'] else 'cumulative',
        marker='.',
        color='blue')
    plt.plot_date(df.dates, series.rolling(window=args['avg']).mean(),
        xdate=True, ydate=False,
        label='%d-day average' % args['avg'],
        marker=None,
        linestyle='solid', linewidth=2,
        color='orange')

    title = '%s %s cases' % (
        location,
        'new' if args['new'] else 'cumulative',
    )
    ax.set_title(title)
    ylabel = '%s cases' % ('new' if args['new'] else 'cumulative')
    ax.set_ylabel(ylabel)

    plt.show()


def get_location(country, state, county=None):
    if county:
        location = '%s county, %s (%s)' % (county, state, country)
    else:
        location = '%s (%s)' % (state, country)
    return location


def get_jhu_data(git_root, country, state, county=None):
    results = []
    if county:
        # COUNTY LEVEL data
        dir_name = git_root + '/csse_covid_19_data/csse_covid_19_daily_reports'
        # FIPS,Admin2,Province_State,Country_Region,Last_Update,Lat,Long_,Confirmed,Deaths,Recovered,Active,Combined_Key,Incidence_Rate,Case-Fatality_Ratio
        # 45001,Abbeville,South Carolina,US,2020-06-22 04:33:20,34.22333378,-82.46170658,88,0,0,88,"Abbeville, South Carolina, US",358.78827414685856,0.0
        country_col = 3
        state_col = 2
        county_col = 1
        case_col = 7
    else:
        # STATE and COUNTRY LEVEL data
        dir_name = git_root + '/csse_covid_19_data/csse_covid_19_daily_reports_us'
        # Province_State,Country_Region,Last_Update,Lat,Long_,Confirmed,Deaths,Recovered,Active,FIPS,Incident_Rate,People_Tested,People_Hospitalized,Mortality_Rate,UID,ISO3,Testing_Rate,Hospitalization_Rate
        # Alabama,US,2020-06-22 04:33:33,32.3182,-86.9023,30021,839,15974,13208.0,1,612.2754903190478,344678,2460,2.794710369408081,84000001,USA,7029.675608813455,8.194264015189367
        country_col = 1
        state_col = 0
        county_col = None
        case_col = 5
    for file_name in sorted(os.listdir(dir_name)):
        if file_name.endswith(".csv"):
            date = datetime.datetime.strptime(file_name.split('.')[0], '%m-%d-%Y')
            total_cases = 0
            csv_filename = os.path.join(dir_name, file_name)
            with open(csv_filename) as csvfile:
                reader = csv.reader(csvfile)
                for row in reader:

                    if row[country_col] != country:
                        continue

                    if state is None:
                        total_cases += int(row[case_col])
                        continue
                    elif row[state_col] != state:
                        continue
                    else:
                        # state was given and it matches
                        pass

                    if county is not None and row[county_col] != county:
                        continue

                    results.append([date, int(row[case_col])])

            if state is None:
                results.append([date, total_cases])

    return results


def get_wake_data():

    # This POST was basically copied from the "view cases by day" graph on https://covid19.wakegov.com/
    # I am pretty sure it could be trimmed a bit... it looks like overkill.
    rsp = requests.post('https://wabi-us-gov-virginia-api.analysis.usgovcloudapi.net/public/reports/querydata',
        params={
            'synchronous': True,
        },
        headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:76.0) Gecko/20100101 Firefox/76.0',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.5',
            'ActivityId': '227c0d27-d110-4ceb-81e1-917410272b35',
            'RequestId': '3edeb143-cc51-c79f-783a-8824a6eebb22',
            'X-PowerBI-ResourceKey': '52058879-6138-46ea-849c-4134a23b838e',
            'Content-Type': 'application/json;charset=UTF-8',
            'Origin': 'https://app.powerbigov.us',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Referer': 'https://app.powerbigov.us/view?r=eyJrIjoiNTIwNTg4NzktNjEzOC00NmVhLTg0OWMtNDEzNGEyM2I4MzhlIiwidCI6ImM1YTQxMmQxLTNhYmYtNDNhNC04YzViLTRhNTNhNmNjMGYyZiJ9',
        },
        data=json.dumps({
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
                            { "Name": "c", "Entity": "Confirmed Cases" },
                            { "Name": "c1", "Entity": "Calendar" }
                          ],
                          "Select": [
                            {
                              "Measure": { "Expression": { "SourceRef": { "Source": "c" } }, "Property": "Running Total" },
                              "Name": "Confirmed Cases.Count of Event ID running total in Specimen Date"
                            },
                            {
                              "Column": { "Expression": { "SourceRef": { "Source": "c1" } }, "Property": "Date" },
                              "Name": "Calendar.Date"
                            }
                          ],
                          "OrderBy": [
                            {
                              "Direction": 1,
                              "Expression": { "Column": { "Expression": { "SourceRef": { "Source": "c1" } }, "Property": "Date" } }
                            }
                          ]
                        },
                        "Binding": {
                          "Primary": { "Groupings": [ { "Projections": [ 0, 1 ] } ] },
                          "DataReduction": { "DataVolume": 4, "Primary": { "Window": { "Count": 1000 } } },
                          "Version": 1
                        }
                      }
                    }
                  ]
                },
                "CacheKey": "{\"Commands\":[{\"SemanticQueryDataShapeCommand\":{\"Query\":{\"Version\":2,\"From\":[{\"Name\":\"c\",\"Entity\":\"Confirmed Cases\"},{\"Name\":\"c1\",\"Entity\":\"Calendar\"}],\"Select\":[{\"Measure\":{\"Expression\":{\"SourceRef\":{\"Source\":\"c\"}},\"Property\":\"Running Total\"},\"Name\":\"Confirmed Cases.Count of Event ID running total in Specimen Date\"},{\"Column\":{\"Expression\":{\"SourceRef\":{\"Source\":\"c1\"}},\"Property\":\"Date\"},\"Name\":\"Calendar.Date\"}],\"OrderBy\":[{\"Direction\":1,\"Expression\":{\"Column\":{\"Expression\":{\"SourceRef\":{\"Source\":\"c1\"}},\"Property\":\"Date\"}}}]},\"Binding\":{\"Primary\":{\"Groupings\":[{\"Projections\":[0,1]}]},\"DataReduction\":{\"DataVolume\":4,\"Primary\":{\"Window\":{\"Count\":1000}}},\"Version\":1}}}]}",
                "QueryId": "",
                "ApplicationContext": {
                  "DatasetId": "bd7fc819-b88a-41d0-a830-7a8dac4576ff",
                  "Sources": [
                    {
                      "ReportId": "52d29698-2a1e-4f66-b0da-4260ef93d895"
                    }
                  ]
                }
              }
            ],
            "cancelQueries": [],
            "modelId": 318337
        })
    )
    raw = json.loads(rsp.content)
    print(json.dumps(raw))
    result_set = raw['results'][0]['result']['data']['dsr']['DS'][0]['PH'][0]['DM0']
    results = [ i['C'] for i in result_set ]
    print(json.dumps(results))
    return [[datetime.datetime.fromtimestamp(r[0]/1000), r[1]] for r in results if len(r) == 2 ]


if __name__ == "__main__":
    main()


