import requests

def getShortUrl(longUrl: str):

    urlApi = "https://goo.su/api/links/create"

    params = {
        "url": longUrl
    }
    headers = {'content-type': 'application/json',
            'x-goo-api-token': '4gXb19TI19vF9Kqo6T08obr6U1vaHR8yR6d897yl4kDWIkdtwPvUXmwQFcpE'}
    
    response = requests.post(urlApi, params=params, headers=headers)

    return response.json()["short_url"]