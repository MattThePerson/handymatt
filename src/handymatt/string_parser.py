from typing import Any
import parse #type:ignore

class StringParser:
    """ Class for converting string -> dict and vice versa given a list of filename formats """

    def __init__(self, formats: list[str]|str|None, use_tags:bool=True):
        if formats == None:
            raise Exception('No format(s) given to the Parser')
        self.formats = self._expand_formats(formats)
        self.use_tags = use_tags
        self.tags_sep = ' #'
    
    def parse(self, string: str) -> dict[str, Any] | None:
        for f in self.formats:
            string_cpy = string
            extracted_tags = []
            if self.use_tags:
                string_cpy, extracted_tags = self._extract_tags_from_string(string_cpy)
            parsed_data = parse.parse(f, string_cpy) #type:ignore
            if parsed_data != None:
                data = parsed_data.named #type:ignore
                if self.use_tags:
                    data['tags'] = extracted_tags
                return data #type:ignore
        return None
    
    def format(self, data: dict[str, Any]) -> str | None:
        data = self._prune_data(data)
        tags, data = self._separate_tags(data)
        for f in self.formats:
            f = self._remove_unsupported_format_codes(f)
            try:
                str = f.format(**data)
                if self.use_tags:
                    for tag in tags:
                        str += self.tags_sep + tag
                return str
            except KeyError:
                pass
        return None
    
    def _extract_tags_from_string(self, string: str):
        """ Extracts tags defined as `#TagName` from a string """
        tags: list[str] = []
        parts = string.split(self.tags_sep)
        for i in reversed(range(1, len(parts))):
            part = parts[i]
            if not ' ' in part:
                tags.append(part)
        return parts[0], tags
    
    @staticmethod
    def _separate_tags(data: dict[str, Any]):
        tags = []
        if 'tags' in data:
            tags = [ t.replace(' ', '-') for t in data['tags'] ]
            del data['tags']
        return tags, data
    
    @staticmethod
    def _remove_unsupported_format_codes(fmt: str):
        for code in [':S', ':D']:
            fmt = fmt.replace(code, '')
        return fmt
    
    def _expand_formats(self, formats: list[str] | str) -> list[str]:
        opt_sig = ';opt'
        if not isinstance(formats, list):
            formats = [formats]
        new_formats: list[str] = []
        for fmt_base in formats:
            format_parts = fmt_base.split()
            optional_count = len([c for c in format_parts if c.endswith(opt_sig)])
            for n in range(2**optional_count):
                parts: list[str] = []
                i = 0
                for part in format_parts:
                    if not part.endswith(opt_sig):
                        parts.append(part)
                    else:
                        mask = 2 ** i
                        if n & mask:
                            parts.append(part.replace(opt_sig, ''))
                        i += 1
                fmt = ' '.join(parts)
                new_formats.append(fmt)
        new_formats.sort(
            reverse=True, 
            key=lambda fmt: ( len(self._get_parse_in_fmt(fmt)), len(self._get_non_param_chars(fmt)) )
        )
        return new_formats
    
    @staticmethod
    def _get_parse_in_fmt(fmt: str) -> list[str]:
        return fmt.split('}')
    
    @staticmethod
    def _get_non_param_chars(fmt: str) -> str:
        parts = fmt.split('{')
        parts = [ p.split('}')[-1] for p in parts ]
        string = ''.join(parts).replace(' ', '')
        return string
    
    @staticmethod
    def _is_date(str: str):
        for c in '.-_':
            str = str.replace(c, '')
        return str.isnumeric()
    
    @staticmethod
    def _prune_data(data: dict[str, Any]):
        remove_keys = [ k for k, v in data.items() if v == None ]
        for k in remove_keys:
            del data[k]
        return data

    @staticmethod
    def _to_cc(string: str):
        if ' ' not in string:
            return string
        parts = [ p for p in string.lower().split(" ") if p != '' ]
        for i in range(len(parts)):
            part = parts[i]
            parts[i] = part[:1].upper() + part[1:]
        return ''.join(parts)
    
    @staticmethod
    def _from_cc(string: str):
        chars: list[str] = []
        for c in list(string):
            if c.isupper():
                chars.append(' ')
            chars.append(c)
        return ''.join(chars)

