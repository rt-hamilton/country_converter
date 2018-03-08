import os
import sys
import pytest
import pandas as pd
from pandas.util.testing import assert_frame_equal
import collections
from collections import OrderedDict

TESTPATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(TESTPATH, '..'))

import country_converter as coco  # noqa
from country_converter.country_converter import _parse_arg  # noqa

regex_test_files = [nn for nn in os.listdir(TESTPATH)
                    if (nn[:10] == 'test_regex') and
                    (os.path.splitext(nn)[1] == '.txt')]
custom_data = os.path.join(TESTPATH, 'custom_data_example.txt')


@pytest.fixture(scope='module', params=regex_test_files)
def get_regex_test_data(request):
    retval = collections.namedtuple('regex_test_data',
                                    ['data_name', 'data'])
    return retval(
        request.param,
        pd.read_table(os.path.join(TESTPATH, request.param),
                      encoding='utf-8'))


def test_name_short():
    """ Tests if there is a unique matching of name_short to regular expressions
    """
    converter = coco.CountryConverter()
    not_found_id = 'XXX'
    for row in converter.data.iterrows():
        name_test = row[1].name_short
        name_result = converter.convert(
            name_test,
            src='regex',
            to='name_short',
            not_found=not_found_id,
            enforce_list=False)
        assert len(name_result) > 2, (
            'Name {} matched several regular expressions: {}'.format(
                name_test, ' ,'.join(name_result)))
        assert name_result != not_found_id, (
            'Name {} did not match any regular expression'.format(name_test))
        assert name_result == name_test, (
            'Name {} did match the wrong regular expression: {}'.format(
                name_test, name_result))


def test_name_official():
    """ Tests if there is a unique matching of name_official to regular expressions
    """
    converter = coco.CountryConverter()
    not_found_id = 'XXX'
    for row in converter.data.iterrows():
        name_test = row[1].name_official
        name_result = converter.convert(
            name_test,
            src='regex',
            to='name_official',
            not_found=not_found_id,
            enforce_list=False)
        assert len(name_result) > 2, (
            'Name {} matched several regular expressions: {}'.format(
                name_test, ' ,'.join(name_result)))
        assert name_result != not_found_id, (
            'Name {} did not match any regular expression'.format(name_test))
        assert name_result == name_test, (
            'Name {} did match the wrong regular expression: {}'.format(
                name_test, name_result))


def test_alternative_names(get_regex_test_data):
    converter = coco.CountryConverter()
    not_found_id = 'XXX'
    for row in get_regex_test_data.data.iterrows():
        name_test = row[1].name_test
        name_short = row[1].name_short
        name_result = converter.convert(
            name_test,
            src='regex',
            to='name_short',
            not_found=not_found_id,
            enforce_list=False)
        assert len(name_result) > 2, (
            'File {0} - row {1}: Name {2} matched several '
            'regular expressions: {3}'.format(
                get_regex_test_data.data_name,
                row[0],
                name_test,
                ' ,'.join(name_result)))
        if name_short != not_found_id:
            assert name_result != not_found_id, (
                'File {0} - row {1}: Name {2} did not match any '
                'regular expression'.format(
                    get_regex_test_data.data_name,
                    row[0],
                    name_test))
        assert name_result == name_short, (
                'File {0} - row {1}: Name {2} did match the '
                'wrong regular expression: {3}'.format(
                    get_regex_test_data.data_name,
                    row[0],
                    name_test,
                    name_result))


def test_additional_country_file():
    converter_basic = coco.CountryConverter()
    converter_extended = coco.CountryConverter(
        additional_data=custom_data)

    assert converter_basic.convert('Congo') == 'COG'
    assert converter_extended.convert('Congo') == 'COD'
    assert converter_extended.convert('wirtland',
                                      to='name_short') == 'Wirtland'


def test_additional_country_data():
    add_data = pd.DataFrame.from_dict({
       'name_short': ['xxx country'],
       'name_official': ['longer xxx country name'],
       'regex': ['xxx country'],
       'ISO3': ['XXX']}
    )
    converter_extended = coco.CountryConverter(
        additional_data=add_data)
    assert 'xxx country' == converter_extended.convert('XXX', src='ISO3',
                                                       to='name_short')
    assert pd.np.nan is converter_extended.convert('XXX', src='ISO3',
                                                   to='continent')


def test_UNmember():
    cc = coco.CountryConverter(only_UNmember=True)
    assert len(cc.data) == 193


def test_special_cases():
    """ Some test for special cases which occurred during development.

    These are test for specific issues turned up.
    """
    converter = coco.CountryConverter().convert

    # issue 22 - namibia iso2 na interpreted as not a number
    assert converter('NA', to='ISO3') == 'NAM'
    assert converter('NAM', to='ISO2') == 'NA'


