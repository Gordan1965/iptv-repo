# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring

import urllib.parse
import json
import hashlib
import os
import requests
import re


def php_call(r_text):
    javascript_code = r_text
    # Razdvoji linije JavaScript koda
    lines = javascript_code.split(';')
    # Pronađi liniju koja sadrži this.ajax_loader i this.portal_protocol
    target_line = None
    for line in lines:
        if "this.ajax_loader" in line and "this.portal_protocol" in line:
            target_line = line
            break

    # Ako nije pronađena odgovarajuća linija, vrati None
    if not target_line:
        return None

    # Izdvoji zadnji string iz linije
    last_string = target_line.split('+')[-1].strip().strip("/';")
    if not ".php" in last_string:
        last_string=""
    return last_string


class Address:
    def __init__(self, url, mac):
        self.url = url
        self.mac = mac


class Device:
    def __init__(self, mac):
        self.mac = mac
        self.url_encoded_mac = urllib.parse.quote(mac)
        self.serial_number = hashlib.md5(
            mac.encode('utf-8')).hexdigest().upper()[:13]
        self.device_id1 = hashlib.sha256(
            self.mac.encode('utf-8')).hexdigest().upper()
        self.device_id2 = hashlib.sha256(
            self.url_encoded_mac.encode('utf-8')).hexdigest().upper()
        pom = self.serial_number+self.mac
        self.sign = hashlib.sha256(pom.encode('utf-8')).hexdigest().upper()
        pom = self.url_encoded_mac
        self.hash = hashlib.sha1(pom.encode('utf-8')).hexdigest().upper()
        self.random = ""
        self.token = ""

def spremi_dict_u_datoteku(dict_data, file_name):
    if os.path.exists(file_name):
        os.remove(file_name)
    with open(file_name, 'w', encoding='utf-8') as f:
        json.dump(dict_data, f)

