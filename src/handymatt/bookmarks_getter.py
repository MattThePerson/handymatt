from typing import Any
import os
import json
import datetime
import platform
import subprocess

from enum import Enum
from dataclasses import dataclass, fields

from .wsl_paths import convert_to_wsl_path


# ==============================================================================
# OS detction
# ==============================================================================
def _is_Windows():
    return platform.system() == "Windows"

def _is_WSL():
    return (
        platform.system() == "Linux"
        and "microsoft" in platform.release().lower()
    )

def _is_Linux():
    return platform.system() == "Linux" and not _is_WSL()


def get_windows_localappdata():
    try:
        win_path = subprocess.check_output(
            ["cmd.exe", "/c", "echo", "%LOCALAPPDATA%"],
            text=True
        ).strip()
        return subprocess.check_output(
            ["wslpath", "-u", win_path],
            text=True
        ).strip()
    except Exception:
        return None



class BrowserFamily(Enum):
    CHROME = 1
    FIREFOX = 2


@dataclass
class Bookmark:
    # 'guid', 'id', 'name', 'type', 'url', 'location', 'date_added_fmt', 'date_last_used_fmt'
    id: str
    name: str
    type: str
    url: str
    location: str
    date_added: str
    date_last_used: str
    date_modified: str=""


def _bookmark_from_json(data: dict, strict: bool=False):
    if not isinstance(data, dict):
        raise TypeError(f"data not of type dict")
    if strict:
        return Bookmark(**data)
    field_names = {f.name for f in fields(Bookmark)}
    filtered = {k: v for k, v in data.items() if k in field_names}
    return Bookmark(**filtered)

# ==============================================================================
# region BookmarksGetter
# ==============================================================================

