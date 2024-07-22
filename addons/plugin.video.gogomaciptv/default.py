# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring


import urllib.parse
import sys
import os
import xbmcaddon
import xbmcplugin
import xbmcgui
import xbmc
import xbmcvfs
import requests
import iptvklase
import shutil


addon = xbmcaddon.Addon()
addon_handle = int(sys.argv[1])
userdata_path = xbmcvfs.translatePath('special://userdata/')
#xbmc.log(f"ud: {userdata_path}", xbmc.LOGINFO)
addon_data_dir = xbmcvfs.translatePath(addon.getAddonInfo("profile"))
#xbmc.log(f"ad: {addon_data_dir}", xbmc.LOGERROR)
home_path = xbmcvfs.translatePath('special://home/')
addon = xbmcaddon.Addon()
addon_path = addon.getAddonInfo('path')
resources_path = os.path.join(addon_path, 'resources')
xbmc.log(f"rp: {resources_path}", xbmc.LOGINFO)
cacheDir = os.path.join(addon_data_dir, "cache")
mac_file_path = os.path.join(addon_data_dir, "mac.txt")
if not os.path.exists(cacheDir):
    #xbmc.log(f"cache: {cacheDir}", xbmc.LOGERROR)
    os.makedirs(cacheDir)

def copy_file_if_exists(source_path, destination_path):
    # Provjera postoji li datoteka
    if os.path.exists(source_path):
        try:
            # Kopiranje datoteke na novu lokaciju
            shutil.copy(source_path, destination_path)
            print(f"Datoteka '{source_path}' je uspješno kopirana u '{destination_path}'.")
        except IOError as e:
            print(f"Greška pri kopiranju datoteke: {e}")
    else:
        print(f"Datoteka '{source_path}' ne postoji.")

def check_file_for_http(filename):
    if not os.path.exists(filename):
        print(f"Datoteka {filename} ne postoji.")
        return False
    with open(filename, 'r') as file:
        for line in file:
            if line.startswith("http"):
                return True
    return False

def build_url(query):
    return sys.argv[0] + '?' + urllib.parse.urlencode(query)

def load_from_internet():
    adresa_lista = addon.getSetting("internetAdresa")
    if not adresa_lista:
        xbmcgui.Dialog().notification("Error",
                                      "Please configure the URL in addon settings", xbmcgui.NOTIFICATION_ERROR, 5000)
        addon.openSettings()
        adresa_lista = addon.getSetting("internetAdresa")
    if not adresa_lista:
        xbmcgui.Dialog().notification("Error", "No URL configured. Exiting addon.",
                                      xbmcgui.NOTIFICATION_ERROR, 5000)
        sys.exit()
    try:        
        response = requests.get(adresa_lista, timeout=5)
        response.raise_for_status()
        lines = response.text.splitlines()
        if lines.count == 0:
            if check_file_for_http(mac_file_path):
                xbmcgui.Dialog().notification("Error", "Failed to fetch addresses from the URL, using cached mac list",
                                            xbmcgui.NOTIFICATION_ERROR, 5000)
                return
            else:
                xbmc.log(
                    f"Failed to fetch addresses from: {adresa_lista}", xbmc.LOGERROR)
                xbmcgui.Dialog().notification("Error", "Failed to fetch addresses from the URL",
                                            xbmcgui.NOTIFICATION_ERROR, 5000)
                sys.exit()
        with open(mac_file_path, "w") as file:
            for l in lines:
                l = iptvklase.extract_http_part(l).rstrip()
                if l:
                    file.write(l + '\n')

    except requests.RequestException as e:
        xbmc.log(f"Failed to fetch addresses {e}", xbmc.LOGERROR)
        if check_file_for_http(mac_file_path):
            xbmcgui.Dialog().notification("Error", "Failed to fetch addresses from the URL, using cached mac list",
                                          xbmcgui.NOTIFICATION_ERROR, 5000)
        else:
            xbmcgui.Dialog().notification("Error", "Failed to fetch addresses from the URL",
                                          xbmcgui.NOTIFICATION_ERROR, 5000)
            sys.exit()


