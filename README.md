# covid_graph
The tool that I use for graphing covid cases.  

It has been made somewhat specific to my personal usage (ie there's lots more work with Pennsylvania counties)

This is set up for my personal workspace currently without any niceties.  Maybe I should clean it up so that others could use it easier but I haven't done that yet.

This parses the data from NYTimes covid github repository for state and county data available at 
git@github.com:nytimes/covid-19-data

And for country data it uses the github repository at:
git@github.com:datasets/covid-19.git

After the includes at the top of the file are several pointers to files within these repos.

Further down is where you specify what you wish to graph just sitting loose in main()
