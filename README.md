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

## graphing Wake County data

* cumulative cases: `./covid-chart.py --source=wake`
* new cases: `./covid-chart.py --source=wake --new`
* logarithmic chart: `./covid-chart.py --source=wake --log`
* custom moving average: `./covid-chart.py --source=wake --avg=10`

## graphing JHU data

* a state: `./covid-chart.py --source=jhu --country=US --state='North Carolina'`
* a county: `./covid-chart.py --source=jhu --country=US --state='North Carolina' --county=Wake`
* JHU is default source: `./covid-chart.py --country=US --state='North Carolina' --county=Wake`

## combine all of the arguments

    $ ./covid-chart.py --help
    usage: covid-chart.py [-h] [--source SOURCE] [--jhu-data-dir JHU-DATA-DIR]
                          [--new] [--deaths] [--country COUNTRY] [--state STATE]
                          [--county COUNTY] [--start-date START-DATE]
                          [--end-date END-DATE] [--avg AVG] [--log] [--summary]
                          [--locations] [--bulk] [--out OUT] [--inches INCHES]
                          [--dpi DPI]
    
    COVID-19 grapher
    
    optional arguments:
      -h, --help            show this help message and exit
      --source SOURCE       jhu or wake
      --jhu-data-dir JHU-DATA-DIR
                            name of JHU git directory
      --new                 new cases
      --deaths              graph deaths rather than cases
      --country COUNTRY     country (JHU data only)
      --state STATE         US state (JHU data only)
      --county COUNTY       US county (JHU data only)
      --start-date START-DATE
                            start-date (YYYY-MM-DD)
      --end-date END-DATE   start-date (YYYY-MM-DD)
      --avg AVG             size of sliding average
      --log                 logarithmic scale
      --summary             print summary of latest information to stdout
      --locations           print list of valid combinations of country, state,
                            county
      --bulk                output option: save all data as PNGs using default
                            filenames
      --out OUT             output option: save one graph to file with this
                            filename
      --inches INCHES       size in inches (WWxHH)
      --dpi DPI             dots per inch

