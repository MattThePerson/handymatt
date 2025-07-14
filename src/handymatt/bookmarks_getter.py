from typing import Any
import os
import json
import datetime


class BookmarksGetter:
    '''
    Class for getting bookmarks from your browser into your python code.
    
    Supported browsers:
    - Brave
    - Chrome
    '''
    DEFUALT_BOOKMARKS_PATHS = [
        r'%localappdata%\Google\Chrome\User Data\Default\Bookmarks',
        r'%localappdata%\BraveSoftware\Brave-Browser\User Data\Default\Bookmarks',
        # '/mnt/c/Users/stirl/AppData/Local/BraveSoftware/Brave-Browser/User Data/Default/Bookmarks' # WSL bandaid
    ]

    @classmethod
    def get_bookmarks(cls, browser: str, foldername:str|None=None, domain:str|list[str]|None=None, sortby:str|None=None, reverse:bool=False) -> list[dict[str, Any]] | None:
        """ Get bookmarks from broswer as a list of python dicts """
        if domain and not isinstance(domain, list):
            domain = [domain]
        bookmarks_path = next( (pth for pth in cls.DEFUALT_BOOKMARKS_PATHS if (browser.lower() in pth.lower() )) , None)
        if bookmarks_path == None:
            print('Cannot find bookmarks for browser named "{}"'.format(browser))
            return None
        bookmarks_path = bookmarks_path.replace(r'%localappdata%', os.getenv('LOCALAPPDATA', 'None'))
        with open(bookmarks_path, 'r') as f:
            bookmarks_json = json.load(f)
        if browser.lower() not in 'chrome chromium bravesoftware edge':
            print('ERROR: "{}" is in an unknown browser family'.format(browser))
            return None
        bookmarks_objects = cls._get_bookmarks_Chrome(bookmarks_json, foldername=foldername)
        bookmarks_objects = [ b for b in bookmarks_objects if ( foldername==None    or foldername.lower() in b.get('location','').lower().split('/')) ]
        bookmarks_objects = [ b for b in bookmarks_objects if ( domain==None        or 0 != len([dom for dom in domain if dom.lower() in b.get('url','').lower()]) ) ]
        for bm in bookmarks_objects: bm['location_relative'] = cls._get_relative_bookmark_location(bm['location'], foldername)
        if sortby and bookmarks_objects != []:
            if sortby not in bookmarks_objects[0].keys():
                raise Exception('ERROR in BookmarksGetter: No such key "{}"'.format(sortby))
            else:
                bookmarks_objects.sort( key=lambda obj: obj.get(sortby, ''), reverse=reverse )
        else:
            bookmarks_objects.sort( key=lambda obj: obj.get('date_added', ''), reverse=reverse )
        return bookmarks_objects

    # TODO: figure out foldername
    @classmethod
    def _get_bookmarks_Chrome(cls, bookmarks_json: dict[Any, Any], foldername:str|None=None):
        base_objects = bookmarks_json['roots']['bookmark_bar'].get('children')
        return cls._get_bookmarks_as_list_Chrome(base_objects)
    
    @classmethod
    def _get_bookmarks_as_list_Chrome(cls, array:list[dict[str, Any]], location:str|None=None):
        bookmarks:list[dict[str, Any]] = []
        for obj in array:
            if obj.get('type') == 'url':
                obj['location'] = location if location else ''
                obj['date_added_fmt'] = cls._windows_epoch_readable(obj['date_added'])
                obj['date_last_used_fmt'] = cls._windows_epoch_readable(obj['date_last_used'])
                if obj.get('date_modified'):
                    obj['date_modified_fmt'] = cls._windows_epoch_readable(obj['date_modified'])
                bookmarks.append(obj)
            elif obj.get('type') == 'folder':
                name = obj.get('name')
                children = obj.get('children', [])
                new_location = f'{location}/{name}' if location else name
                bookmarks.extend(cls._get_bookmarks_as_list_Chrome(children, new_location))
        return bookmarks


    ### HELPER METHODS
    @staticmethod
    def _windows_epoch_readable(us: str) -> str:
        windows_epoch_start = datetime.datetime(1601, 1, 1)
        return str(windows_epoch_start + datetime.timedelta(microseconds=int(us)))
    
    @staticmethod
    def _get_relative_bookmark_location(location:str, foldername:str|None):
        if foldername == None:
            return location
        if location == foldername:
            return ''
        return location.replace(f'{foldername}/', '')
