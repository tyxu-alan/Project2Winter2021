#########################################
##### Name:     TianyuanXu          #####
##### Uniqname:    tyxu             #####
#########################################

from bs4 import BeautifulSoup
import requests
import json
from Project2Winter2021 import secrets

CACHE_FILENAME = "nps_cache.json"

def open_cache():
    ''' opens the cache file if it exists and loads the JSON into
    the CACHE_DICT dictionary.
    if the cache file doesn't exist, creates a new cache dictionary
    Parameters
    ----------
    None
    Returns
    -------
    The opened cache
    '''
    try:
        cache_file = open(CACHE_FILENAME, 'r')
        cache_contents = cache_file.read()
        cache_dict = json.loads(cache_contents)
        cache_file.close()
    except:
        cache_dict = {}
    return cache_dict

def save_cache(cache_dict):
    ''' saves the current state of the cache to disk
    Parameters
    ----------
    cache_dict: dict
        The dictionary to save
    Returns
    -------
    None
    '''
    dumped_json_cache = json.dumps(cache_dict)
    fw = open(CACHE_FILENAME,"w")
    fw.write(dumped_json_cache)
    fw.close()

def construct_unique_key(baseurl, params):
    ''' constructs a key that is guaranteed to uniquely and
    repeatably identify an API request by its baseurl and params
    Parameters
    ----------
    baseurl: string
        The URL for the API endpoint
    params: dictionary
        A dictionary of param: param_value pairs
    Returns
    -------
    string
        the unique key as a string
    '''
    param_strings = []
    connector = "_"
    for k in params.keys():
        param_strings.append(f'{k}_{params[k]}')
    param_strings.sort()
    unique_key = baseurl + connector + connector.join(param_strings)
    return unique_key

def make_request(baseurl, params):
    '''Make a request to the Web API using the baseurl and params
    Parameters
    ----------
    baseurl: string
        The URL for the API endpoint
    params: dictionary
        A dictionary of param: param_value pairs
    Returns
    -------
    string
        the results of the query as a Python object loaded from JSON
    '''
    response = requests.get(baseurl, params=params)
    return response.json()

def make_request_with_cache(baseurl, params={}, API=False):
    '''Check the cache for a saved result for this baseurl+params
    combo. If the result is found, return it. Otherwise send a new
    request, save it, then return it.
    Parameters
    ----------
    baseurl: string
        The URL for the API endpoint
    params: dictionary
        A dictionary of param: param_value pairs
    Returns
    -------

    string
        the results of the query as a Python object loaded from JSON or html
    '''
    request_key = construct_unique_key(baseurl, params)
    CACHE_DICT = open_cache()
    if request_key in CACHE_DICT.keys():
        print("Using cache")
        if not API:
            return CACHE_DICT[request_key]["html"]
        else:
            return CACHE_DICT[request_key]
    else:
        print("Fetching")
        if not API:
            CACHE_DICT[request_key] = {"html":requests.get(baseurl).text}
            save_cache(CACHE_DICT)
            return CACHE_DICT[request_key]["html"]
        else:
            CACHE_DICT[request_key] = make_request(baseurl, params)
            save_cache(CACHE_DICT)
            return CACHE_DICT[request_key]

class NationalSite:
    '''a national site

    Instance Attributes
    -------------------
    category: string
        the category of a national site (e.g. 'National Park', '')
        some sites have blank category.
    
    name: string
        the name of a national site (e.g. 'Isle Royale')

    address: string
        the city and state of a national site (e.g. 'Houghton, MI')

    zipcode: string
        the zip-code of a national site (e.g. '49931', '82190-0168')

    phone: string
        the phone of a national site (e.g. '(616) 319-7906', '307-344-7381')
    '''

    def __init__(self, category="No category", name="No name",
                 address="No address", zipcode="No zipcode",
                 phone="No phone"):
        # user input data
        self.category = category
        self.name = name
        self.address = address
        self.zipcode = str(zipcode)
        self.phone = str(phone)

    def info(self):
        '''return the media name, author, release year

        Parameters
        ----------
        none

        Returns
        -------
        information : string
            media name, author, release year
        '''
        return self.name + " (" + self.category + ")" + ": " +\
               self.address + " " + self.zipcode


def build_state_url_dict():
    ''' Make a dictionary that maps state name to state page url from "https://www.nps.gov"

    Parameters
    ----------
    None

    Returns
    -------
    dict
        key is a state name and value is the url
        e.g. {'michigan':'https://www.nps.gov/state/mi/index.htm', ...}
    '''
    url_dict = {}
    homepage = "https://www.nps.gov"
    homedata = make_request_with_cache(homepage)
    homesoup = BeautifulSoup(homedata, "html.parser")
    url_data = homesoup.find(class_="dropdown-menu SearchBar-keywordSearch")
    state_url_lst = url_data.find_all("li")
    for url in state_url_lst:
        url_dict[url.text.lower()] = homepage + url.a['href']
    return url_dict



