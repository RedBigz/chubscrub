# urls
avatar_url = "https://avatars.charhub.io/avatars/%s/avatar.webp"
search_url = "https://api.chub.ai/search?search=&first=%i&topics=&excludetopics=&page=1&sort=default&venus=false&min_tokens=50&page=1"
char_url = "https://api.chub.ai/api/characters/%s?full=true"
char_frontend = "https://chub.ai/characters/%s"

import json
import cloudscraper
from PIL import Image
from os import makedirs
from os.path import join
from shutil import rmtree

from requests_toolbelt import MultipartEncoder

rmtree("out")

requests = cloudscraper.create_scraper()

def search(limit = 100):
    return requests.get(search_url % limit).json()

def getchar(path):
    return requests.get(char_url % path).json()

def simple_search(limit = 100):
    return [node["fullPath"] for node in search(limit)["data"]["nodes"]]

def getcharpng(path):
    return Image.open(requests.get(avatar_url % path, stream=True).raw)

searchresults = simple_search(1000)

for char in searchresults:
    print(char)

    dirpath = join("out", char)

    makedirs(dirpath, exist_ok=True)

    charpath = join(dirpath, "char.json")
    cardpath = join(dirpath, "card.png")
    metapath = join(dirpath, "metadata.txt")

    ch = getchar(char)
    chnode = ch["node"]
    chdef = chnode["definition"]

    name = chdef["name"]
    desc = chdef["description"]
    
    ex = chdef["example_dialogs"]
    fm = chdef["first_message"]
    ps = chdef["personality"]

    with open(metapath, "w+", encoding="utf-8") as meta:
        meta.write(f"{name}\nChub.ai Page: {char_frontend % char}")
    
    jsonout = json.dumps({
            "name": name,
            "description": ps,
            "avatar": "none",
            "personality": ps,
            "first_mes": fm,
            "mes_example": ex,
            "spec": "chara_card_v2",
            "spec_version": "2.0",
            "data": {
                "creator_notes": desc
            }
        })

    with open(charpath, "w+", encoding="utf-8") as charfile:
        charfile.write(jsonout)
    
    img = getcharpng(char)
    img.save(cardpath)

    with open(charpath, "rb") as charfile:
        enc = MultipartEncoder({"avatar": ("avatar.json", charfile, "text/json"), "file_type": "json"})
        rq = requests.post("http://127.0.0.1:8000/api/characters/import", headers={"Content-Type": enc.content_type, "Connection": "keep-alive", "Host": "localhost:8000"}, data=enc)

        print(rq.request.body)

        print(rq.text)
        fn = rq.json()["file_name"]
        
    with open(cardpath, "rb") as cardfile:
        enc = MultipartEncoder({"ch_name": name, "avatar": ("avatar.png", cardfile, "image/png"), "json_data": jsonout, "avatar_url": f"{fn}.png", "description": desc})
        requests.post("http://127.0.0.1:8000/api/characters/edit", headers={"Content-Type": enc.content_type, "Connection": "keep-alive", "Host": "localhost:8000"}, data=enc)