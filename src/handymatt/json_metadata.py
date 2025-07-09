import os
import json
import yaml



def save_metadata(data: dict, id_: str, path: str, in_metadata_folder=True, quiet=True):
    """ saves data (dict) to .json file close to path """
    if in_metadata_folder:
        path = path + os.sep + '.metadata'
    json_path = path + os.sep + f'{id_}.json'
    os.makedirs(os.path.dirname(json_path), exist_ok=True)
    if not quiet:
        print(f'saving metadata to "{json_path}"')
    with open(json_path, 'w') as f:
        json.dump(data, f, indent=4)


def get_metadata(id_: str, path: str, only_use_id=False) -> dict:
    """ Find's metadata saved in .json/.yaml files near path using file id_  """
    
    if os.path.isfile(path):
        path = os.path.dirname(path)
    
    endpaths = [ f'{id_}.json', 'metadata.json' ]
    if only_use_id:
        endpaths.remove('metadata.json')
    endpaths.extend([ fn.replace('.json', '.yaml') for fn in endpaths ])
    endpaths.extend([ os.path.join('.metadata', fn) for fn in endpaths ])
    
    data = {}
    basepath = path
    while not os.path.ismount(basepath):
        for endpath in endpaths:
            metadata_path = basepath + os.sep + endpath
            if os.path.exists(metadata_path) and os.path.isfile(metadata_path):
                newdata = {}
                if metadata_path.endswith('.json'):
                    newdata = _read_json(metadata_path)
                elif metadata_path.endswith('.yaml'):
                    newdata = _read_yaml(metadata_path)
                data = _merge_dicts(data, newdata)
        basepath = os.path.dirname(basepath)
        
    return data



#region - HELPERS -----------

def _read_json(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        data_json = json.load(f)
    return data_json

def _read_yaml(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        data_yaml = yaml.safe_load(f)
    return data_yaml

def _merge_dicts(d1: dict, d2: dict) -> dict:
    """  """
    result = dict(d1)  # start with d1
    for k, v2 in d2.items():
        if k not in result:
            result[k] = v2  # new key from d2
        else:
            v1 = result[k]
            if isinstance(v1, dict) and isinstance(v2, dict):
                result[k] = _merge_dicts(v1, v2)
            elif isinstance(v1, list) and isinstance(v2, list):
                result[k] = v1 + v2
            elif type(v1) == type(v2):
                result[k] = v1  # same type, not mergable → d1 wins
            else:
                result[k] = v1  # type mismatch → d1 wins
            
    return result