class BookmarksGetter:
    
    DEFAULT_PATHS_WINDOWS = {
        'chrome':  r'%localappdata%\Google\Chrome\User Data\BROWSER_PROFILE_NAME\Bookmarks',
        'brave':   r'%localappdata%\BraveSoftware\Brave-Browser\User Data\BROWSER_PROFILE_NAME\Bookmarks',
        'firefox': r'',
    }
    
    DEFAULT_PATHS_LINUX = {
        'chrome':  '',
        'brave':   '',
        'firefox': '',
    }
    
    def __init__(
            self,
            browser: str,
            profile: str='Default',
            localappdata: str|None=None,
        ):
        self.browser_family = self._get_browser_family(browser)
        if self.browser_family is BrowserFamily.FIREFOX:
            raise NotImplementedError(f'no support for firefox yet')
        self.bookmarks_file = self._get_bookmarks_file(browser, profile, localappdata)

    def get_bookmarks(
        self,
        foldername: str|None=None,
        domain: str|list[str]|None=None,
        sortby: str|None=None,
        reverse: bool=False,
    ) -> list[Bookmark]:
        
        if domain and not isinstance(domain, list):
            domain = [domain]
        
        # get bookmarks as dicts
        bookmarks_dicts: list[dict] = []
        match self.browser_family:
            case BrowserFamily.CHROME:
                bookmarks_dicts = self._get_bookmarks_Chrome(self.bookmarks_file)
            case BrowserFamily.FIREFOX:
                raise Exception(f"you shouldn't be here, wtf? firefox not support")
            case _:
                raise Exception(f"browser family wrong, wtfff? {self.browser_family}")
        
        bookmarks: list[Bookmark] = self._convert_to_Bookmarks_class(bookmarks_dicts)
        
        # filter foldername
        if foldername is not None:
            foldername = foldername.lower()
            if '/' in foldername: # ie: folder/subfolder
                bookmarks = [
                    b for b in bookmarks
                    if foldername in b.location.lower()
                ]
            else:
                bookmarks = [
                    b for b in bookmarks
                    if foldername in b.location.lower().split('/')
                ]
        
        # filter domain
        if domain is not None:
            bookmarks = [
                b for b in bookmarks
                if 0 != len([dom for dom in domain if dom.lower() in b.url.lower()])
            ]
        
        # sort
        bookmarks.sort(
            key=lambda bm: bm.date_added,
            reverse=reverse,
        )
        if sortby:
            bookmarks.sort(
                key=lambda bm: getattr(bm, sortby),
                reverse=reverse,
            )
        
        return bookmarks


    def _convert_to_Bookmarks_class(self, bookmarks_dicts: list[dict]) -> list[Bookmark]:
        bookmarks = []
        for bm_dict in bookmarks_dicts:
            try:
                bookmarks.append( _bookmark_from_json(bm_dict) )
            except Exception as e:
                raise Exception(f"unable to create Bookmarks class from dict \nexception: {e}")
        return bookmarks
        

    # ==========================================================================
    # region Bookmarks getting
    # ==========================================================================
    
    def _get_bookmarks_Chrome(self, file: str, foldername:str|None=None):
        with open(file, 'r') as f:
            bookmarks_json = json.load(f)
        base_objects = bookmarks_json['roots']['bookmark_bar'].get('children')
        return self._get_bookmarks_as_list_Chrome(base_objects)


    def _get_bookmarks_as_list_Chrome(self, array:list[dict[str, Any]], location:str|None=None):
        bookmarks:list[dict[str, Any]] = []
        for obj in array:
            if obj.get('type') == 'url':
                obj['location'] = location if location else ''
                obj['date_added'] = self._windows_epoch_readable(obj['date_added'])
                obj['date_last_used'] = self._windows_epoch_readable(obj['date_last_used'])
                if obj.get('date_modified'):
                    obj['date_modified'] = self._windows_epoch_readable(obj['date_modified'])
                bookmarks.append(obj)
            elif obj.get('type') == 'folder':
                name = obj.get('name')
                children = obj.get('children', [])
                new_location = f'{location}/{name}' if location else name
                bookmarks.extend(self._get_bookmarks_as_list_Chrome(children, new_location))
        return bookmarks
    
    
    # ==========================================================================
    # region File getting
    # ==========================================================================
    
    def _get_bookmarks_file(self, browser: str, profile: str, localappdata: str|None = None) -> str:
        if _is_Windows():
            file = self._get_bookmarks_file_Windows(browser, profile)
        elif _is_WSL():
            if localappdata is None:
                raise Exception(f"must declare localappdata folder when in WSL")
            file = self._get_bookmarks_file_WSL(browser, profile, localappdata)
        elif _is_Linux():
            file = self._get_bookmarks_file_Linux(browser, profile)
        else:
            raise Exception(f"operating system not known to mankind")
        if not os.path.exists(file):
            raise FileNotFoundError(f"default bookmarks file doesn't exist (for profile '{profile}')\n  looked for: '{file}'")
        return file

    def _get_bookmarks_file_Windows(self, browser: str, profile: str) -> str:
        default_path = self.DEFAULT_PATHS_WINDOWS.get(browser, None)
        if default_path is None:
            raise Exception(f"unknown default bookmarks path for: '{browser}'")
        default_path = default_path.replace(r'%localappdata%', os.getenv('LOCALAPPDATA', 'None'))
        default_path = default_path.replace('BROWSER_PROFILE_NAME', profile)
        return default_path
    
    def _get_bookmarks_file_WSL(self, browser: str, profile: str, localappdata: str) -> str:
        default_path = self.DEFAULT_PATHS_WINDOWS.get(browser, None)
        if default_path is None:
            raise Exception(f"unknown default bookmarks path for: '{browser}'")
        default_path = default_path.replace(r'%localappdata%', localappdata)
        default_path = default_path.replace('BROWSER_PROFILE_NAME', profile)
        return convert_to_wsl_path(default_path)
        
    def _get_bookmarks_file_Linux(self, browser: str, profile: str) -> str:
        raise NotImplementedError(f"no support for linux yet")

    def _get_browser_family(self, browser: str) -> BrowserFamily:
        if browser.lower() in ['chrome', 'chromium', 'brave', 'bravesoftware', 'edge']:
            return BrowserFamily.CHROME
        elif browser.lower() in ['firefox', 'waterfox', 'librewolf']:
            return BrowserFamily.FIREFOX
        else:
            raise Exception(f'unknown browser family for: {browser}')
    

    # ==========================================================================
    # region Static helpers
    # ==========================================================================
    
    @staticmethod
    def _windows_epoch_readable(us: str) -> str:
        windows_epoch_start = datetime.datetime(1601, 1, 1)
        return str(windows_epoch_start + datetime.timedelta(microseconds=int(us)))[:-7]
    
    @staticmethod
    def _get_relative_bookmark_location(location:str, foldername:str|None):
        if foldername is None:
            return location
        if location == foldername:
            return ''
        return location.replace(f'{foldername}/', '')

