import requests

class FollowerAlert:
    def get_followers(offset=0):
        username = "less-than-zero"
        followers = []
        offset = 0
        response = requests.get(f"https://api.mixcloud.com/{username}/followers/?offset={offset}")    
        data = response.json()
        followers += data['data']
        while "paging" in data and "next" in data['paging']:
            offset += 20
            response = requests.get(f"https://api.mixcloud.com/{username}/followers/?offset={offset}")
            data = response.json()
            followers += data['data']
        return {follower['name'] for follower in followers}