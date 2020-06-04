from collections import defaultdict

from math import log

import matplotlib.pyplot as plt
import numpy as np

import datetime
import matplotlib.dates as mplDates

if 0:
    countyFile = "/home/jim/code/covid19/covid-19-data/us-counties.csv"
    stateFile = "/home/jim/code/covid19/covid-19-data/us-states.csv"
    countryFile = "/home/jim/code/covid19/covid-19/data/countries-aggregated.csv"
else:
    countyFile = "/home/jim/mnt/dort/code/covid19/covid-19-data/us-counties.csv"
    stateFile = "/home/jim/mnt/dort/code/covid19/covid-19-data/us-states.csv"
    countryFile = "/home/jim/mnt/dort/code/covid19/covid-19/data/countries-aggregated.csv"

import csv

def parseDate(s):
    days = (31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31) # this is for a leap year!
    sDays = (0, 0, 31, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335)
    
    try:
        y,m,d = (int(v) for v in s.split('-'))

        return sDays[m] + d
    except:
        print("something went wrong in parseDate()")

def convertDay(doy):
    days = (31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31) # this is for a leap year!
    sDays = (0, 0, 31, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335)

    year = 2020
    for m,d in enumerate(days):
        doy -= d

        if doy < 1:
            doy += d
            return mplDates.date2num(datetime.datetime(year, m+1, doy))
        
def convertDays(dayList):
    return [convertDay(d) for d in dayList]
            
            
    

fipsDict = defaultdict(lambda : ([], [], []))
countyDict = defaultdict(lambda : ([], [], []))
stateDict = defaultdict(lambda : ([], [], []))
countryDict = defaultdict(lambda : ([], [], []))

def addEntry(d, k, day, cases, deaths):
    cases = int(cases)
    if cases < 1:
        return
    entry = d[k]
    entry[0].append(int(day))
    entry[1].append(cases)
    entry[2].append(int(deaths))

def readUSCounties():
    with open(countyFile) as f:
        header = f.readline()
        csvReader = csv.reader(f)
        
        for row in csvReader:
            date, county, state, fips, cases, deaths = row        
            days = parseDate(date)
            
            try:
                addEntry(fipsDict, int(fips), days, cases, deaths)
            except:
                pass
            addEntry(countyDict, (state, county), days, cases, deaths)

                
def readStates():
    with open(stateFile) as f:
        header = f.readline()
        csvReader = csv.reader(f)
        
        for row in csvReader:
            date, state, fips, cases, deaths = row
            days = parseDate(date)

            addEntry(fipsDict, int(fips), days, cases, deaths)
            addEntry(stateDict, state, days, cases, deaths)
            
            #print (date, days, state, fips, cases, deaths)

def readCountries():
    with open(countryFile) as f:
        header = f.readline()
        csvReader = csv.reader(f)
        
        for row in csvReader:
            date, country, cases, recovered, deaths = row
            days = parseDate(date)
            
            addEntry(countryDict, country, days, cases, deaths)
#            print (date, days, country, cases, recovered, deaths)

def diffSeq(s):
#    print(s)
    last = 0
    ret = []
    for v in s:
        #print (v)
        ret.append(v - last)
        last = v

    return ret

def rolling(s, n):
    ret = np.zeros(len(s) + n-1)
    ar = np.array(s)
    for i in range(n):
        ret[i:i+len(s)] += ar
    ret /= n
    return ret[:len(s)]
    

def readEverything():
    readUSCounties()
    readStates()
    readCountries()


def fixPADeaths(da):
    """
    on entry 46 (0 based), PA added an additional 254 deaths, most of which should
    have been counted earlier.  So let's shift them a bit
    """
    ret = []

    totAdded = 0
    for i,v in enumerate(da):
        
        if i > 25 and i < 46:
            totAdded += 10
            v += totAdded
        ret.append(v)

    print (totAdded)
    return ret

class CovidEntity:
    def __init__(self, name, data):
        self.name = name
        self.days = data[0]
        self.cases = data[1]
        self.deaths = data[2]

def normalize(days, cases, deaths, dayMin, dayMax):
    dayCount = dayMax - dayMin + 1
    retDays = np.arange(dayMin,dayMax+1, dtype="i4")
    retCases = np.zeros(dayCount, dtype="i4")
    retDeaths = np.zeros(dayCount, dtype="i4")

    for d,c,t in zip(days, cases, deaths):
        if d >= dayMin and d <= dayMax:
            retCases[d - dayMin] = c
            retDeaths[d - dayMin] = t

    return (retDays, retCases, retDeaths)