def load_from_addon_storage():
    xbmc.log(f"Ucitavanje iz local storage: {mac_file_path}", xbmc.LOGERROR)
    if not mac_file_path:
        xbmcgui.Dialog().notification("Error", "No path configured. Exiting addon.",
                                      xbmcgui.NOTIFICATION_ERROR, 5000)
        sys.exit()
    try:
        if not os.path.exists(mac_file_path):
                with open(mac_file_path, 'w') as file:
                    pass 
        with open(mac_file_path, "r") as file:
            lines = file.readlines()
        addresses = []
        for line in lines:
            line = iptvklase.extract_http_part(line)
            parts = line.split(',')
            if len(parts) == 2:
                url, mac = parts
                addresses.append(iptvklase.Address(url.strip(), mac.strip()))
            else:
                xbmc.log(f"Skipping malformed line: {line}", xbmc.LOGWARNING)
        return addresses
    except:
        xbmcgui.Dialog().notification("Error", "Failed to load lists from addon storage",
                                      xbmcgui.NOTIFICATION_ERROR, 5000)
        sys.exit()



def load_from_local_storage():
    adresa_lista = addon.getSetting("lokalnaAdresa")
    if not adresa_lista:
        xbmcgui.Dialog().notification("Error",
                                      "Please configure the path in addon settings", xbmcgui.NOTIFICATION_ERROR, 5000)
        addon.openSettings()
        adresa_lista = addon.getSetting("lokalnaAdresa")
    if not adresa_lista:
        xbmcgui.Dialog().notification("Error", "No path configured. Exiting addon.",
                                      xbmcgui.NOTIFICATION_ERROR, 5000)
        sys.exit()
    copy_file_if_exists(adresa_lista,mac_file_path)


def load_addresses():
    izvor_tip = addon.getSetting("izvorTip")
    if izvor_tip == "0":
        load_from_internet()
    elif izvor_tip=="1":
        load_from_local_storage()

# Function to list unique servers
def get_unique_ordered_urls(addresses):
    unique_urls = []
    seen_urls = set()

    for address in addresses:
        if address.url not in seen_urls:
            unique_urls.append(address.url)
            seen_urls.add(address.url)

    return unique_urls

def glavni_izbornik():
    server_url = sys.argv[0] + \
        '?action=list_servers&modul=1'
    li = xbmcgui.ListItem("Live TV")
    li.setArt({'icon': os.path.join(resources_path, 'television.png'), 'thumb': os.path.join(resources_path, 'television.png')})
    xbmcplugin.addDirectoryItem(
        handle=addon_handle, url=server_url, listitem=li, isFolder=True)
    server_url = sys.argv[0] + \
        '?action=list_servers&modul=2'
    li = xbmcgui.ListItem("Movies")
    li.setArt({'icon': os.path.join(resources_path, 'film.png'), 'thumb': os.path.join(resources_path, 'film.png')})    
    xbmcplugin.addDirectoryItem(
        handle=addon_handle, url=server_url, listitem=li, isFolder=True)
    server_url = sys.argv[0] + \
        '?action=list_servers&modul=3'
    # li = xbmcgui.ListItem("Series")
    # xbmcplugin.addDirectoryItem(
    #     handle=addon_handle, url=server_url, listitem=li, isFolder=True)
    xbmcplugin.endOfDirectory(addon_handle)

def dodaj_nove_filmove(novi_filmovi, datotekafilmova):
    filmovi = iptvklase.procitaj_dict_iz_datoteke(
        datotekafilmova)
    for d in novi_filmovi["js"]["data"]:
        if not da_li_postoji_id_filma(d["id"],filmovi):
            filmovi["js"]["data"].append(d)
    iptvklase.spremi_dict_u_datoteku(filmovi,datotekafilmova)

def da_li_postoji_id_filma(id,filmovi):
    for d in filmovi["js"]["data"]:
        if d["id"]==id:
            return True
    return False

