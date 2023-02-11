#import relevant libs
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

import time
import difflib
import requests
import regex as re
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns


#tokens from spotify dev account to access api
client_id = "b7773bb5826242d49de03c9e61fe2c15"
client_secret = "1179ce9968c948f09b2a3f71e016a95d"


### setting up spotipy search 
# authetification for spotpipy
auth_manager = SpotifyClientCredentials(client_id=client_id, 
                                        client_secret=client_secret)
# spotify search call
sp = spotipy.Spotify(auth_manager=auth_manager)


### setting up fetch from api endpoint with requests
#
auth_url = 'https://accounts.spotify.com/api/token'
base_url = 'https://api.spotify.com/v1/'

# get authentication from spotify dev
auth_response = requests.post(auth_url, {
    'grant_type': 'client_credentials',
    'client_id': client_id,
    'client_secret': client_secret,
})

# convert the response to JSON
auth_response_data = auth_response.json()

# fetch access token
access_token = auth_response_data['access_token']

# header for authentication
headers = {
    'Authorization': 'Bearer {token}'.format(token=access_token)
}


### loading and cleaning disney movie list
disney_df = pd.read_csv('../data/disney_musicals.csv')

name_year_tuples = list(zip(disney_df.Title,
                            disney_df.Year))


def deBracket(string):
    '''
    Description:
    Takes a string and removes all text within brackets

    Parameters:
     - string - str type object

    Returns:
    String type object 
    
    Example:
    >>> input:  deBracket('Beauty and the Beast (Original Motion Picture Soundtrack)')
    >>> output: Beauty and the Beast
    '''
    return re.sub('\([^)]*\)','',string).strip()

#function that returns True if strings are at least two thirds similar
def isSimilar(movie_title,album_title):
    
    '''
    Description:
    Compares whether the movie title and album title are similar enough to be considered a match

    Parameters:
     - movie_title - str type object
     - album_title - str type object

    Returns:
    Boolean True or False
    
    Example:
    >>> input:  isSimilar('Beauty and the Beast','Beauty and the Beast (Original Motion Picture Soundtrack)')
    >>> output: True

    '''
    album_title = deBracket(album_title) #remove text within brackets
    
    movie_split = movie_title.split()
    album_split = album_title.split()
    
    if len(album_split) > len(movie_split):
        album_split = album_split[:len(movie_split)]
        return SequenceMatcher(isjunk=None,a=movie_split,b=album_split).ratio()>=0.75
    else:
        return SequenceMatcher(isjunk=None,a=movie_title,b=album_title).ratio()>=0.75

def getAllAlbums(name):
    '''
    Description:
    Takes a movie `name` and finds all albums on spotify that match on name

    Parameters:
     - name - str type object

    Returns:
     - List object of matching albums if matches are found
     - Empty list object if no matches found
    '''
    #fetch album name search from spotify api endpoint
    r = requests.get(base_url+'search/?q={q}&type=album'.format(q=name.replace(' ','%20')), headers=headers)
    r = r.json()    #convert to json
    try: #if matches found
        all_albums = [album for album in r['albums']['items'] if isSimilar(name,deBracket(album['name']))]
    except IndexError: #index error occurs when no matches found
        all_albums = []    #return empty list
    return all_albums

def yearDelay(string_date,year,delay=0):
    '''
    Description:
    Inspects release date of album and compares it to release year of movie, returning True if the
    difference between the dates is no longer than `delay`
    
    Parameters:
     - string_date - str type object
     - year - int type object
     - delay - int type object with default value = 0
    
    Returns:
    Boolean True or False
    
    Example:
    >>> input:  yearDelay('1990',1990,1)
    >>> output: True
    '''
    #turns string date into integer year
    int_year = int(string_date[:4])
    #match if album released at most `delay` years after movie
    return int_year-year==delay

def matchYear(all_albums, year):
    '''
    Description:
    Takes list of album dictionaries and subselects based on if album release year is the same as
    movie release year, or if there is at most a 1-year delay between the two
    
    Parameters:
     - all_albums - list type object made up of dict type objects
     - year - int type object
    
    Returns:
     - List type object made up of dict type objects if matches are found
     - Empty list type object if no matches are found
    '''
                       
    album_dicts = [album for album in all_albums if yearDelay(album['release_date'],year)]
    
    if len(album_dicts)==0:
        album_dicts = [temp_dict for temp_dict in all_albums if yearDelay(album['release_date'],year,delay=1)]
    
    return album_dicts