def subtractEntities(e1, e2):
    #print (e1)
    dayMin = min(min(e1[0]), min(e2[0]))
    dayMax = min(max(e1[0]), max(e2[0]))  # yes the min on this is correct
    
    e1 = normalize(e1[0], e1[1], e1[2], dayMin, dayMax)
    e2 = normalize(e2[0], e2[1], e2[2], dayMin, dayMax)

    retCases = e1[1] - e2[1]
    retDeaths = e1[2] - e2[2]
    return (e1[0], retCases, retDeaths)

def sumEntities(e1, e2):
    dayMin = min(min(e1[0]), min(e2[0]))
    dayMax = min(max(e1[0]), max(e2[0]))  # yes the min on this is correct
    
    e1 = normalize(e1[0], e1[1], e1[2], dayMin, dayMax)
    e2 = normalize(e2[0], e2[1], e2[2], dayMin, dayMax)

    retCases = e1[1] + e2[1]
    retDeaths = e1[2] + e2[2]
    return (e1[0], retCases, retDeaths)

def multEntity(ent, m):
    cases = np.array(ent[1], dtype='f4')
    deaths = np.array(ent[2], dtype='f4')
    cases *= m
    deaths *= m
    return (ent[0], cases, deaths)

def sumMany(newName, *args):
    ret = None
    for arg in args:
        if ret is None:
            ret = arg[0]
            continue
        ret = sumEntities(ret, arg[0])
    return (ret, newName)

def subMany(newName, base, *args):
    ret = base[0]
    for arg in args:
        ret = subtractEntities(ret, arg[0])
    return (ret, newName)

def stateRegion(newName, state, *args):
    totPop = 0
    counties = []
    for arg in args:
        counties.append(getCounty(state, arg))
        if state == "Pennsylvania":
            totPop += PACountyPop[arg]

    mult = 100000. / totPop
    nn100k = "%s per 100k"%newName

    ret = sumMany(newName, *counties)
    if state != "Pennsylvania":
        return ret
    ret2 = (multEntity(ret[0], mult), nn100k)
    return ret, ret2


def getCountry(c):
    if c not in countryDict:
        raise RuntimeError("invalid country %s"%c)
    return (countryDict[c], c)
def getState(s):
    if s not in stateDict:
        raise RuntimeError("invalid country %s"%s)
    return (stateDict[s], s)
def getCounty(s, c):
    if (s,c) not in countyDict:
        raise RuntimeError("invalid county %s, %s"%(s,c))
    return (countyDict[(s,c)], "%s County %s"%(c, s))

def addPlot(s1, ax, attr, color, showPoints=True, showRolling=True):
    days = convertDays(s1[0][0])
    
    if showPoints:
        ax.plot(days, diffSeq(s1[0][attr]), '%s.'%color, label='%s'%(s1[1],))
    if showRolling:
        ax.plot(days, rolling(diffSeq(s1[0][attr]), 7), '%s-'%color, label="%s (7 day average)"%(s1[1],))
    

def maxCases(ent):
    return np.amax(ent[0][1])

def percentOfMax(ent):
    name = "%s percent of max"%ent[1]

    maxCases = np.amax(diffSeq(ent[0][1]))
    maxDeaths = np.amax(diffSeq(ent[0][2]))

    #print (maxCases)
    
    cases = np.array(ent[0][1], dtype='f4') * (1.0 / maxCases)
    #print (ent[0][0])
    #print (ent[0][1])
    #print (cases)
    deaths = np.array(ent[0][2], dtype='f4') * (1.0 / maxDeaths)
    return ((ent[0][0], cases, deaths), name)


