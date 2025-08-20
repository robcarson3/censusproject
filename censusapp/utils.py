from django.db.models import Q
from django.conf import settings
import re
from . import models


# --- String Cleaning ---

def strip_article(s): 
    if not s:
        return ''
    articles = ['a', 'an', 'the']
    lower_s = s.lower()
    for article in articles:
        prefix = article + ' '
        if lower_s.startswith(prefix):
            return s[len(prefix):]
    return s
# This function removes leading articles for correct alphabetization

def convert_year_range(year):
    if '-' in year:
        start, end = [n.strip() for n in year.split('-', 1)]
        if len(start) == 4 and start.isdigit() and len(end) == 4 and end.isdigit():
            return int(start), int(end)
    elif len(year) == 4 and year.isdigit():
        return int(year), int(year)
    return False
# This function allows years and year ranges to be sorted in the correct order

def split_record(field_value):
    if not field_value:
        return []
    return [part.strip() for part in str(field_value).split(';') if part.strip()]
# This function allows for certain records to be split into two results by means of a semicolon

def format_issue_label(issue) -> str:
    edition_number = getattr(issue.edition, "edition_number", None) or str(issue.edition.pk)
    total = getattr(issue.edition, "_issue_count", None)
    if total is None:
        total = issue.edition.issues.count()
    if total <= 1:
        return f"{edition_number}"
    if issue.issue_number is not None:
        return f"{edition_number}.{issue.issue_number}"
    return f"{edition_number}.x"
# This function generates a label for each issue (either the edition number, or edition.issue, or edition.x).


# --- Sorting functions for Titles and Issues ---

def title_sort_key(title_object):
    title = title_object.title

    if title and title[0].isdigit():
        title = title.split()
        return strip_article(' '.join(title[1:] + [title[0]]))
    else:
        return strip_article(title)

def issue_sort_key(issue):
    try:
        ed_number = int(issue.edition.edition_number)
    except (TypeError, ValueError):
        ed_number = float('inf')
    unknown_sort = 1 if getattr(issue, "unknown_issue", False) else 0
    num_sort = issue.issue_number if issue.issue_number is not None else 10**9
    return (ed_number, unknown_sort, num_sort)


# --- Sorting Functions for Copies ---

def copy_location_sort_key(copy):
    name = copy.location.name if copy.location else ''
    return strip_article(name)

def copy_shelfmark_sort_key(copy):
    return copy.shelfmark or ''

def copy_census_id_sort_key(copy):
    census_id = copy.census_id or ''
    try:    
        if '.' in census_id:
            census_id_a, census_id_b = map(int, census_id.split('.'))
        else:
            census_id_a = int(census_id)
            census_id_b = 0
    except (ValueError, TypeError):
        census_id_a, census_id_b = 0, 0
    return (census_id_a, census_id_b)

def copy_sort_key(copy):
    census_id_a, census_id_b = copy_census_id_sort_key(copy)
    return (copy_location_sort_key(copy),
            copy_shelfmark_sort_key(copy),
            census_id_a,
            census_id_b)


# --- Sorting Functions for Search Results ---

def search_sort_copy_id(copy):
    s = (copy.census_id or "").strip()
    if not s:
        return (2, "", "")  

    if re.fullmatch(r"\d+(?:\.\d+)?", s):
        return (0, float(s), s)  

    return (1, s.lower(), s)

def copy_date_sort_key(copy):
    v = getattr(copy.issue, 'start_date', 0) or 0
    try:
        return int(v)
    except (TypeError, ValueError):
        return 0

def search_sort_date(copy):
    return (copy_date_sort_key(copy),
            title_sort_key(copy.issue.edition.title),
            copy_location_sort_key(copy))

def search_sort_title(copy):
    return (title_sort_key(copy.issue.edition.title),
            copy_date_sort_key(copy),
            copy_location_sort_key(copy))

def search_sort_location(copy):
    return (copy_location_sort_key(copy),
            copy_date_sort_key(copy),
            title_sort_key(copy.issue.edition.title))

def search_sort_stc(copy):
    stc = (copy.issue.stc_wing or '')
    return (stc, copy_location_sort_key(copy))


# --- Verification Queries ---

verified_query = Q(verification='V')
unverified_query = Q(verification='U')
false_query = Q(verification='F')
canonical_query = (Q(verification='V') |
                    Q(verification='U'))


# --- Search options ---

SEARCH_DISPLAY_NAMES = {
    'keyword': 'Keyword Search',
    'location': 'Location',
    'geography': 'Geography',
    'provenance_name': 'Provenance Name',
    'collection': 'Specific Features',
    'year': 'Year',
    'stc': 'STC / Wing',
}

def get_display_field(field_name):
    if field_name == 'census_id':
        return f"{getattr(settings, 'COPY_ID_PREFIX', 'ID')}\u202f#"
    return SEARCH_DISPLAY_NAMES.get(field_name, field_name)


# --- Specific Features options ---

def get_collection(copy_list, collection_name):
    if collection_name == 'ghost':
        return models.Copy.objects.filter(false_query), 'Ghost copies'
    
    feature_map = {
        'earlyprovenance': {
            'filter': copy_list.filter(provenance_names__start_century='17'),
            'display': 'Copies with known early provenance (before 1700)'
        },
        'womanowner': {
            'filter': copy_list.filter(provenance_names__gender='F'),
            'display': 'Copies with a known woman owner'
        },
        'earlywomanowner': {
            'filter': copy_list.filter(Q(provenance_names__gender='F') &
                                       (Q(provenance_names__start_century='17') |
                                        Q(provenance_names__start_century='18'))),
            'display': 'Copies with a known woman owner before 1800'
        },
        'marginalia': {
            'filter': copy_list.exclude(Q(marginalia='') | Q(marginalia=None)),
            'display': 'Copies that include marginalia'
        },
        'earlysammelband': {
            'filter': copy_list.filter(in_early_sammelband=True),
            'display': 'Copies in an early sammelband'
        },
        'unverified': {
            'filter': copy_list.filter(unverified_query),
            'display': 'Unverified copies'
        },
        'ghost': {
            'filter': models.Copy.objects.filter(false_query),
            'display': 'Ghost copies'
        }
    }

    feature = feature_map.get(collection_name)
    if feature:
        return feature['filter'], feature['display']
    else:
        return copy_list.none(), 'Specific Features'
    

# --- Context Processor for Census Globals ---
def census_globals(request):
    return {
        'CENSUS_NAME': getattr(settings, 'CENSUS_NAME', 'Census Project'),
        'COPY_ID_PREFIX': getattr(settings, 'COPY_ID_PREFIX', 'ID'),
        'CENSUS_EMAIL': getattr(settings, 'CENSUS_EMAIL', 'default@example.com'),
    }