def procitaj_dict_iz_datoteke(file_name):
    with open(file_name, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_live_stream_url(url, headers):
    # Korištenje `with` kontekstualnog menadžera za automatsko zatvaranje sesije
    result={}
    with requests.Session() as session:
        # Postavi zaglavlja na session objekt
        session.headers.update(headers)
        # Izvrši GET zahtjev
        response = session.get(url)
        result=response.json()
    return result

def get_live_streams_in_group(group_id,url,headers,programi):
    rezultat={}
    with requests.Session() as session:
        session.headers.update(headers)
        pg=1
        while True:
            poziv_url=url+f"type=itv&action=get_ordered_list&genre={group_id}&force_ch_link_check=&fav=0&sortby=number&hd=0&p={pg}&JsHttpRequest=1-xml HTTP/1.1"
            response = session.get(poziv_url)
            result=response.json()
            print(result)
            mpi=result["js"]["max_page_items"]
            dld=len(result["js"]["data"])
            if dld>0:
                for d in result["js"]["data"]:
                    programi["js"]["data"].append(d)
                if pg==1:
                    rezultat=result
                else:
                    for d in result["js"]["data"]:
                        rezultat["js"]["data"].append(d)
            if dld<mpi:
                break
            pg+=1
    return rezultat

def get_movies_in_category(group_id,url,headers,pg):
    rezultat={}
    with requests.Session() as session:
        session.headers.update(headers)
        poziv_url=url+f"type=vod&action=get_ordered_list&category={group_id}&movie_id=0&season_id=0&episode_id=0&force_ch_link_check=&fav=0&sortby=added&hd=0&not_ended=0&p={pg}&from_ch_id=0&JsHttpRequest=1-xml"
        response = session.get(poziv_url)
        rezultat=response.json()
    return rezultat

def extract_http_part(s):
    http_index = s.find("http")
    if http_index != -1:
        return s[http_index:]
    else:
        return s

def extract_string_part(s,odstringa):
    http_index = s.find(odstringa)
    if http_index != -1:
        return s[http_index:]
    else:
        return s

def is_valid_url(url):
    # Regularni izraz za provjeru URL-a koji počinje s http/https i ima domenu
    regex = re.compile(
        r'^(http:\/\/|https:\/\/)'  # Provjera da li počinje sa http:// ili https://
        r'(([A-Za-z0-9-]+\.)+[A-Za-z]{2,})'  # Provjera domene (npr. example.com)
    )
    return re.match(regex, url) is not None

class MacLista:
    def __del__(self):
        self.session.close()

    def __init__(self, url, mac, php_poziv="portal.php", timeout=10, user_agent="Player (Linux; Android 7.1.2)"):
        mac = mac.upper().strip()
        url=url.strip()
        self.error=""
        self.php_poziv = php_poziv
        self.device = Device(mac)
        self.url = url
        self.mac = mac
        self.timeout = timeout
        self.version = "5.6.8"
        self.user_agent = user_agent
        self.token = ""
        self.headers={}
        self.session = requests.Session()
        self.profile = {}
        self.account_info = {}
        self.series_categories = {}
        self.vod_categories = {}
        self.live_categories = {}
        self.live_channels = {}
        self.xpcom_common_js=""
        domena = urllib.parse.urlparse(url).hostname
        cookie = f"mac={urllib.parse.quote(mac)}; stb_lang=en; timezone=Europe%2FParis; adid=19627C931EDA9;"
        self.session.headers.update({
            "Connection": "Keep-Alive",
            "User-Agent": user_agent,
            "Accept": '*/*',
            "Pragma": "no-cache",
            "X-User-Agent": "Model: MAG250; Link: WiFi",
            "Accept-Encoding": "gzip, deflate",
            "Host": domena,
            "Cookie": cookie
        })

    def inicijaliziraj_listu(self,modul):
        referer = self.url+"/index.html"
        r = self.session.get(referer, timeout=self.timeout)
        if r.status_code != 200:
            referer = self.url+"/c/index.html"
            r = self.session.get(referer, timeout=self.timeout)
            #if r.status_code != 200:
                #return
        self.session.headers.update({"Referer": referer})
        r = self.session.get(self.url+"/version.js", timeout=self.timeout)
        if r.status_code != 200:
            r = self.session.get(self.url+"/c/version.js",
                                 timeout=self.timeout)
            if r.status_code != 200:
                return
        version = r.text
        parts = version.split("'")
        if len(parts) > 1:
            self.version = parts[1]
        self.version = f"ImageDescription: 0.2.18-r23-250; ImageDate: Wed Aug 29 10:49:53 EEST 2018; PORTAL version: {self.version}; API Version: JS API version: 343; STB API version: 146; Player Engine version: 0x58c"
        self.version = urllib.parse.quote(self.version)
        r = self.session.get(self.url+"/xpcom.common.js", timeout=self.timeout)
        if r.status_code != 200:
            r = self.session.get(
                self.url+"/c/xpcom.common.js", timeout=self.timeout)
            if r.status_code != 200:
                return
        response_text = r.text
        if response_text:
            self.php_poziv = php_call(response_text)
            self.xpcom_common_js=response_text
        url_pom = self.url + f"/{self.php_poziv}?"
        adr = url_pom + \
            f"type=stb&action=handshake&prehash={self.device.hash}&JsHttpRequest=1-xml"
        r = self.session.get(adr, timeout=self.timeout)
        ok = True
        try:
            response_json = r.json()
            self.token = response_json.get("js", {}).get("token")
        except Exception as e:
            ok = False
        if not ok:
            url_pom = self.url + f"/c/{self.php_poziv}?"
            adr = url_pom + \
                f"type=stb&action=handshake&prehash={self.device.hash}&JsHttpRequest=1-xml"
            r = self.session.get(adr, timeout=self.timeout)
            ok = True
            try:
                response_json = r.json()
                self.token = response_json.get("js", {}).get("token")
            except Exception as e:
                ok = False
        if not ok:
            return
        if not self.token:
            return
        self.url = url_pom
        self.device.token = self.token
        metrics = f'"mac":"{self.device.mac}","sn":"{self.device.serial_number}","type":"STB","model":"MAG250","uid":"{self.device.device_id1}"'
        if response_json.get("js", {}).get("random"):
            self.device.random = response_json.get("js", {}).get("random")
            metrics += f',"random":"{self.device.random}"'
        metrics = urllib.parse.quote("{" + metrics + "}")
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        self.headers=self.session.headers
        get_profile_call = f"type=stb&action=get_profile&hd=1&ver={self.version}"
        get_profile_call += f"&num_banks=2&sn={self.device.serial_number}&stb_type=MAG250&client_type=STB&image_version=218&video_out=hdmi"
        get_profile_call += f"&device_id={self.device.device_id1}"
        get_profile_call += f"&device_id2={self.device.device_id1}"
        get_profile_call += f"&signature={self.device.sign}"
        get_profile_call += f"&metrics={metrics}"
        get_profile_call += "&auth_second_step=1&hw_version=1.7-BD-00&not_valid_token=0&hw_version_2=3c7ae5b19d3c84544afd34f190d0b1fbd988cc02&api_signature=262&prehash=&JsHttpRequest=1-xml"
        adr = self.url+get_profile_call
        r = self.session.get(adr, timeout=self.timeout)
        try:
            self.profile = r.json()
        except Exception as e:
            ok = False            
        adr = self.url + "type=stb&action=get_profile&auth_second_step=1&JsHttpRequest=1-xml"
        r = self.session.get(adr, timeout=self.timeout)
        self.profile = r.json()
        adr = self.url+"type=account_info&action=get_main_info&JsHttpRequest=1-xml"
        try:
            r = self.session.get(adr, timeout=self.timeout)
            if r.text:
                self.account_info = r.json()
        except Exception as e:
            self.error="account info"
        if modul=="2" or modul=="":
            try:        
                adr = self.url+"type=vod&action=get_categories&JsHttpRequest=1-xml"
                r = self.session.get(adr, timeout=self.timeout)
                self.vod_categories = r.json()
            except Exception as e:
                self.error="VOD categories"
        if modul=="3" or modul=="":                
            try:
                adr = self.url+"type=series&action=get_categories&JsHttpRequest=1-xml"
                r = self.session.get(adr, timeout=self.timeout)
                self.series_categories = r.json()
            except Exception as e:
                self.error="series categories"
        if modul=="1" or modul=="":
            try:
                adr = self.url+"type=itv&action=get_genres&JsHttpRequest=1-xml"
                r = self.session.get(adr, timeout=self.timeout)
                self.live_categories = r.json()
            except Exception as e:
                self.error="live categories"
            try:
                adr = self.url+"type=itv&action=get_all_channels&JsHttpRequest=1-xml"
                r = self.session.get(adr, timeout=self.timeout)
                self.live_channels = r.json()
            except Exception as e:
                self.error="live programs"
        
