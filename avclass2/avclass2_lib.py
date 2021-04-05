#!/usr/bin/env python
'''
AVClass as a lib
'''
import os
import sys
from collections import namedtuple
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(1, os.path.join(script_dir, 'lib/'))
sys.path.insert(1, os.path.join(script_dir, '../shared/'))
from avclass2_common import AvLabels  # noqa: E402
import json  # noqa: E402

# Default tagging file
default_tag_file = os.path.join(script_dir, "data/default.tagging")
# Default expansion file
default_exp_file = os.path.join(script_dir, "data/default.expansion")
# Default taxonomy file
default_tax_file = os.path.join(script_dir, "data/default.taxonomy")

# Return messages
NO_LABELS_MSG = 'No AV labels in VT reports.'
PARSER_ERROR_MSG = 'Cannot parse VT report.'
SUCCESS_MSG = 'Successfully extracted family labels.'
SUCCESS = 'OK'
FAILURE = 'ERROR'


AVCInfo = namedtuple('ReturnInfo',
                     ['md5', 'sha1', 'sha256',
                      'vt_count', 'first_seen', 'scan_date',
                      'family', 'is_pup', 'tags',
                      'msg', 'verbose_msg'])


def format_tag_pairs(tags, taxonomy=None):
    ''' Return ranked tags as string '''
    if not tags:
        return ""
    if taxonomy is not None:
        p = taxonomy.get_path(tags[0][0])
    else:
        p = tags[0][0]
    out = "%s|%d" % (p, tags[0][1])
    for (t, s) in tags[1:]:
        if taxonomy is not None:
            p = taxonomy.get_path(t)
        else:
            p = t
        out += ",%s|%d" % (p, s)
    return out


def extract_avclass_labels(vt_rep, vtapi, av_file=None):
    '''
    Given a VT report it returns the AVClass labels
    '''
    # Create AvLabels object
    av_labels = AvLabels(default_tag_file, default_exp_file, default_tax_file,
                         av_file, False)

    if vtapi == 'v3':
        get_sample_info = av_labels.get_sample_info_vt_v3
    elif vtapi == 'v2':
        get_sample_info = av_labels.get_sample_info_vt_v2
    sample_info = get_sample_info(vt_rep)

    if sample_info is None:
        return AVCInfo(None, None, None, None, None, None,
                       FAILURE, PARSER_ERROR_MSG)

    # If the VT report has no AV labels, continue
    if not sample_info.labels:
        return AVCInfo(sample_info.md5, sample_info.sha1, sample_info.sha256,
                       None, sample_info.first_seen, sample_info.scan_date,
                       None, None, None,
                       FAILURE, NO_LABELS_MSG)

    # Compute VT_Count
    vt_count = len(sample_info.labels)

    # Get the distinct tokens from all the av labels in the report
    av_tmp = av_labels.get_sample_tags(sample_info)
    tags = av_labels.rank_tags(av_tmp)
    tags_str = format_tag_pairs(tags, av_labels.taxonomy)

    # Check if samples is PUP
    is_pup = False
    if av_labels.is_pup(tags, av_labels.taxonomy):
        is_pup = True

    # Get most probable family name
    family = 'singleton'
    for (t, s) in tags:
        cat = av_labels.taxonomy.get_category(t)
        if (cat == "UNK") or (cat == "FAM"):
            family = t
            break

    return AVCInfo(sample_info.md5, sample_info.sha1, sample_info.sha256,
                   vt_count, sample_info.first_seen, sample_info.scan_date,
                   family, is_pup, tags_str,
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
            avc_res = extract_avclass_labels(rep, 'v2')
            print(avc_res)

    print('\n\nTesting VT API3 Jsons:')
    with open(test_file_v3, 'r') as fr:
        for pos, line in enumerate(fr):
            # if pos and pos % 50 == 0:
            #     break
            rep = json.loads(line.strip('\n'))
            avc_res = extract_avclass_labels(rep, 'v3')
            print(avc_res)
