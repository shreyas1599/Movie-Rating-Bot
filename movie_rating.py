import json 
import requests
import time
import urllib
from bs4 import BeautifulSoup
from urllib.request import Request,urlopen

TOKEN = "832013131:AAGhJKR5i6BSsjq1v5W3k01x6_aOekNlPZw"
URL = "https://api.telegram.org/bot{}/".format(TOKEN)

def get_url(url):
    response = requests.get(url)
    content = response.content.decode("utf8")
    return content

def get_json_from_url(url):
    content = get_url(url)
    js = json.loads(content)
    return js

def get_updates(offset=None):
    url = URL + "getUpdates?timeout=100"
    if offset:
        url += "&offset={}".format(offset)
    js = get_json_from_url(url)
    return js

def get_last_update_id(updates):
    update_ids = []
    for update in updates["result"]:
        update_ids.append(int(update["update_id"]))
    return max(update_ids)

def get_last_chat_id_and_text(updates):
    num_updates = len(updates["result"])
    last_update = num_updates - 1
    text = updates["result"][last_update]["message"]["text"]
    chat_id = updates["result"][last_update]["message"]["chat"]["id"]
    return (text,chat_id)

def send_message(text,chat_id,reply_markup=None):
    text = urllib.parse.quote_plus(text)
    url = URL + "sendMessage?text={}&chat_id={}".format(text,chat_id)
    if(reply_markup):
        url+="&reply_markup={}".format(reply_markup)
    get_url(url)

def rotten_tomatoes_movies(text,chat):
    page = requests.get("http://rottentomatoes.com/" + text)
    if page.status_code == 404:
        send_message("Sorry movie not found on Rotten Tomatoes\n",chat)
    else:
        soup = BeautifulSoup(page.content,'html.parser')
        average_tomatometer = "Average Tomatometer: " + soup.find("span",class_="mop-ratings-wrap__percentage").get_text().strip()
        average_audience_score = "Average Audience Score: " + soup.find("span",class_="mop-ratings-wrap__percentage--audience").get_text().replace("liked it","").strip()
        send_message("Rotten Tomatoes: \n" + average_tomatometer+"\n"+average_audience_score,chat)

def rotten_tomatoes_tv(text,chat):
    page = requests.get("http://rottentomatoes.com/" + text)
    if page.status_code == 404:
        send_message("Sorry TV show not found on Rotten Tomatoes\n",chat)
    else:
        soup = BeautifulSoup(page.content,'html.parser')
        if(soup.find("p",class_="noReviewText") is None):
            average_tomatometer = "Average Tomatometer: " + soup.find("div",class_="critic-score meter").get_text().strip()
            average_audience_score = "Average Audience Score: " + soup.find("div",class_="audience-score meter").get_text().replace("liked it","").strip()
            send_message("Rotten Tomatoes: \n" + average_tomatometer+"\n"+average_audience_score,chat)
        else:
            average_audience_score = "Average Audience Score: " + soup.find("div",class_="audience-score meter").get_text().replace("liked it","").strip() 
            average_tomatometer = "Average Tomatometer: No critic consensus yet"
            send_message("Rotten Tomatoes: \n" + average_tomatometer + "\n" + average_audience_score,chat)

def meta_critic_tv(text,chat):
    text = text.replace("_","-")
    user_agent = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7'
    headers={'User-Agent':user_agent,} 
    URL = "http://metacritic.com/" + text
    request=urllib.request.Request(URL,None,headers)
    try:
        response = urllib.request.urlopen(request)
        data = response.read()
        soup = BeautifulSoup(data,'html.parser')
        metacritic_rating = "Metascore: " + soup.find("span",class_="metascore_w").get_text()
        send_message(metacritic_rating,chat) 
    except:
        send_message("Sorry TV show not found on Metacritic",chat)

#This was used when I scraped the rating directly from Metacritic and did not use the OMDb API
"""
def meta_critic_movies(text,chat):
    text = text.replace("_","-")
    user_agent = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7'
    headers={'User-Agent':user_agent,} 
    URL = "http://metacritic.com/movie/" + text
    try:
        request=urllib.request.Request(URL,None,headers)
        response = urllib.request.urlopen(request)
        data = response.read()
        soup = BeautifulSoup(data,'html.parser')
        metacritic_rating = "Metascore: " + soup.find("span",class_="metascore_w").get_text()
        send_message(metacritic_rating,chat)
    except urllib.error.HTTPError:
        send_message("Sorry movie not available on Metacritic",chat)
"""

def omdb(text,chat):
    url = "http://www.omdbapi.com/?t=" + text + "&apikey=fb14230f"
    response = requests.get(url)
    try:
        content = response.content.decode("utf8")
        js = json.loads(content)
        send_message("IMDb Rating: " + js["imdbRating"],chat)
        send_message("Metacritic: " + js["Metascore"],chat)
    except:
        send_message("Sorry the movie does not exist on IMDb and Metacritic",chat)

def handle_updates(updates):
    for update in updates["result"]:
        try:
            text = update["message"]["text"]
            chat = update["message"]["chat"]["id"]
            if text == "/start":
                send_message("Format for searching for the review of a movie \nm/MovieName for movie \ntv/TVShow for a TV Show\nSo far "+
                    "I have only managed to get movies from IMDb. Will update soon",chat)
            else:
                text = text.replace(' ','_').lower()
                i=0
                for char in text:
                    if char == '/':
                        break
                    i = i+1
                kind = text[:i]
                if kind == 'm':
                    rotten_tomatoes_movies(text,chat)
                    text = text[i+1:] #To remove 'm/' from the text input
                    omdb(text,chat)
                    
                else:
                    rotten_tomatoes_tv(text,chat)
                    meta_critic_tv(text,chat)
                    text = text[i+1:]
        except KeyError:
            pass

def main():
    last_update_id = None
    while True:
        updates = get_updates(last_update_id)
        if(len(updates["result"]) > 0):
            last_update_id = get_last_update_id(updates) + 1
            handle_updates(updates)
        

if __name__ == "__main__":
    main()