PACountyPop = {'Philadelphia': 1584138,
                   'Allegheny': 1218452,
                   'Montgomery': 828604,
                   'Bucks': 628195,
                   'Delaware': 564751,
                   'Lancaster': 543557,
                   'Chester': 522046,
                   'York': 448273,
                   'Berks': 420152,
                   'Lehigh': 368100,
                   'Westmoreland': 350611,
                   'Luzerne': 317646,
                   'Northampton': 304807,
                   'Dauphin': 277097,
                   'Erie': 272061,
                   'Cumberland': 251423,
                   'Lackawanna': 210793,
                   'Washington': 207346,
                   'Butler': 187888,
                   'Monroe': 169507,
                   'Beaver': 164742,
                   'Centre': 162805,
                   'Franklin': 154835,
                   'Schuylkill': 142067,
                   'Lebanon': 141314,
                   'Cambria': 131730,
                   'Fayette': 130441,
                   'Blair': 122492,
                   'Lycoming': 113664,
                   'Mercer': 110683,
                   'Adams': 102811,
                   'Northumberland': 91083,
                   'Lawrence': 86184,
                   'Crawford': 85063,
                   'Indiana': 84501,
                   'Clearfield': 79388,
                   'Somerset': 73952,
                   'Columbia': 65456,
                   'Armstrong': 65263,
                   'Carbon': 64227,
                   'Bradford': 60833,
                   'Pike': 55933,
                   'Wayne': 51276,
                   'Venango': 51266,
                   'Bedford': 48176,
                   'Mifflin': 46222,
                   'Perry': 46139,
                   'Huntingdon': 45168,
                   'Union': 44785,
                   'Jefferson': 43641,
                   'McKean': 40968,
                   'Tioga': 40763,
                   'Susquehanna': 40589,
                   'Snyder': 40540,
                   'Warren': 39498,
                   'Clarion': 38779,
                   'Clinton': 38684,
                   'Greene': 36506,
                   'Elk': 30169,
                   'Wyoming': 27046,
                   'Juniata': 24704,
                   'Montour': 18240,
                   'Potter': 16622,
                   'Fulton': 14523,
                   'Forest': 7279,
                   'Sullivan': 6071,
                   'Cameron': 4492,
}
def main():
    readEverything()
    usa = getCountry('US')
    sw = getCountry('Sweden')
    md = getState('Maryland')
    pa = getState('Pennsylvania')
    paf = ((pa[0][0], pa[0][1], fixPADeaths(pa[0][2])), "Pennsylvania Adjusted")
    ma = getState('Massachusetts')
    ny = getState('New York')
    de = getState('Delaware')
    nj = getState('New Jersey')
    fl = getState('Florida')
    oh = getState('Ohio')
    tx = getState('Texas')
    mi = getState('Michigan')
    ca = getState('California')
    nyc = getCounty('New York', 'New York City')

    usaSubNyNj = subMany("US without NY, NJ", usa, ny, nj)
    usaSubNy = subMany("US without NY", usa, ny)
    #usaSubNy = (subtractEntities(usa[0], ny[0]), 'US without NY')
    #usaSubNyNj = (subtractEntities(usaSubNy[0], nj[0]), 'US without NY, NJ')

    
    allegheny = getCounty('Pennsylvania', 'Allegheny')
    westmoreland = getCounty('Pennsylvania', 'Westmoreland')
    washPA = getCounty('Pennsylvania', 'Washington')
    beaver = getCounty('Pennsylvania', 'Beaver')
    butler = getCounty('Pennsylvania', 'Butler')
    fayette = getCounty('Pennsylvania', 'Fayette')
    armstrong = getCounty('Pennsylvania', 'Armstrong')
    indiPA = getCounty('Pennsylvania', 'Indiana')
    york = getCounty('Pennsylvania', 'York')
    phil = getCounty('Pennsylvania', 'Philadelphia')
    berks = getCounty('Pennsylvania', 'Berks')

    balt = getCounty('Maryland', 'Baltimore city')
    baltMsaMD = sumMany("Baltimore MSA in MD",
                        getCounty('Maryland', "Baltimore city"),
                        getCounty('Maryland', "Baltimore"),
                        getCounty('Maryland', "Anne Arundel"),
                        getCounty('Maryland', "Howard"),
                        getCounty('Maryland', "Harford"),
                        getCounty('Maryland', "Carroll"),
                        getCounty('Maryland', "Queen Anne's"))

    washMsaMD = sumMany("Washington DC MSA in MD",
                        getCounty('Maryland', "Prince George's"),
                        getCounty('Maryland', "Charles"),
                        getCounty('Maryland', "Calvert"),
                        getCounty('Maryland', "Montgomery"),
                        getCounty('Maryland', "Frederick"))