def list_movies(idc,pg):
    server = iptvklase.procitaj_dict_iz_datoteke(
        os.path.join(cacheDir, "server.txt"))
    headers = iptvklase.procitaj_dict_iz_datoteke(
        os.path.join(cacheDir, "header.txt"))
    filmovi=iptvklase.get_movies_in_category(
        idc, server["baseUrl"], headers, pg)
    if filmovi:
        if not os.path.exists(os.path.join(cacheDir, "filmovi.txt")):
            iptvklase.spremi_dict_u_datoteku(
                filmovi, os.path.join(cacheDir, "filmovi.txt"))
        else:
            dodaj_nove_filmove(filmovi, os.path.join(cacheDir, "filmovi.txt"))    
        for index, film in enumerate(filmovi['js']['data'], start=1):
            server_url = sys.argv[0] + \
                f'?action=play_movie&id={film["id"]}&modul=2'
            k = film["name"]
            li = xbmcgui.ListItem(f"{k}")
            if film["screenshot_uri"]:
                img=film["screenshot_uri"]
                li.setArt({
                    'icon': img,
                    'thumb': img
                })
            xbmcplugin.addDirectoryItem(
                handle=addon_handle, url=server_url, listitem=li, isFolder=False)
        next_page = pg + 1
        server_url = sys.argv[0] + \
                f'?action=list_programs&categorie={idc}&modul=2&pg={next_page}'
        li = xbmcgui.ListItem(f'Next Page ({next_page})>>')
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=server_url, listitem=li, isFolder=True)

        xbmcplugin.endOfDirectory(addon_handle)


def list_servers(addresses,modul):
    izvor_tip = addon.getSetting("izvorTip")
    if izvor_tip!="0":
        dialog_url = sys.argv[0]+'?action=open_add_list_dialog'
        li = xbmcgui.ListItem(label='Dodaj MAC listu')
        #li.setArt({'icon': 'path/to/add_icon.png'})  # Postavljanje ikone za "Dodaj URL"
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=dialog_url, listitem=li, isFolder=False)

    # unique_urls = {address.url for address in addresses}
    unique_urls = get_unique_ordered_urls(addresses)
    for index, url in enumerate(unique_urls, start=1):
        server_url = sys.argv[0] + f'?action=list_macs&server={url}&modul={modul}'
        li = xbmcgui.ListItem(f"{url}")
        xbmcplugin.addDirectoryItem(
            handle=addon_handle, url=server_url, listitem=li, isFolder=True)
    xbmcplugin.addSortMethod(addon_handle, xbmcplugin.SORT_METHOD_NONE)
    xbmcplugin.addSortMethod(addon_handle, xbmcplugin.SORT_METHOD_LABEL)
    # xbmcplugin.addSortMethod(addon_handle, xbmcplugin.SORT_METHOD_PLAYLIST_ORDER)
    # xbmcplugin.addSortMethod(addon_handle, xbmcplugin.SORT_METHOD_TITLE)
    xbmcplugin.endOfDirectory(addon_handle)


def list_macs(adrese, server,modul):
    xbmcplugin.setPluginCategory(addon_handle, server)
    for index, url in enumerate(adrese, start=1):
        server_url = sys.argv[0] + \
            f'?action=list_categories&server={server}&mac={url.mac}&modul={modul}'
        li = xbmcgui.ListItem(f"{url.mac}")
        xbmcplugin.addDirectoryItem(
            handle=addon_handle, url=server_url, listitem=li, isFolder=True)

    xbmcplugin.endOfDirectory(addon_handle)


def list_categories(kategorije,modul):
    if os.path.exists(os.path.join(cacheDir, "filmovi.txt")):
        os.remove(os.path.join(cacheDir, "filmovi.txt"))
    for index, kategorija in enumerate(kategorije, start=1):
        if not kategorija["id"] == "*":
            server_url = sys.argv[0] + \
                f'?action=list_programs&categorie={kategorija["id"]}&modul={modul}&pg=1'
            k = kategorija["title"]
            li = xbmcgui.ListItem(f"{k}")
            xbmcplugin.addDirectoryItem(
                handle=addon_handle, url=server_url, listitem=li, isFolder=True)
    xbmcplugin.endOfDirectory(addon_handle)


