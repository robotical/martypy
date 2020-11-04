

class ClientGeneric():

    SIDE_CODES = {
        'left'    : 1,
        'right'   : 0,
        'forward' : 3,
        'back'    : 2,
        'auto'    : 0,
    }

    EYE_POSES = {
        'angry'   : 'eyesAngry',
        'excited' : 'eyesExcited',
        'normal'  : 'eyesNormal',
        'wide'    : 'eyesWide',
        'wiggle'  : 'wiggleEyes'
    }

    NOT_IMPLEMENTED = "Unfortunately this Marty doesn't do that"

    @classmethod
    def dict_merge(cls, *dicts):
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