##                        getCounty('Maryland', ""),
#                        getCounty('Maryland', ""),
    
    kcm = getCounty('Missouri', 'Jackson')
    msx = getCounty('Massachusetts', 'Middlesex')
    suf = getCounty('Massachusetts', 'Suffolk')
    nor = getCounty('Massachusetts', 'Norfolk')
    dc = getState('District of Columbia')
    ga = getState('Georgia')
    wv = getState('West Virginia')
    ky = getState('Kentucky')
    aus = getCountry('Australia')
    brazil = getCountry('Brazil')
    delCty = getCounty('Pennsylvania', 'Delaware')
    bucks = getCounty('Pennsylvania', 'Bucks')
    chester = getCounty('Pennsylvania', 'Chester')
    montgomery = getCounty('Pennsylvania', 'Montgomery')
    schuylkill = getCounty('Pennsylvania', 'Schuylkill')
    lancaster = getCounty('Pennsylvania', 'Lancaster')


    pghMSA = sumMany("Pittsburgh MSA", allegheny, armstrong, beaver, butler, fayette, washPA, westmoreland)
    philMSA = sumMany("Philadelphia MSA",
                      phil,
                      delCty,
                      bucks,
                      chester,
                      montgomery,
                      berks)

    #    sePA = sumMany("SouthEast PA", phil, delCty, bucks, chester, montgomery, berks, schuylkill, lancaster)
    #    swPA = stateRegion("SouthWest PA", "Pennsylvania", "Allegheny", "Armstrong", "Beaver", "Bedford",
    #                       "Blair", 'Butler', 'Cambria', 'Fayette', 'Fulton', 'Greene', 'Indiana',
    #                       'Somerset', 'Washington', 'Westmoreland')
    
    

    ncPA, ncPA100 = stateRegion("North Central PA", "Pennsylvania",
                                'Bradford',
                                'Centre',
                                'Clinton',
                                'Columbia',
                                'Lycoming',
                                'Montour',
                                'Northumberland',
                                'Potter',
                                'Snyder',
                                'Sullivan',
                                'Tioga',
                                'Union')
    ncPAPerMax = percentOfMax(ncPA)
    nePA, nePA100 = stateRegion("NorthEast PA", "Pennsylvania",
                                'Carbon',
                                'Lackawanna',
                                'Lehigh',
                                'Luzerne',
                                'Monroe',
                                'Northampton',
                                'Pike',
                                'Susquehanna',
                                'Wayne',
                                'Wyoming')
    nePAPerMax = percentOfMax(nePA)
    nwPA, nwPA100 = stateRegion("NorthWest PA", "Pennsylvania",
                                'Cameron',
                                'Clarion',
                                'Clearfield',
                                'Crawford',
                                'Elk',
                                'Erie',
                                'Forest',
                                'Jefferson',
                                'Lawrence',
                                'McKean',
                                'Mercer',
                                'Venango',
                                'Warren')
    nwPAPerMax = percentOfMax(nwPA)
    scPA, scPA100 = stateRegion("South Central PA", "Pennsylvania",
                                'Adams',
                                'Bedford',
                                'Blair',
                                'Cumberland',
                                'Dauphin',
                                'Franklin',
                                'Fulton',
                                'Huntingdon',
                                'Juniata',
                                'Lebanon',
                                'Mifflin',
                                'Perry',
                                'York')
    scPAPerMax = percentOfMax(scPA)
    sePA, sePA100 = stateRegion("SouthEast PA", "Pennsylvania",
                                'Berks',
                                'Bucks',
                                'Chester',
                                'Delaware',
                                'Lancaster',
                                'Montgomery',
                                'Philadelphia',
                                'Schuylkill')
    sePAPerMax = percentOfMax(sePA)
    swPA, swPA100 = stateRegion("SouthWest PA", "Pennsylvania",
                                'Allegheny',
                                'Armstrong',
                                'Beaver',
                                'Butler',
                                'Cambria',
                                'Fayette',
                                'Greene',
                                'Indiana',
                                'Somerset',
                                'Washington',
                                'Westmoreland')
    swPAPerMax = percentOfMax(swPA)
    allegheny, allegheny100 = stateRegion("Allegheny County", "Pennsylvania", "Allegheny")
    
    
    
    paNoSE = subMany("PA except SouthEast", pa, sePA)
    
    paNoPhilPgh = subMany("Pennsylvania without Philadelphia and Pittsburgh MSA", pa, philMSA, pghMSA)

    
    s1 = s2 = s3 = s4 = s5 = s6 = None

    if 0:
        #s1 = ny
        s4 = fl
    if 0:
        s1 = getCountry('Japan')
    
    if 0:
        s1 = getState('Texas')
        s2 = getState('North Carolina')
        s3 = getState('California')
        s5 = getState('West Virginia')
        s6 = getState('Wisconsin')
    if 0:
        s1 = getCounty('Georgia', 'Cobb')
        s2 = getCounty('Georgia', 'DeKalb')
        s3 = getCounty('Georgia', 'Fulton')
        s5 = getCounty('Georgia', 'Gwinnett')
        s6 = getCounty('Georgia', 'Hall')

    if 1:
        s1 = subMany("FL without Miami-Dade", fl, getCounty('Florida', 'Miami-Dade'))
        s2 = getCounty('Florida', 'Miami-Dade')
    if 0:
        s1 = getCounty('Florida', 'Miami-Dade')
        s2 = getCounty('Florida', 'Broward')
        s3 = getCounty('Florida', 'Palm Beach')
        s4 = getCounty('Florida', 'Hillsborough')
        s5 = getCounty('Florida', 'Orange')
        s6 = getCounty('Florida', 'Pinellas')

    if 0:
        s1 = nwPA
        s2 = ncPA
        s3 = nePA
        s4 = swPA
        s5 = scPA
        s6 = sePA
    if 0:
        s1 = nwPAPerMax
        s2 = ncPAPerMax
        s3 = nePAPerMax
        s4 = swPAPerMax
        s5 = scPAPerMax
        s6 = sePAPerMax

    if 0:
        s4 = scPA100
    if 0:
        s1 = nwPA100
        s2 = ncPA100
        s3 = nePA100
        s4 = swPA100
        s5 = scPA100
        s6 = sePA100
    if 0:
        s4 = allegheny100
        s1 = swPA100
    if 0:
        s1 = baltMsaMD
        s2 = washMsaMD
    if 0:
        s1 = pa
        s2 = sw
        #s2 = sePA
        #s3 = paNoSE
        #s6 = ga
    if 0:
        s1 = usa
        s2 = ny
        #s3 = nj
        #s5 = usaSubNyNj
        s6 = usaSubNy
        #s4 = usa
    if 0:
        s1 = fl
        s2 = getState("Alabama")
        #s3 = getState("Mississippi")
        s4 = getState("Wisconsin")
        s5 = getState("Louisiana")
        s6 = tx
    if 0:
        s1 = allegheny
        #s2 = pghMSA
        #s3 = swPA
    if 0:
        s1 = pa
        s2 = ma
        #s2 = ky
        #s3 = oh
        #s2 = dc
        #s3 = ga
        #s2 = fl
        #s6 = md
    if 0:
        s1 = aus
        s2 = brazil
        s3 = usa
    
    attr = 1
    showPoints = True
    showRolling = True

    if attr == 1:
        attrName = 'confirmed new cases'
    elif attr == 2:
        attrName = 'deaths'

    fig, ax = plt.subplots()

    if s1 is not None:
        addPlot(s1, ax, attr, 'r', showPoints=showPoints, showRolling=showRolling)
    if s2 is not None:
        addPlot(s2, ax, attr, 'b', showPoints=showPoints, showRolling=showRolling)
    if s3 is not None:
        addPlot(s3, ax, attr, 'g', showPoints=showPoints, showRolling=showRolling)
    if s4 is not None:
        addPlot(s4, ax, attr, 'k', showPoints=showPoints, showRolling=showRolling)
    if s5 is not None:
        addPlot(s5, ax, attr, 'c', showPoints=showPoints, showRolling=showRolling)
    if s6 is not None:
        addPlot(s6, ax, attr, 'm', showPoints=showPoints, showRolling=showRolling)

    #    plt.yscale('log')

    legend = ax.legend(loc='upper left', shadow=True)
    ax.set_xlabel('date')
    ax.set_ylabel(attrName)

    locator = mplDates.AutoDateLocator(minticks=10, maxticks=20)
    formatter = mplDates.ConciseDateFormatter(locator)
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(formatter)
    
    plt.show()


main()
