    
def dict_merge(*dicts):
    '''
    Merge all provided dicts into one dict
    '''
    merged = {}
    for d in dicts:
        if not isinstance(d, dict):
            raise ValueError('Value should be a dict')
        else:
            merged.update(d)
    return merged