def narrowAlbums(album_dicts):
    '''
    Description:
    Takes a list of album dictionaries which have been matched on name and release year and checks if
    any of them are different versions of the same album (e.g. Deluxe Version, Original soundtrack, 
    Broadway soundtrack) etc.

    Album is selected in order of following preference
        Deluxe Edition > Original Motion Picture Soundtrack > Not a Broadway album
    
    Parameters:
     - album_dicts - list of dict type objects
    
    Returns:
     - Dict object if the conditions match
     - List object identical to input if no conditions match
     
    Example:
    >>> input:  narrowAlbums([{..., 'name': 'Annie', ...}, {..., 'name': 'Annie Broadway Musical',...}]
    >>> output: {..., 'name':'Annie',...}
    '''
    check_deluxe = ['Deluxe Edition' in album['name'] for album in album_dicts]
    check_original = ['Original Motion' in album['name'] for album in album_dicts]
    check_broadway = ['Broadway' in album['name'] for album in album_dicts]
    
    if sum(check_deluxe)>0:
        album_dict = album_dicts[check_deluxe.index(True)]
    elif sum(check_original)>0:
        album_dict = album_dicts[check_original.index(True)]
    elif sum(check_broadway)>0:
        album_dict = album_dicts[check_broadway.index(False)]
    else:
        album_dict = album_dicts
        
    return album_dict
    
def matchCopyright(all_albums):
    '''
    Description:
    Takes list of album dictionaries and queries spotify api for their specific album id to identify
    copyright holders for those albums, returning list of all albums with a Disney copyright.
    
    Parameters:
     - all_albums - list of dictionaries
     
    Returns:
     - List of dictionaries
    '''
    temp_list = [] #to check if we end up with multiple matching albums
    #create list of all album ids
    album_ids = [album['id'] for album in all_albums]

    for (idx,album_id) in enumerate(album_ids):
        try:
            #fetch the correspondiing album for api endpoint
            r = requests.get(base_url+'albums/{album_id}'.format(album_id=album_id), headers=headers)
            #conver to json
            r = r.json()
        except ReadTimeout:    #spotify sometimes times out and we have to retry
            print('Spotify timed out... trying again...')
            #repeat as above
            r = requests.get(base_url+'albums/{album_id}'.format(album_id=album_id), headers=headers)
            r = r.json()

        #check if at least one of the copyrights belongs to Disney
        cr_check = sum(['Disney' in dic['text'] for dic in r['copyrights']])

        #confirm album has disney copyright
        if cr_check>0:
            temp_list.append(all_albums[idx])
            
    return temp_list

def addMovieInfo(album_dict,i,name,year):
    '''
    Description:
    Adds movie id to the dictionary for better maintenance and relational query
    
    Parameters:
     - album_dict - dict type object
     - i - int type object
     - name - str type object
     - year - int type object
     
    Returns:
    - dict type object with added keys and values
    '''
    album_dict['movie_id'] = i
    album_dict['movie_name'] = name
    album_dict['movie_year'] = year
    
    return album_dict



albums_list = []
copyright_list = []
failed_list = []
multiple_albums = []

headers = getAuth()
#search for Disney artist to obtain ID
for (i,tup) in enumerate(name_year_tuples):
    #assign anme an year
    name = tup[0]
    year = tup[1]
    #dictionary for specific inspection if everything fails
    movie_dict = {'movie_name':name, 'movie_year':year, 'movie_id':i}
    #all albums with a similar name to movie title
    all_albums = getAllAlbums(name)
    
    if len(all_albums)==0:    #if we have no matches
        failed_list.append(movie_dict)
    else:    
        #list of albums roughly matching release year from those matching names
        #returns list of matches, or empty list if no matches
        album_dicts = matchNameYear(all_albums,year)

        if len(album_dicts)==1:
            #if single match, list len is 1, so return the only match
            album_dict = album_dicts[0]
            #append with relational schema to movie
            albums_list.append(addMovieInfo(album_dict,i,name,year))
        elif len(album_dicts)>1:
            #if multiple matches, narrow down albums based on deluxe/original/not-broadway
            #if none of the albums meet conditions, the same input list is returned
            album_dict = narrowAlbums(album_dicts)    
            #check if still more than one album identified
            if type(album_dict)==list and len(album_dict)>1: 
                multiple_albums.append(movie_dict)    #keep track if multiple albums match
                album_dict = album_dict[0]    #just return first copy
            #append with relational schema to movie
            albums_list.append(addMovieInfo(album_dict,i,name,year))

        if len(album_dicts)==0: #no album matches
            #get list of albums that have disney copyright
            temp_list = matchCopyright(all_albums)

            if len(temp_list)>1:    #multiple matches
                multiple_albums.append(movie_dict)    #keep track
                copyright_list.append(movie_dict)    #keep track
                album_dict = temp_list[0]    #just return first copy
                #append with relational schema to movie
                albums_list.append(addMovieInfo(album_dict,i,name,year))
            elif len(temp_list)==1:
                copyright_list.append(movie_dict)    #keep track
                album_dict = temp_list[0]
                #append with relational schema to movie
                albums_list.append(addMovieInfo(album_dict,i,name,year))
            else:
                failed_list.append(movie_dict)