def get_site_instance(site_url):
    '''Make an instances from a national site URL.
    
    Parameters
    ----------
    site_url: string
        The URL for a national site page in nps.gov
    
    Returns
    -------
    instance
        a national site instance
    '''
    raw_data = make_request_with_cache(site_url)
    parsed_data = BeautifulSoup(raw_data, "html.parser")
    title_info = parsed_data.find(class_="Hero-titleContainer clearfix")
    name = title_info.a.text
    category = title_info.span.text.strip()
    try:
        state = parsed_data.find(itemprop="addressRegion").text.strip()
        city = parsed_data.find(itemprop="addressLocality").text.strip()
        address = city + ", " + state
        zipcode = parsed_data.find(itemprop="postalCode").text.strip()
        phone = parsed_data.find(itemprop="telephone").text.strip()
        return NationalSite(category, name, address, zipcode, phone)
    except:
        return NationalSite(category, name)

def get_sites_for_state(state_url):
    '''Make a list of national site instances from a state URL.
    
    Parameters
    ----------
    state_url: string
        The URL for a state page in nps.gov
    
    Returns
    -------
    list
        a list of national site instances
    '''
    url_lst = []
    homepage = "https://www.nps.gov"
    raw_data = make_request_with_cache(state_url)
    parsed_data = BeautifulSoup(raw_data, "html.parser")
    ul_raw = parsed_data.find(id="parkListResultsArea")
    url_lst_raw = ul_raw.find_all("h3")
    for url in url_lst_raw:
        url_lst.append(get_site_instance(homepage + url.a["href"]))
    return url_lst



def get_nearby_places(site_object):
    '''Obtain API data from MapQuest API.
    
    Parameters
    ----------
    site_object: object
        an instance of a national site
    
    Returns
    -------
    dict
        a converted API return from MapQuest API
    '''
    baseurl = "http://www.mapquestapi.com/search/v2/radius"
    parameters = {"origin": site_object.zipcode, "radius": 10,
                  "maxMatches": 10, "ambiguities": "ignore",
                  "outFormat": "json", "key": secrets.API_KEY,
                  "units": "m"}
    resp = make_request_with_cache(baseurl, parameters, API=True)
    return resp

def print_nearby_places(api_dict):
    '''print the obtained places

    Parameters
    ----------
    api_dict : dictionary
        a converted API return from MapQuest API

    Returns
    -------
    list
        nearby places in a list
    '''
    places_lst = []
    for place in api_dict["searchResults"]:
        name = place.get("name", "No name")
        category = place["fields"].get("group_sic_code_name", "No category")
        address = place["fields"].get("address", "No address")
        city = place["fields"].get("city", "No city")
        if category == "":
            category = "No category"
        if address == "":
            address = "No address"
        if city == "":
            city = "No city"
        places_lst.append(name + " (" + category + "): " + address + ", " + city)
    for place in places_lst:
        print("-" + place)


if __name__ == "__main__":
    # part 1 : build the dictionary of state urls
    state_url_dict = build_state_url_dict()
    # wait for user to input a state name
    while True:
        commend = input("Enter a state name (e.g. Michigan, michigan) or \"exit\" \n:").lower()
        # check if it is a valid key
        try:
            target_url = state_url_dict[commend]
        except:
            if commend == "exit":
                break
            else:
                print("[Error] Enter proper state name" + "\n")
                continue
        # print the retrieved information
        return_parks = get_sites_for_state(target_url)

        print("-" * 35)
        print(f"List of national sites in {commend}")
        print("-" * 35)

        index = range(len(return_parks))
        for i in index:
            print(f"[{i+1}]" + " " + return_parks[i].info())

        commend2 = ""
        while True:
            commend2 = input("Choose the number for detail search or \"exit\" or \"back\" \n:")
            # check if input is integer
            try:
                number = int(commend2)
            except:
                if commend2 == "exit":
                    break
                elif commend2 == "back":
                    break
                else:
                    print("[Error] Invalid input \n")
                    print("-" * 50)
                    continue
            # check if input is within range
            if number-1 not in index:
                print("[Error] Invalid input \n")
                print("-" * 50)
                continue
            else:
                api_resp = get_nearby_places(return_parks[i-1])
                print("-" * 35)
                print(f"Places near {return_parks[number-1].name}")
                print("-" * 35)
                print_nearby_places(api_resp)
        if commend2 == "exit":
            break

    # get_nearby_places(get_site_instance('https://www.nps.gov/yell/index.htm'))
