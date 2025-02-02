import parse

class StringParser:

    def __init__(self, formats, use_tags=True):
        self.formats = self.expand_formats(formats)
        self.use_tags = use_tags
        self.tags_sep = ' #'
    
    def parse(self, string):
        if self.formats == None:
            raise Exception('No format(s) given to the Parser')
        for f in self.formats:
            string_cpy = string
            if self.use_tags:
                string_cpy, tags = self.extract_tags(string_cpy)
                # for t in tags:
                #     string_cpy = string_cpy.replace( f'{self.tags_sep}{t}', '' )
            parsed_data = parse.parse(f, string_cpy)
            if parsed_data != None:
                data = parsed_data.named
                if self.use_tags:
                    data['tags'] = tags
                return data
        return None
    
    def format(self, data):
        data = self.prune_data(data)
        if self.formats == None:
            raise Exception('No format(s) given to the Parser')
        tags, data = self.separate_tags(data)
        for f in self.formats:
            f = self.remove_unsupported_format_codes(f)
            try:
                str = f.format(**data)
                if self.use_tags:
                    for tag in tags:
                        str += self.tags_sep + tag
                return str
            except KeyError:
                pass
        return None
    
    def extract_tags(self, string):
        tags = []
        parts = string.split(self.tags_sep)
        for i in reversed(range(1, len(parts))):
            part = parts[i]
            if not ' ' in part:
                tags.append(part)
        return parts[0], tags
    
    @staticmethod
    def separate_tags(data):
        tags = []
        if 'tags' in data:
            tags = [ t.replace(' ', '-') for t in data['tags'] ]
            del data['tags']
        return tags, data
    
    @staticmethod
    def remove_unsupported_format_codes(f):
        for code in [':S', ':D']:
            f = f.replace(code, '')
        return f
    
    def expand_formats(self, formats):
        opt_sig = ';opt'
        if not isinstance(formats, list):
            formats = [formats]
        new_formats = []
        for fmt_base in formats:
            format_parts = fmt_base.split()
            optional_count = len([c for c in format_parts if c.endswith(opt_sig)])
            for n in range(2**optional_count):
                parts = []
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
            key=lambda fmt: ( len(self.get_parse_in_fmt(fmt)), len(self.get_non_param_chars(fmt)) )
        )
        return new_formats
    
    @staticmethod
    def get_parse_in_fmt(fmt):
        return fmt.split('}')
    
    @staticmethod
    def get_non_param_chars(fmt):
        parts = fmt.split('{')
        parts = [ p.split('}')[-1] for p in parts ]
        string = ''.join(parts).replace(' ', '')
        return string
    
    @staticmethod
    def is_date(str):
        for c in '.-_':
            str = str.replace(c, '')
        return str.isnumeric()
    
    @staticmethod
    def prune_data(data):
        remove_keys = [ k for k, v in data.items() if v == None ]
        for k in remove_keys:
            del data[k]
        return data

    @staticmethod
    def to_cc(str):
        if ' ' not in str:
            return str
        parts = [ p for p in str.lower().split(" ") if p != '' ]
        for i in range(len(parts)):
            part = parts[i]
            parts[i] = part[:1].upper() + part[1:]
        return ''.join(parts)
    
    @staticmethod
    def from_cc(str):
        chars = []
        for c in list(str):
            if c.isupper():
                chars.append(' ')
            chars.append(c)
        return ''.join(chars)



if __name__ == '__main__':

    formats = [
        "{sort_performer} - {studio:ns} - [{year:d;opt}] [{date_released:dt;opt}] [{line:ns;opt}] {scene_title} ({mention_performer:opt}) [{other_info:opt}]",
        "[{studio:ns}] [{year:d;opt}] [{date_released:dt;opt}] [{line:ns;opt}] {scene_title} ({sort_performer:opt}) [{other_info:opt}]",
        "{sort_performer} [{year:d;opt}] [{date_released:dt;opt}] {scene_title} [{other_info:opt}]",
        "[{jav_code:ns}]",
        "{sort_performer} - {scene_title}",
        "{scene_title}",
    ]

    parser = StringParser(formats)
