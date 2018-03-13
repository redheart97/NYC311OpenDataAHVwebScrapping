from django.shortcuts           import render, redirect
from django.views.generic.base  import TemplateView
from django.http                import HttpResponse, HttpResponseRedirect,HttpRequest


from urllib.request     import urlopen
from datetime           import datetime, timedelta
from dateutil           import parser
from collections        import OrderedDict

import json
import csv
import re
import pandas as pd

from AHVscrappingUtil.settings import BASE_DIR

# Create your views here.

class HomePageView(TemplateView):
    template_name   = "home.html"

class TablePageView(TemplateView):
    template_name   = "result.html"

def callScript(request):
    if request.method == 'POST':
        startDate       = str(request.POST.get('startDate', ''))
        endDate         = str(request.POST.get('endDate', ''))
        searchRadius    = str(request.POST.get('searchRadius', ''))
        communityBoard  = str(request.POST.get('communityBoard', ''))
        #print(startDate + " " + endDate + " " + searchRadius + " " + communityBoard)    
    
        #Keys to order data on (the wanted keys from 311 data)
        wantedKeys = [  'unique_key', 'created_date', 'incident_zip', 
                        'incident_address', 'community_board', 'latitude', 'longitude'  ]

        #API key and base url with custom filters agency = DEP and complaint_type = Noise
        apiKey   = "$$app_token=D66z9bcjNltBbJ52YldqPlzGc"
        baseUrl  = "https://data.cityofnewyork.us/resource/fhrw-4uyv.json?"
        baseUrl += apiKey+"&$order=unique_key&agency=DEP&complaint_type=Noise"

        startDate = str(parser.parse(startDate)).replace(" ","T")
        endDate = str(parser.parse(endDate)).replace(" ","T")

        #Construct query on created date
        createdDateQuery = "&$where=created_date between '" + startDate + "' and '" + endDate + "'"
        createdDateQuery = createdDateQuery.replace(" ","%20")
        createdDateQuery = createdDateQuery.replace("'","%27")

        #Construct query on descriptor 'NM1' and format it for query
        descriptorQuery = " AND (descriptor like '%NM1%')" 
        descriptorQuery = descriptorQuery.replace("%","%25")
        descriptorQuery = descriptorQuery.replace(" ","%20")
        descriptorQuery = descriptorQuery.replace("'","%27")

        #Construct query on community board = CB02  or 02 manhattan
        communityBoardQuery = "&community_board=" + communityBoard.upper()
        communityBoardQuery = communityBoardQuery.replace(" ","%20")

        #Update Url and Pull down 311data from website. default 1000 results will be produced
        resultLimit = "1000"
        baseUrl += "&$limit=" + resultLimit
        baseUrl += createdDateQuery + descriptorQuery + communityBoardQuery
        jsonObj = urlopen(baseUrl)
        data = json.load(jsonObj)

        #data (queried 311data) is list of dictionaries. Need to remove some keys and format others (Only wanted keys remain after)
        for entry in data:
            keysToBeRemoved = [someKeys for someKeys in entry if someKeys not in wantedKeys]
            for key in keysToBeRemoved: del entry[key]
            newKeys = entry.keys()
            
            for key in wantedKeys:
                if key not in newKeys:
                    entry[key] = 'NULL'
            
            dateKeys = ['created_date']
            for key in dateKeys: 
                entry.get(key) and entry.update({key: entry[key].replace("T"," ")})
                entry.get(key) and entry.update({key: entry[key].replace(":00.000","")})
            
            latlonKeys = ['latitude', 'longitude']
            for key in latlonKeys: 
                if entry[key] != 'NULL':
                    entry.get(key) and entry.update({key: str('%.4f'%(float(entry[key])))})

        
        df = pd.DataFrame(data,columns = data[0].keys())
        #with pd.option_context('display.max_rows', None, 'display.max_columns', None): print(df.to_string())
        path = BASE_DIR + r"\templates\result.html"
        df.to_html(path)
        
        
        return HttpResponse('.')