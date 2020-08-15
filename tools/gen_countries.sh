#!/bin/bash

csvtool format '%(4)\n' COVID-19/csse_covid_19_data/csse_covid_19_daily_reports/08-14-2020.csv | sort -u | while read name ; do
    abbr=$(echo "$name" |  sed -e 's/[^0-9a-zA-Z]\+/_/g' -e 's/^_//g' -e 's/_$//g' | tr 'A-Z' 'a-z')
    echo "<td><a href=/covid/$abbr/new-cases.png><img src=/covid/$abbr/new-cases.png class=smallchart><br><div class=label>$name</div></a></td>"
done