def list_programs(programi, kategorija):
    for index, program in enumerate(programi, start=1):
        if str(program["tv_genre_id"]) == kategorija:
            server_url = sys.argv[0] + \
                f'?action=play_program&programid={program["id"]}'
            k = program["name"]
            img = program["logo"]
            li = xbmcgui.ListItem(label=f"{k}", label2=f"{k}")
            li.setArt({
                'icon': img,
                'thumb': img
            })
            xbmcplugin.addDirectoryItem(
                handle=addon_handle, url=server_url, listitem=li, isFolder=False)
    xbmcplugin.endOfDirectory(addon_handle)


def dodaj_praznu_kategoriju(programi, kategorija):
    for d in programi["js"]["data"]:
        if str(d["tv_genre_id"]) == kategorija:
            return
    server = iptvklase.procitaj_dict_iz_datoteke(
        os.path.join(cacheDir, "server.txt"))
    headers = iptvklase.procitaj_dict_iz_datoteke(
        os.path.join(cacheDir, "header.txt"))
    iptvklase.get_live_streams_in_group(
        kategorija, server["baseUrl"], headers, programi)
    iptvklase.spremi_dict_u_datoteku(
        programi, os.path.join(cacheDir, "livechannels.txt"))

def lista_kategorija(server,mac,modul):
    lista = iptvklase.MacLista(server, mac)
    lista.inicijaliziraj_listu(modul)
    bazni_podaci = {
        'server': f'{server}',
        'mac': f'{mac}',
        'baseUrl': f'{lista.url}'
    }
    iptvklase.spremi_dict_u_datoteku(
        bazni_podaci, os.path.join(cacheDir, "server.txt"))
    iptvklase.spremi_dict_u_datoteku(
        dict(lista.session.headers), os.path.join(cacheDir, "header.txt"))
    if modul=="2":
        if lista.vod_categories:
            if os.path.exists(os.path.join(cacheDir, "filmovi.txt")):
                os.remove(os.path.join(cacheDir, "filmovi.txt"))
            iptvklase.spremi_dict_u_datoteku(
                lista.vod_categories, os.path.join(cacheDir, "vodcategories.txt"))
            list_categories(lista.vod_categories["js"],"2")
        else:
            xbmcgui.Dialog().notification("Obavijest",
                                            "Lista nema filmova", xbmcgui.NOTIFICATION_INFO, 5000)              
    elif modul=="3":
        if lista.series_categories:
            iptvklase.spremi_dict_u_datoteku(
                lista.series_categories, os.path.join(cacheDir, "seriescategories.txt"))
            list_categories(lista.series_categories["js"],"3")
        else:
            xbmcgui.Dialog().notification("Obavijest",
                                            "Lista nema serija", xbmcgui.NOTIFICATION_INFO, 5000)  
    elif modul=="1":
        if lista.live_categories:
            iptvklase.spremi_dict_u_datoteku(
                lista.live_channels, os.path.join(cacheDir, "livechannels.txt"))
            iptvklase.spremi_dict_u_datoteku(
                lista.live_categories, os.path.join(cacheDir, "livecategories.txt"))
            list_categories(lista.live_categories["js"],"1")
        else:
            xbmcgui.Dialog().notification("Obavijest",
                                            "Lista nema kategorija", xbmcgui.NOTIFICATION_INFO, 5000)    
