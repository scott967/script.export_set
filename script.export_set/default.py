#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#    Copyright (C) 2025 Scott Smart
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#    PathValidate package 3.3.1 Copyright (c) 2016-2025 Tsuyoshi Hombashi
#    The MIT license:
#
#    Permission is hereby granted, free of charge, to any person obtaining a copy
#    of this software and associated documentation files (the "Software"), to deal
#    in the Software without restriction, including without limitation the rights
#    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#    copies of the Software, and to permit persons to whom the Software is
#    furnished to do so, subject to the following conditions:
#
#    The above copyright notice and this permission notice shall be included in all
#    copies or substantial portions of the Software.
#
#
#
# pylint: disable=line-too-long,invalid-name
""" Kodi program (script) addon to export video library set/collection
data to "set.nfo" files in a user's MSIF folder tree.  When executed, a
Kodi yes/no dialog is raised to determine if existing set.nfo file should
be overwritten (updated).

Raises:
    ValueError: Custom handler for invalid or missing user MSIF  Generates
    a Kodi LOGERROR and UI ok popup.
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlencode, urlparse

import simplejson
#import smbclient
import xbmc
import xbmcaddon
import xbmcgui
from lib.pathvalidate import sanitize_filepath

MSIF = None
ADDON = xbmcaddon.Addon()
ADDON_ID = ADDON.getAddonInfo('id')
network = False

# get the Kodi user MSIF from Kodi settings.  If successful MSIF is valid Path object.
# Note:  Path class will return '.' as path if no argument provided in init.
try:
    xbmc.log(f'{ADDON_ID} json result {simplejson.loads(xbmc.executeJSONRPC(
                '{"jsonrpc":"2.0", "method":"Settings.GetSettingValue", "params":{"setting":"videolibrary.moviesetsfolder"}, "id":1}'))['result']['value']}')
    parsed_url = urlparse(simplejson.loads(xbmc.executeJSONRPC(
                '{"jsonrpc":"2.0", "method":"Settings.GetSettingValue", "params":{"setting":"videolibrary.moviesetsfolder"}, "id":1}'))['result']['value'])
    xbmc.log(f'{ADDON_ID} parsed_url {parsed_url}')
    if parsed_url.scheme == ('smb' or 'nfs'):
        network = True
        MSIF = Path(parsed_url.path)
    else:
        MSIF = Path(simplejson.loads(xbmc.executeJSONRPC(
                '{"jsonrpc":"2.0", "method":"Settings.GetSettingValue", "params":{"setting":"videolibrary.moviesetsfolder"}, "id":1}'))['result']['value'])
    if (MSIF is None) or (MSIF == Path('.')):
        xbmcgui.Dialog().ok(ADDON_ID, ADDON.getLocalizedString(32001))
        MSIF = None
        xbmc.log(f'{ADDON_ID} invalid or no movie set info folder',
                 xbmc.LOGWARNING)
        raise ValueError
except simplejson.JSONDecodeError:
    xbmcgui.Dialog().ok(ADDON_ID, ADDON.getLocalizedString(32001))
    MSIF = None
    xbmc.log(f'{ADDON_ID} invalid or no movie set info folder', xbmc.LOGWARNING)
except ValueError:
    xbmc.log(f'{ADDON_ID} unable to export', xbmc.LOGERROR)

ELEMENTS = ['title', 'overview', 'originaltitle'] #set/collection info to add to set.nfo


def get_ET_trees(source: list[list], overwrite=False):
    """Generate and save to MSIF set.nfo files for each row in source

    Args:
        source (list[list]): A list of movie set info.  Each row is a list of set ELEMENTS
        overwrite (bool, optional): Should existing set.nfo files be updated. Defaults to False.
    """
    for row in source:
        root = ET.Element("set")
        for index, element in enumerate(ELEMENTS):
            child = ET.SubElement(root, element)
            try:
                child.text = row[index+1]
            except IndexError:
                child.text = ''
        tree = ET.ElementTree(root)
        ET.indent(tree, space="\t", level=0)
        try:
            if not network:  #use Path semantics
                sani_path:Path = MSIF / sanitize_filepath(
                    Path(row[1].replace('/', '_')), replacement_text='_', platform="auto", normalize=False)
                xbmc.log(f'{ADDON_ID} the sani path is {sani_path} and exists {(sani_path).exists()}')
                (sani_path).mkdir(parents=True, exist_ok=True)  # Path objects don't allow "/"
                xbmc.log(f'{ADDON_ID} the sani path is {sani_path} and exists after mkdir {(sani_path).exists()}')
                if overwrite or not (sani_path / 'set.nfo').is_file():
                    tree.write(sani_path / 'set.nfo',
                            encoding='utf-8', xml_declaration=True, short_empty_elements=False)
                    xbmc.log(f'{ADDON_ID} wrote file {sani_path / "set.nfo"} and exists {(sani_path / "set.nfo").exists()}')
            else:  # use url string semantics
                url_path:str = urlencode((parsed_url.scheme, parsed_url.netloc, (parsed_url.path + sanitize_filepath(
                    Path(row[1].replace('/', '_')), replacement_text='_', platform="auto", normalize=False)), '', '', ''))
                xbmc.log(f'{ADDON_ID} url_path {url_path}')

        except IOError as err:
            xbmc.log(f'{ADDON_ID} Could not write set.nfo file due to {err}')

def export_set_data(sif: Path = None):
    """retrieves set data from library and creates set.nfo

    Args:
        sif (Path, optional): Path object for MSIF. Defaults to None.
    """
    if sif:
        replace_nfo = xbmcgui.Dialog().yesno(
            ADDON_ID, ADDON.getLocalizedString(32004))  # overwrite yes/no
        response = simplejson.loads(xbmc.executeJSONRPC(
            '{"jsonrpc":"2.0", "method":"VideoLibrary.GetMovieSets", "params":{"properties":["title", "plot"]}, "id":1}'))
        if ('result' in response) and ('sets' in response['result']):
            lib_rows = []  # list of set property rows (1 row per set)
            for i in range(response['result']['limits']['total']):
                lib_rows.append([0, response['result']['sets'][i].get(
                    'label', ''), response['result']['sets'][i].get('plot', '')])
            get_ET_trees(lib_rows, overwrite=replace_nfo)

if __name__ == '__main__':
    if MSIF:
        export_set_data(sif=MSIF)
        xbmcgui.Dialog().notification(ADDON_ID, ADDON.getLocalizedString(32002))
