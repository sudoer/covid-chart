#!/usr/bin/env python3

import argparse
import datetime
import json
import requests
import matplotlib.pyplot as plt
import pandas as pd
import tkinter as tk  # sudo apt-get install python3-tk


def main():

    parser = argparse.ArgumentParser(description='Wake County COVID-19 grapher')
    parser.add_argument('-a','--avg', type=int, default=7, help='size of sliding average', required=False)
    args = vars(parser.parse_args())
    print(json.dumps(args))

    raw = pull_raw_json()
    print(json.dumps(raw))
    result_set = raw['results'][0]['result']['data']['dsr']['DS'][0]['PH'][0]['DM0']
    results = [ i['C'] for i in result_set ]
    print(json.dumps(results))

    pairs = [ r for r in results if len(r) == 2 ]
    series = list(zip(*pairs))

    df = pd.DataFrame(data={
        'dates': [datetime.datetime.fromtimestamp(ms/1000) for ms in series[0]],
        'cases': series[1],
    })


    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    ax.set_yscale('log')

    ## # Major ticks every 20, minor ticks every 5
    ## major_ticks = np.arange(0, 101, 20)
    ## minor_ticks = np.arange(0, 101, 5)

    ## ax.set_xticks(major_ticks)
    ## ax.set_xticks(minor_ticks, minor=True)
    ## ax.set_yticks(major_ticks)
    ## ax.set_yticks(minor_ticks, minor=True)

    # And a corresponding grid
    ax.grid(which='both')

    # Or if you want different settings for the grids:
    ax.grid(which='minor', alpha=0.2)
    ax.grid(which='major', alpha=0.5)



    plt.plot_date(df.dates, df.cases,
        xdate=True, ydate=False,
        marker='.',
        color='blue')
    plt.plot_date(df.dates, df.cases.rolling(window=args['avg']).mean(),
        xdate=True, ydate=False,
        label='average',
        marker=None,
        linestyle='solid', linewidth=2,
        color='orange')

    plt.show()





def pull_raw_json():

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
    return json.loads(rsp.content)



# jq -c .results[0].result.data.dsr.DS[0].PH[0].DM0[].C < out1 > out2
#
# yestcases=0
# grep ',' out2 | sed -e 's/^\[//g' -e 's/\]$//g' | while read ln ; do
#     dateint=${ln%,*}
#     cases=${ln#*,}
#     # echo "dateint=[$dateint] cases=[$cases]"
#     date=$(date -d "@$(($dateint/1000))" "+%Y-%m-%d")
#     echo "$date,$cases,$(($cases-$yestcases))"
#     yestcases=$cases
# done > out3.csv


if __name__ == "__main__":
    main()