def test_get_correspondance_dict_standard():
    """ Standard test case for get_correspondance_dict method
    """
    classA = 'EXIO1'
    classB = 'continent'
    cc = coco.CountryConverter()
    corr = cc.get_correspondance_dict(classA=classA,
                                      classB=classB)
    assert type(corr) == dict
    assert len(corr) == 44
    assert corr['DE'] == ['Europe']
    assert corr['ZA'] == ['Africa']
    assert corr['WW'] == ['Asia', 'Europe',
                          'Africa', 'Oceania',
                          'America', 'Antarctica']


def test_get_correspondance_dict_numeric_replace():
    """ Numeric replacement test of get_correspondance_dict method
    """
    classA = 'EXIO1'
    classB = 'OECD'
    cc = coco.CountryConverter()
    corr_str = cc.get_correspondance_dict(classA=classA,
                                          classB=classB,
                                          replace_numeric=True)
    assert type(corr_str) == dict
    assert len(corr_str) == 44
    assert corr_str['JP'] == ['OECD']
    assert corr_str['ZA'] == [None]
    assert None in corr_str['WW']
    assert 'OECD' in corr_str['WW']
    assert len(corr_str['WW']) == 2

    corr_num = cc.get_correspondance_dict(classA=classA,
                                          classB=classB,
                                          replace_numeric=False)
    assert type(corr_num) == dict
    assert len(corr_num) == 44
    assert corr_num['JP'] == [1964]
    assert pd.np.isnan(corr_num['ZA'])
    assert 2010 in corr_num['WW']
    assert 1961 in corr_num['WW']
    assert len(corr_num['WW']) == 4


def test_build_agg_conc_custom():
    """ Minimal test of the aggregation concordance building functionality
    """

    original_countries = ['c1', 'c2', 'c3', 'c4']
    aggregates = [{'c1': 'r1', 'c2': 'r1', 'c3': 'r2'}]

    agg_dict_wmiss = coco.agg_conc(original_countries,
                                   aggregates,
                                   merge_multiple_string=None,
                                   missing_countries=True,
                                   log_missing_countries=None,
                                   log_merge_multiple_strings=None,
                                   as_dataframe=False
                                   )

    assert agg_dict_wmiss == OrderedDict([('c1', 'r1'),
                                          ('c2', 'r1'),
                                          ('c3', 'r2'),
                                          ('c4', 'c4')])

    agg_dict_replace = coco.agg_conc(original_countries,
                                     aggregates,
                                     merge_multiple_string=None,
                                     missing_countries='RoW',
                                     log_missing_countries=None,
                                     log_merge_multiple_strings=None,
                                     as_dataframe=False
                                     )

    assert agg_dict_replace == OrderedDict([('c1', 'r1'),
                                            ('c2', 'r1'),
                                            ('c3', 'r2'),
                                            ('c4', 'RoW')])

    agg_vec_womiss = coco.agg_conc(original_countries,
                                   aggregates,
                                   merge_multiple_string=None,
                                   missing_countries=False,
                                   log_missing_countries=None,
                                   log_merge_multiple_strings=None,
                                   as_dataframe='sparse'
                                   )

    expected_vec = pd.DataFrame(data=[['c1', 'r1'],
                                      ['c2', 'r1'],
                                      ['c3', 'r2'],
                                      ],
                                columns=['original', 'aggregated']
                                )

    assert_frame_equal(agg_vec_womiss, expected_vec)

    agg_matrix_womiss = coco.agg_conc(original_countries,
                                      aggregates,
                                      merge_multiple_string=None,
                                      missing_countries=False,
                                      log_missing_countries=None,
                                      log_merge_multiple_strings=None,
                                      as_dataframe='full'
                                      )

    expected_matrix = pd.DataFrame(data=[[1.0, 0.0],
                                         [1.0, 0.0],
                                         [0.0, 1.0],
                                         ],
                                   columns=['r1', 'r2'],
                                   index=['c1', 'c2', 'c3'],
                                   )
    expected_matrix.index.names = ['original']
    expected_matrix.columns.names = ['aggregated']

    assert_frame_equal(agg_matrix_womiss, expected_matrix)