def reproduciraj_film(idf):
    filmovi = iptvklase.procitaj_dict_iz_datoteke(
        os.path.join(cacheDir, "filmovi.txt"))
    server = iptvklase.procitaj_dict_iz_datoteke(
        os.path.join(cacheDir, "server.txt"))
    header = iptvklase.procitaj_dict_iz_datoteke(
        os.path.join(cacheDir, "header.txt"))
    found_film={}
    for film in filmovi["js"]["data"]:
        if str(film["id"]) == idf:
            found_film = film
            break

    if found_film:
        cmd=found_film["cmd"]
        
        link = cmd
        link = link.replace(" h", "+h")
        link = urllib.parse.quote(link)
        url = server["baseUrl"] + \
            f"type=vod&action=create_link&forced_storage=undefined&download=0&cmd={link}&JsHttpRequest=1-xml"
        cmd = iptvklase.extract_http_part(cmd)
        xbmc.log(
            f"naziv {found_film['name']}  cmd: {cmd}  cmd za url: {cmd} url: {url}", xbmc.LOGINFO)
        ls = iptvklase.get_live_stream_url(url, header)
        xbmc.log(
            f"java script od get_live_tream_url: {ls}", xbmc.LOGINFO)
        url_programa = ""
        try:
            url_programa = ls["js"]["cmd"]
        except:
            url_programa = ""
        logo = ""
        try:
            logo = found_film["screenshot_uri"]
        except:
            logo = ""
        token = ""
        if not url_programa:
            xbmc.log("program nije pronađen", xbmc.LOGINFO)
            return
        url_programa = iptvklase.extract_http_part(url_programa)
        xbmc.log(f"url videa: {url_programa}", xbmc.LOGINFO)
        list_item = xbmcgui.ListItem(label=found_film['name'])
        xbmc.log(
            f"logo URL: {logo}", xbmc.LOGINFO)
        if logo:
            list_item.setArt({'icon': logo, 'fanart': logo})
        list_item.setInfo('video',
                            {'title': found_film['name'],
                            'plot': found_film['name']
                            }
                            )
        # Postavljanje User-Agent zaglavlja
        headers = {'User-Agent': "Player (Linux; Android 7.1.2)"}
        list_item.setPath(url)
        xbmc.log(f"url za list item: {url}", xbmc.LOGINFO)
        list_item.setProperty(
            'inputstream.adaptive.manifest_type', 'hls')
        list_item.setProperty('inputstream.adaptive.stream_headers', '&'.join(
            [f"{k}={v}" for k, v in headers.items()]))
        if url_programa.endswith("==.ts"):
            url_programa = url_programa[:-3]
        xbmc.Player().play(url_programa, list_item)
    else:
        xbmc.log("program nije pronađen", xbmc.LOGINFO)


def reproduciraj_program(idp):
    programi = iptvklase.procitaj_dict_iz_datoteke(
        os.path.join(cacheDir, "livechannels.txt"))
    server = iptvklase.procitaj_dict_iz_datoteke(
        os.path.join(cacheDir, "server.txt"))
    header = iptvklase.procitaj_dict_iz_datoteke(
        os.path.join(cacheDir, "header.txt"))
    found_program = {}

    for program in programi["js"]["data"]:
        if str(program["id"]) == idp:
            found_program = program
            break

    if found_program:
        cmd = found_program['cmd']
        link = cmd
        link = link.replace(" h", "+h")
        link = urllib.parse.quote(link)
        url = server["baseUrl"] + \
            f"type=itv&action=create_link&forced_storage=undefined&download=0&cmd={link}&JsHttpRequest=1-xml"
        cmd = iptvklase.extract_http_part(cmd)
        xbmc.log(
            f"naziv {found_program['name']}  cmd: {cmd}  cmd za url: {cmd} url: {url}", xbmc.LOGINFO)
        ls = iptvklase.get_live_stream_url(url, header)
        xbmc.log(
            f"java script od get_live_tream_url: {ls}", xbmc.LOGINFO)
        url_programa = ""
        try:
            url_programa = ls["js"]["cmd"]
        except:
            url_programa = ""
        logo = ""
        try:
            logo = found_program["logo"]
        except:
            logo = ""
        token = ""
        if url_programa:
            url_programa = iptvklase.extract_http_part(url_programa)
            i = url_programa.find("?play")
            if i != -1:
                token = url_programa[i:]
        else:
            url_programa = cmd
        if cmd.find("localhost") != -1:
            if iptvklase.is_valid_url(cmd):
                url_programa = cmd + token
        else:
            url_programa = cmd
        xbmc.log(f"url videa: {url_programa}", xbmc.LOGINFO)
        list_item = xbmcgui.ListItem(label=found_program['name'])
        xbmc.log(
            f"logo URL: {logo}", xbmc.LOGINFO)
        if logo:
            list_item.setArt({'icon': logo, 'fanart': logo})
        list_item.setInfo('video',
                            {'title': found_program['name'],
                            'plot': found_program['name']
                            }
                            )
        # Postavljanje User-Agent zaglavlja
        headers = {'User-Agent': "Player (Linux; Android 7.1.2)"}
        list_item.setPath(url)
        xbmc.log(f"url za list item: {url}", xbmc.LOGINFO)
        list_item.setProperty(
            'inputstream.adaptive.manifest_type', 'hls')
        list_item.setProperty('inputstream.adaptive.stream_headers', '&'.join(
            [f"{k}={v}" for k, v in headers.items()]))
        if url_programa.endswith("==.ts"):
            url_programa = url_programa[:-3]
        xbmc.Player().play(url_programa, list_item)
    else:
        xbmc.log("program nije pronađen", xbmc.LOGINFO)



