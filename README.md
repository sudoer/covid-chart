# covid-chart.py
Started as a graph of Wake County COVID-19 cases.
Quickly grew into a graph of JHU data as well.

# usage

## graphing Wake County data

* new cases: `./covid-chart.py --source=wake --new`
* cumulative cases: `./covid-chart.py --source=wake --new`
* logarithmic chart: `./covid-chart.py --source=wake --log`
* custom moving average: `./covid-chart.py --source=wake --avg=10`

## graphing JHU data

* a state: `./covid-chart.py --source=jhu --state='North Carolina'`
* a county: `./covid-chart.py --source=jhu --state='North Carolina' --county=Wake`
* JHU is default source: `./covid-chart.py --state='North Carolina' --county=Wake`

## combine all of the arguments

    $ ./covid-chart.py --help
    usage: covid-chart.py [-h] [--avg AVG] [--log] [--new] [--source SOURCE]
                          [--jhu-data-dir JHU-DATA-DIR] [--county COUNTY]
                          [--state STATE] [--country COUNTRY]

    Wake County COVID-19 grapher

    optional arguments:
      -h, --help            show this help message and exit
      --avg AVG             size of sliding average
      --log                 logarithmic scale
      --new                 new cases
      --source SOURCE       jhu or wake
      --jhu-data-dir JHU-DATA-DIR
                            name of JHU git directory
      --county COUNTY       US county (JHU data only)
      --state STATE         US state (JHU data only)
      --country COUNTRY     country (JHU data only)

