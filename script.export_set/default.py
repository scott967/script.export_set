#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#     Copyright (C) 2025 Scott Smart
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
#
# pylint: disable=line-too-long,invalid-name

import csv
import xml.etree.ElementTree as ET
from pathlib import Path

import simplejson
import xbmc
import xbmcaddon
import xbmcgui

SIF = None
CSV = None
try:
    ADDON = xbmcaddon.Addon()
    ADDON_ID = ADDON.getAddonInfo('id')
    SIF = Path(simplejson.loads(xbmc.executeJSONRPC(
                '{"jsonrpc":"2.0", "method":"Settings.GetSettingValue", "params":{"setting":"videolibrary.moviesetsfolder"}, "id":1}'))['result']['value'])
    if (SIF is None) or (not SIF.name):
        xbmcgui.Dialog().ok(ADDON_ID, ADDON.getLocalizedString(32001))
        SIF = None
        xbmc.log(f'{ADDON_ID} invalid or no movie set info folder', xbmc.LOGWARNING)
        raise ValueError
except simplejson.JSONDecodeError:
    CSV = Path('C:/Video3') / 'sets3.csv'
except ValueError:
    CSV = None


ELEMENTS = ['title', 'overview', 'originaltitle']

def get_ET_trees(source, overwrite=False):
    """_summary_

    Args:
        source (_type_): _description_
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
        if CSV:
            try:
                tree.write(Path('x:/Movie Set Art') / row[1] / 'set.xml', encoding='utf-8', xml_declaration=True)
            except IOError as err:
                print(f'Could not write set.xml file due to {err}')
        elif SIF:
            try:
                (SIF / row[1]).mkdir(exist_ok=True)
                if overwrite or not ((SIF / row[1]) / 'set.xml').is_file():
                    tree.write((SIF / row[1]) / 'set.xml', encoding='utf-8', xml_declaration=True)
            except IOError as err:
                print(f'Could not write set.xml file due to {err}')

def export_set_data(sif:Path=None, csv_file:Path=None):
    """retrieves set data from library and creates set.xml
    """
    if csv_file:
        with open(csv_file, encoding='utf-8') as source:
            source_reader = csv.reader(source, delimiter='|')
            print(f'script.export_set export_set_data csv: {source_reader}', xbmc.LOGDEBUG)
            get_ET_trees(source_reader)
    if sif:
        replace_xml = xbmcgui.Dialog().yesno(ADDON_ID, ADDON.getLocalizedString(32004))
        response = simplejson.loads(xbmc.executeJSONRPC(
                '{"jsonrpc":"2.0", "method":"VideoLibrary.GetMovieSets", "params":{"properties":["title", "plot"]}, "id":1}'))
        if ('result' in response) and ('sets' in response['result']):
            lib_rows = []
            for i in range(response['result']['limits']['total']):
                lib_rows.append([0, response['result']['sets'][i].get('label', ''), response['result']['sets'][i].get('plot', '')])
            get_ET_trees(lib_rows, overwrite=replace_xml)

if __name__ == '__main__':
    if SIF:
        export_set_data(sif=SIF)
        xbmcgui.Dialog().notification(ADDON_ID, ADDON.getLocalizedString(32002))
    elif CSV:
        CSV = Path('C:/Video3/sets3.csv')
        export_set_data(csv_file=CSV)
    else:
        try:
            xbmc.log('script.export_set no valid CSV or SIF setting in Kodi', xbmc.LOGWARNING)
            xbmcgui.Dialog().notification(ADDON_ID, ADDON.getLocalizedString(32003))
        except Exception:
            print('script.export_set no valid CSV or SIF setting in Kodi')