def router(paramstring):
    params = ""
    if paramstring:
        xbmc.log(f"{addon.getAddonInfo('id')}", xbmc.LOGINFO)
        params = dict(part.split('=') for part in paramstring[1:].split('&'))
    if not params:
        glavni_izbornik()
        # xbmc.log(f"{paramstring} adresa datoteke: {mac_file_path}", xbmc.LOGINFO)
        # load_addresses()
        # addresses=load_from_addon_storage()
        # list_servers(addresses)
    else:
        action = params.get('action')
        xbmc.log(f"{action}", xbmc.LOGINFO)
        if action=="list_servers":
            load_addresses()
            addresses=load_from_addon_storage()
            list_servers(addresses,params.get('modul'))
        if action=='open_add_list_dialog':
            open_add_list_dialog()
            return
        if action == 'list_macs':
            addresses=load_from_addon_storage()
            server = urllib.parse.unquote(params.get('server'))
            xbmc.log(f"{server}", xbmc.LOGINFO)
            server_addresses = [
                address for address in addresses if address.url == server]
            list_macs(server_addresses, server,params.get('modul'))
        elif action == 'list_categories':
            server = urllib.parse.unquote(params.get('server'))
            mac = urllib.parse.unquote(params.get('mac'))
            lista_kategorija(server,mac,params.get('modul'))
        elif action == "list_programs":
            modul=params.get('modul')
            if modul=="1":
                idc = urllib.parse.unquote(params.get('categorie'))
                programi = iptvklase.procitaj_dict_iz_datoteke(
                    os.path.join(cacheDir, "livechannels.txt"))
                dodaj_praznu_kategoriju(programi, idc)
                list_programs(programi["js"]["data"], idc)
            elif modul=="2":
                idc = urllib.parse.unquote(params.get('categorie'))
                page=int(urllib.parse.unquote(params.get('pg')))
                xbmc.log(f"Promjena stranice filmova stranica: {page}", xbmc.LOGINFO)
                list_movies(idc,page)
        elif action == "play_program":
            idp = urllib.parse.unquote(params.get('programid'))
            reproduciraj_program(idp)
        elif action=="play_movie":
            idf = urllib.parse.unquote(params.get('id'))
            reproduciraj_film(idf)            

def open_add_list_dialog():
    # Otvori dijaloški okvir s tekstualnim poljem i dva gumba
    keyboard = xbmc.Keyboard('', 'Unesi adresu liste i MAC')
    keyboard.doModal()
    if keyboard.isConfirmed():
        new_url = keyboard.getText()
        if new_url:
            save_url_to_file(new_url)
            xbmc.executebuiltin('Container.Refresh')

def save_url_to_file(url):
    izvor_tip = addon.getSetting("izvorTip")
    if mac_file_path:
        xbmc.log(f"dodavanje nove liste addonstorage datoteka: {mac_file_path}", xbmc.LOGINFO)
        with open(mac_file_path, "a") as file:
            file.write(url + '\n')
    if izvor_tip=="1":
        datoteka=addon.getSetting("lokalnaAdresa")
        xbmc.log(f"dodavanje nove liste lokalna datoteka datoteka: {datoteka}", xbmc.LOGINFO)
        if datoteka:
            with open(datoteka, "a") as file:
                file.write(url + '\n')




if __name__ == '__main__':
    xbmc.log(f"pokrenut addon: {sys.argv[2]}", xbmc.LOGINFO)
    router(sys.argv[2])
