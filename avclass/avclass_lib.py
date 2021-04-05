#!/usr/bin/env python
'''
AVClass as a lib
'''
import os
import sys
from collections import namedtuple
path = os.path.dirname(os.path.abspath(__file__))
libpath = os.path.join(path, 'lib/')
sys.path.insert(0, libpath)
from avclass_common import AvLabels  # noqa: E402
import json  # noqa: E402

# Default alias file
default_alias_file = os.path.join(path, "data/default.aliases")
# Default generic tokens file
default_gen_file = os.path.join(path, "data/default.generics")

# Return messages
NO_LABELS_MSG = 'No AV labels in VT reports.'
PARSER_ERROR_MSG = 'Cannot parse VT report.'
SUCCESS_MSG = 'Successfully extracted family labels.'
SUCCESS = 'OK'
FAILURE = 'ERROR'


AVCInfo = namedtuple('ReturnInfo',
                     ['md5', 'sha1', 'sha256', 'family', 'is_pup',
                      'all_families', 'msg', 'verbose_msg'])


def extract_avclass_labels(vt_rep, hash_type, vtapi, av_file=None):
    '''
    Given a VT report it returns the AVClass labels
    '''
    # Create AvLabels object
    av_labels = AvLabels(default_gen_file, default_alias_file, av_file)

    if vtapi == 'v3':
        get_sample_info = av_labels.get_sample_info_vt_v3
    elif vtapi == 'v2':
        get_sample_info = av_labels.get_sample_info_vt_v2
    sample_info = get_sample_info(vt_rep)
    if sample_info is None:
        return AVCInfo(None, None, None, None, None, None,
                       FAILURE, PARSER_ERROR_MSG)

    # Sample's name is selected hash type (md5 by default)
    name = getattr(sample_info, hash_type)

    # If the VT report has no AV labels, continue
    if not sample_info.labels:
        return AVCInfo(sample_info.md5, sample_info.sha1,
                       sample_info.sha256, None, None, None,
                       FAILURE, NO_LABELS_MSG)

    # Get distinct tokens from AV labels
    tokens = list(av_labels.get_family_ranking(sample_info).items())

    # Top candidate is most likely family name
    if tokens:
        family = tokens[0][0]
    else:
        family = "SINGLETON:" + name

    # Check if sample is PUP, if requested
    is_pup = av_labels.is_pup(sample_info[3])
    return AVCInfo(sample_info.md5, sample_info.sha1,
                   sample_info.sha256, family, is_pup, tokens,
                   SUCCESS, SUCCESS_MSG)


if __name__ == '__main__':
    """Example that tests the AVClass extraction"""
    test_file_v2 = '../examples/vtv2_sample.json'
    # my_test_file_v3 = '../examples/vtv3_sample_mine.json'
    test_file_v3 = '../examples/vtv3_sample.json'

    print('Testing VT API2 Jsons:')
    with open(test_file_v2, 'r') as fr:
        for pos, line in enumerate(fr):
            # if pos and pos % 50 == 0:
            #     break
            rep = json.loads(line.strip('\n'))
            avc_res = extract_avclass_labels(rep, 'sha256', 'v2')
            print(avc_res)

    print('\n\nTesting VT API3 Jsons:')
    with open(test_file_v3, 'r') as fr:
        for pos, line in enumerate(fr):
            # if pos and pos % 50 == 0:
            #     break
            rep = json.loads(line.strip('\n'))
            avc_res = extract_avclass_labels(rep, 'sha256', 'v3')
            print(avc_res)
