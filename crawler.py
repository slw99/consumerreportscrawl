from lxml import etree
import csv
import json
import re
import requests

from states import us_state_abbrev

def parse_page(report_card_page_path):
    page = requests.get('http://www.consumerreports.org'+report_card_page_path,verify=False)
    response = page.content

            
    htmlparser = etree.HTMLParser()
    tree = etree.XML(response, htmlparser)
    tds = tree.xpath("//td[@class='heading']")
    for i in range(0,len(tds)) :
        elem = tds[i]
        
        if elem.text.startswith('Overall Aortic Valve Replacement'):
        
            
            #total patients
            total_patients_text = elem.findall('div')[0].text
            total_patients = None
            start_date = None
            end_date = None        
            
            total_patients_text = total_patients_text.replace('\n','')
            if 'This hospital did not have a rating' in total_patients_text:
                return None,None,None,None,None
            
            if total_patients_text:
                
                total_patients = int(re.findall('These ratings are based on (\d+)',
                                                 total_patients_text)[0])
                
               
                start_date,end_date = re.findall('between (\w+ \d+) and (\w+ \d+)',
                                                 total_patients_text)[0]
                
        
           
            mortality_rate_td = tds[i+1]
            complication_rate_td = tds[i+2]
            
            #pull out morality score
            mortality_text = mortality_rate_td.findall('p')[0].text
            mortality_score = None
            if mortality_text:
                mortality_score = int(re.findall('Patients have a (\d+)',
                                                 mortality_text)[0])
            
          
            #pull out complication score
            complication_text = complication_rate_td.findall('p')[0].text
            
            complication_score = None
            if complication_text:
                complication_score = int(re.findall('Patients have a (\d+)',
                                                 complication_text)[0])        
        
          
            
            return total_patients,start_date,end_date,mortality_score,complication_score
    
    
def clean_json(json_text):
    """removes the invalid line in their json"""
    lines = json_text.split('\n')
    response = ''
    for line in lines:
        if '"cities"' not in line:
            response +=  line+'\n'
            
    response = re.sub('\],\W+\}',']}',response)
    return response

def start_crawl(filename):
    
    csvfile = open(filename, 'w')
    result_file = csv.writer(csvfile,lineterminator='\n')
    
    result_file.writerow(['Name','City','State','Total Patients','Mortality %',
                          'Complication %',
                          'Start Date','End Date'])
    for state in us_state_abbrev.values():
        
        state_text = requests.get('http://www.consumerreports.org/health/pay-resources/scripts/hospital-ratings/search/%s.js'%state).content
        state_text = state_text.decode("unicode_escape")
        state_text = clean_json(state_text)

        state_info = json.loads(state_text )
        
        for hospital in state_info['hospitals']:
            
            city = hospital['city']
            stateName = hospital['stateName']
            hospitalName = hospital['hospitalName']
            hospitalReportCardPage = hospital['hospitalReportCardPage']
            total_patients,start_date,end_date,mortality_score,complication_score = parse_page(hospitalReportCardPage)
            
            
            result_file.writerow([hospitalName,city,stateName,
                                 total_patients,mortality_score,complication_score,
                                 start_date,end_date])
            
            #needed to watch file change
            csvfile.flush()

if __name__=="__main__":
    start_crawl("results.csv")
 