def test_build_agg_conc_exio():
    """ Some agg_conc test with a subset of exio countries
    """

    original_countries = ['TW', 'XX', 'AT', 'US', 'WA']
    aggregates = [
        'EU', 'OECD', 'continent'
    ]

    agg_dict_replace = coco.agg_conc(original_countries,
                                     aggregates,
                                     merge_multiple_string=False,
                                     missing_countries='RoW',
                                     log_missing_countries=None,
                                     log_merge_multiple_strings=None,
                                     as_dataframe=False
                                     )

    assert agg_dict_replace == OrderedDict([('TW', 'Asia'),
                                            ('XX', 'RoW'),
                                            ('AT', 'EU'),
                                            ('US', 'OECD'),
                                            ('WA', 'RoW')])

    agg_dict_skip = coco.agg_conc(original_countries,
                                  aggregates,
                                  merge_multiple_string=False,
                                  missing_countries=False,
                                  log_missing_countries=None,
                                  log_merge_multiple_strings=None,
                                  as_dataframe=False
                                  )

    assert agg_dict_skip == OrderedDict([('TW', 'Asia'),
                                         ('AT', 'EU'),
                                         ('US', 'OECD')])

    agg_matrix_skip = coco.agg_conc(original_countries,
                                    aggregates,
                                    merge_multiple_string=False,
                                    missing_countries=False,
                                    log_missing_countries=None,
                                    log_merge_multiple_strings=None,
                                    as_dataframe='full'
                                    )

    assert agg_matrix_skip.index.tolist() == ['TW', 'AT', 'US']

    aggregates_oecd_first = [
        'OECD', 'EU', {'WA': 'RoW', 'WF': 'RoW'}
    ]

    agg_dict_oecd_eu = coco.agg_conc(original_countries,
                                     aggregates_oecd_first,
                                     merge_multiple_string=False,
                                     missing_countries=True,
                                     log_missing_countries=None,
                                     log_merge_multiple_strings=None,
                                     as_dataframe=False
                                     )

    assert agg_dict_oecd_eu == OrderedDict([('TW', 'TW'),
                                            ('XX', 'XX'),
                                            ('AT', 'OECD'),
                                            ('US', 'OECD'),
                                            ('WA', 'RoW')])

    aggregates = 'EU'
    agg_dict_full_exio = coco.agg_conc('EXIO2',
                                       aggregates,
                                       merge_multiple_string=False,
                                       missing_countries='RoW',
                                       log_missing_countries=None,
                                       log_merge_multiple_strings=None,
                                       as_dataframe=False
                                       )

    assert len(agg_dict_full_exio) == 48
    assert agg_dict_full_exio['US'] == 'RoW'
    assert agg_dict_full_exio['AT'] == 'EU'


def test_match():
    match_these = ['norway', 'united_states', 'china', 'taiwan']
    master_list = ['USA', 'The Swedish Kingdom', 'Norway is a Kingdom too',
                   'Peoples Republic of China', 'Republic of China']
    matching_dict = coco.match(match_these, master_list)
    assert matching_dict['china'] == 'Peoples Republic of China'
    assert matching_dict['taiwan'] == 'Republic of China'
    assert matching_dict['norway'] == 'Norway is a Kingdom too'
    match_string_from = 'united states'
    match_string_to_correct = 'USA'
    matching_dict = coco.match(match_string_from, match_string_to_correct)
    assert matching_dict['united states'] == 'USA'
    match_from = ('united states')
    match_false = ('abc')
    matching_dict = coco.match(match_from, match_false)
    assert matching_dict['united states'] == 'not_found'
    matching_dict = coco.match(match_false, match_false)
    assert matching_dict['abc'] == 'not_found'


def test_wrapper_convert():
    assert 'US' == coco.convert('usa', src='regex', to='ISO2')
    assert 'AT' == coco.convert('40', to='ISO2')


def test_convert_wrong_classification():
    with pytest.raises(KeyError) as e:
        coco.convert('usa', src='abc')


def test_EU_output():
    cc = coco.CountryConverter()
    EU28 = cc.EU28as('ISO2')
    assert len(EU28 == 28)
    assert cc.convert('Croatia', to='ISO2') in EU28.ISO2.values
    EU27 = cc.EU27as('ISO2')
    assert len(EU27 == 27)
    assert cc.convert('Croatia', to='ISO2') not in EU27.ISO2.values


def test_OECD_output():
    cc = coco.CountryConverter()
    oecd = cc.OECDas('ISO3')
    assert cc.convert('Netherlands', to='ISO3') in oecd.values


def test_UN_output():
    cc = coco.CountryConverter()
    un = coco.CountryConverter().UNas('ISO3')
    assert cc.convert('Netherlands', to='ISO3') in un.values


def test_properties():
    cc = coco.CountryConverter()
    assert all(cc.EU28 == cc.EU28as(to='name_short'))
    assert all(cc.EU27 == cc.EU27as(to='name_short'))
    assert all(cc.OECD == cc.OECDas(to='name_short'))
    assert all(cc.UN == cc.UNas(to='name_short'))


def test_parser():
    sys.argv = ['AT']
    args = _parse_arg(coco.CountryConverter().valid_class)
    assert args.src == None  # noqa
    assert args.to == 'ISO3'
