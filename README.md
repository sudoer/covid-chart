# covid-chart.py
Started as a graph of Wake County COVID-19 cases.
Quickly grew into a graph of JHU data as well.

# set-up

## data sources

If you want to graph the data from Johns Hopkins University, you'll need to check out their data repo.
By default, the program looks in a folder called "COVID-19", but there is a command-line option to
override that location.

    git clone https://github.com/sudoer/covid-chart.git
    cd covid-chart
    git clone https://github.com/CSSEGISandData/COVID-19.git

## python environment

The requirements are listed in the `requirements.txt` file.  I recommend using a "virtual environment"
(sandbox) to keep all of the dependencies local to this project, without interfering with libraries
installed globally on your system.

    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    # ready to run
    ./covid-chart.py --country=US --state="North Carolina"

# usage

## 3 levels of location data: country, state, county
* `./covid-chart.py --country=US --state='North Carolina' --county=Forsyth`
* `./covid-chart.py --country=US --state='North Carolina' --county=Wake`
* `./covid-chart.py --country=US --state='North Carolina'`
* `./covid-chart.py --country=US`
* `./covid-chart.py --country=Japan`
* `./covid-chart.py --country=Japan --state=Hokkaido`

## 4 graph options: new-vs-cumulative, cases-vs-deaths:
* `./covid-chart.py --country=US --state='North Carolina' --county=Wake`
* `./covid-chart.py --country=US --state='North Carolina' --county=Wake --new`
* `./covid-chart.py --country=US --state='North Carolina' --county=Wake --deaths`
* `./covid-chart.py --country=US --state='North Carolina' --county=Wake --new --deaths`

## graphing JHU data
* Johns Hopkins University is the default source.
* source can be specified or omitted
* `./covid-chart.py --source=jhu --country=US --state='North Carolina' --county=Wake`

## getting source data from Wake County DHHS
* Wake source MUST be specified (because the default source is JHU)
* `./covid-chart.py --source=wake`
* Using `--source=wake` implies `--country=US` and `--state='North Carolina'` and `--county=Wake`

## graph options
* logarithmic chart: `./covid-chart.py --source=wake --log`
* custom moving average: `./covid-chart.py --source=wake --avg=10`
* size: `./covid-chart.py --source=wake --dpi=120 --inches=10x8`
* output to a file: `./covid-chart.py --source=wake --dpi=120 --inches=10x8 --out=wake.png`

## bulk
* The `--recursive` option expands a country to include all states, or a state to include all counties.
* Used with filters, you can specify any combination that you want.
* `./covid-chart.py --new --country=US --state=North\ Carolina --bulk --recursive --out=nc-charts` will produce 510 files:
    + (4 graphs and a summary) for each of 100 counties
    + (4 graphs and a summary) for "NC unassigned" (included in the JHU data like a county)
    + (4 graphs and a summary) for the entire state
* `./covid-chart.py --new --country=US --state=North\ Carolina --county-Wake --bulk --out=nc-charts` will produce 5 files:
    + (4 graphs and a summary) for Wake county
* `./covid-chart.py --new --country=US --bulk --out=us-charts` will produce 5 files:
    + (4 graphs and a summary) for the entire US

## reading multiple filters from a file
* To graph several combinations of filters in one bulk operation, put your filters in a file.
* Format is the same as the output of `./covid-chart.py --locations`
* For example, make a file called "locations" containing:

    Norway|*|*
    United Kingdom|England|*
    United Kingdom|Scotland|*
    US|*|*
    Japan|*|*

* Then run `./covid-chart.py --new --filters=locations --bulk --out=5countries` to get charts for the 5 countries.
* Or run `./covid-chart.py --new --filters=locations --bulk --out=5countries --recursive` to get charts for all states and counties within those.


