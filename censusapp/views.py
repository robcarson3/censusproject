from django.http import HttpResponse, JsonResponse, Http404
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import authenticate, login, logout
from django.db.models import Q, Count
from django.utils.http import url_has_allowed_host_and_scheme
from django.shortcuts import render
from django.views.decorators.http import require_GET
from . import models
from .utils import (
    convert_year_range, 
    title_sort_key, issue_sort_key, copy_sort_key, search_sort_copy_id, 
    search_sort_date, search_sort_title, search_sort_location, search_sort_stc, 
    verified_query, unverified_query, canonical_query, 
    get_display_field, get_collection,
)
from datetime import datetime
from collections import Counter
import csv

# --- Main Pages ---

def homepage(request):
    gridwidth = 5
    titles = models.Title.objects.all()
    titles = sorted(titles, key=title_sort_key)
    titlerows = [titles[i: i + gridwidth]
                 for i in range(0, len(titles), gridwidth)]
    context = {
        'frontpage': True,
        'titlerows': titlerows,
        'icon_path': 'census/images/plus-sign.png'
    }
    return render(request, 'census/frontpage.html', context)

def issue_list(request, id):
    selected_title = get_object_or_404(models.Title, pk=id)
    editions = list(selected_title.editions.order_by('edition_number'))
    issues_qs = (
        models.Issue.objects
        .filter(edition__in=editions)
        .select_related("edition")
        .order_by("edition__edition_number", "unknown_issue", "issue_number")
    )
    issues = list(issues_qs)
    counts = Counter(i.edition_id for i in issues)
    for i in issues:
        i.edition._issue_count = counts[i.edition_id]   
    copy_count = models.Copy.objects.filter(canonical_query, issue__in=issues).count()
    context = {
        'title': selected_title,
        'editions': editions,
        'issues': issues,
        'copy_count': copy_count,
        'icon_path': 'census/images/plus-sign.png',
    }
    return render(request, 'census/issue-list.html', context)

def copy_list(request, id):
    selected_issue = get_object_or_404(models.Issue, pk=id)
    copies = models.Copy.objects.filter(canonical_query, issue=selected_issue)
    copies = sorted(copies, key=copy_sort_key)
    context = {
        'title': selected_issue.edition.title,
        'selected_issue': selected_issue,
        'copies': copies,
        'copy_count': len(copies),
        'icon_path': 'census/images/plus-sign.png',
    }
    return render(request, 'census/copy-list.html', context)

def single_copy(request, census_id):
    selected_copy = get_object_or_404(models.Copy, census_id=census_id)
    copies = [selected_copy]
    selected_issue = selected_copy.issue
    context = {
        'title': selected_issue.edition.title,
        'selected_issue': selected_issue,
        'copies': copies,
        'copy_count': 1,
        'icon_path': 'census/images/plus-sign.png',  
        'open_modal_id': selected_copy.pk, 
    }
    return render(request, 'census/copy-list.html', context)

def copy_data(request, pk):
    selected_copy = get_object_or_404(models.Copy, pk=pk)
    context = {"copy": selected_copy}
    return render(request, 'census/copy-modal.html', context)


# --- Authentication ---

def login_user(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        next_url = request.POST.get('next') or '/admin/'

        if not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
            next_url = '/admin/'

        user_account = authenticate(username=username, password=password)
        if user_account is not None:
            login(request, user_account)
            return redirect(next_url)
        else:
            return render(request, 'census/login.html', {'failed': True, 'next': next_url})

    next_url = request.GET.get('next') or '/admin/'
    if not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        next_url = '/admin/'

    return render(request, 'census/login.html', {'next': next_url})

def logout_user(request):
    logout(request)
    return render(request, 'census/logout.html')


# --- Search ---

def search(request, field=None, value=None, order=None):
    field = field or request.GET.get('field')
    value = value or request.GET.get('value')
    order = order or request.GET.get('order')
    initial_field = request.GET.get('initial_field')
    initial_value = request.GET.get('initial_value')
    initial_ids = request.GET.getlist('initial_ids')

    canonical_copies = models.Copy.objects.filter(canonical_query)

    if initial_ids:
        canonical_copies = canonical_copies.filter(pk__in=initial_ids)

    if not field and value:
        field = 'keyword'

    display_field = get_display_field(field)
    display_value = value

    if field == 'keyword':
        query = (
            Q(binding__icontains=value) |
            Q(sammelband_notes__icontains=value) |
            Q(marginalia__icontains=value) |
            Q(local_notes__icontains=value) |
            Q(provenance_notes__icontains=value) |
            Q(provenance_names__name__icontains=value) |
            Q(bibliography__icontains=value)
        )
        result_list = canonical_copies.filter(query)

    elif field == 'location' and value:
        result_list = canonical_copies.filter(location__name__icontains=value)

    elif field == 'geography' and value:
        result_list = canonical_copies.filter(
            Q(location__city__icontains=value) |
            Q(location__state__icontains=value) |
            Q(location__country__icontains=value) |
            Q(location__continent__icontains=value)
        )

    elif field == 'provenance_name' and value:
        result_list = canonical_copies.filter(provenance_names__name__icontains=value)

    elif field == 'collection':
        result_list, display_field = get_collection(canonical_copies, value)
        display_value = 'All'

    elif field == 'year' and value:
        year_range = convert_year_range(value)
        if year_range:
            start, end = year_range
            result_list = canonical_copies.filter(issue__start_date__lte=end, issue__end_date__gte=start)
        else:
            result_list = canonical_copies.filter(issue__year__icontains=value)

    elif field == 'stc' and value:
        result_list = canonical_copies.filter(issue__stc_wing__icontains=value)

    elif field == 'census_id' and value:
        result_list = canonical_copies.filter(census_id=value)

    else:
        result_list = models.Copy.objects.none()

    result_list = result_list.distinct()
    initial_display_field = get_display_field(initial_field)

    if not order:
        order = 'date'

    if order == 'date':
        result_list = sorted(result_list, key=search_sort_date)
    elif order == 'title':
        result_list = sorted(result_list, key=search_sort_title)
    elif order == 'location':
        result_list = sorted(result_list, key=search_sort_location)
    elif order == 'stc':
        result_list = sorted(result_list, key=search_sort_stc)
    elif order == 'census_id':
        result_list = sorted(result_list, key=search_sort_copy_id)

    current_ids = [copy.pk for copy in result_list]

    icon_path = 'census/images/ghost.png' if field == 'collection' and value == 'ghost' else 'census/images/question-mark.png'

    context = {
        'field': field,
        'value': value,
        'initial_field': initial_field,
        'initial_value': initial_value,
        'display_field': display_field,
        'display_value': display_value,
        'initial_display_field': initial_display_field,
        'result_list': result_list,
        'copy_count': len(result_list),
        'initial_ids': current_ids,
        'icon_path': icon_path,
        'order': order,
    }

    return render(request, 'census/search-results.html', context)


# --- Autofill ---

@require_GET
def autofill_location(request, query=None):
    matches = []
    if query:
        matches = models.Location.objects.filter(name__icontains=query).values_list('name', flat=True)
    return JsonResponse({'matches': list(matches)})

@require_GET
def autofill_geography(request, query=None):
    if not query:
        return JsonResponse({'matches': []})
    
    fields = ['city', 'state', 'country', 'continent']
    matches = set()

    for field in fields:
        values = models.Location.objects.filter(**{f'{field}__icontains': query}).values_list(field, flat=True)
        matches.update(values)
    
    filtered_matches = sorted({m.strip() for m in matches if m and m.strip()})
    return JsonResponse({'matches': filtered_matches})

@require_GET
def autofill_provenance(request, query=None):
    matches = []
    if query:
        matches = models.ProvenanceName.objects.filter(name__icontains=query).values_list('name', flat=True)
    return JsonResponse({'matches': list(matches)})

@require_GET
def autofill_collection(request, query=None):
    collections = [
        {'label': 'With known early provenance (before 1700)', 'value': 'earlyprovenance'},
        {'label': 'With a known woman owner', 'value': 'womanowner'},
        {'label': 'With a known woman owner before 1800', 'value': 'earlywomanowner'},
        {'label': 'Includes marginalia', 'value': 'marginalia'},
        {'label': 'In an early sammelband', 'value': 'earlysammelband'},
        {'label': 'Unverified copies', 'value': 'unverified'},
        {'label': 'Ghost copies', 'value': 'ghost'},
    ]
    return JsonResponse({'matches': collections})


# --- Static Pages ---

def info(request, viewname):
    DISPLAY_NAMES = {
    'about': 'About',
    'advisoryboard': 'Advisory Board',
    'references': 'References',
}
    current_date = datetime.now().strftime('%d %B %Y')
    canonical_count = models.Copy.objects.filter(canonical_query).count()
    copy_count = models.Copy.objects.filter(canonical_query & Q(fragment=False)).count()
    fragment_copy_count = models.Copy.objects.filter(canonical_query & Q(fragment=True)).count()
    verified_copy_count = models.Copy.objects.filter(verified_query).count()
    unverified_copy_count = models.Copy.objects.filter(unverified_query).count()
    estc_copy_count = models.Copy.objects.filter(canonical_query, from_estc=True).count()
    non_estc_copy_count = models.Copy.objects.filter(canonical_query, from_estc=False).count()
    facsimile_copy_count = models.Copy.objects.filter(canonical_query).exclude(Q(digital_facsimile_url__isnull=True) | Q(digital_facsimile_url='')).count()
    facsimile_copy_percent = round(
        100 * facsimile_copy_count / canonical_count
    ) if canonical_count else 0
    context = {
        'page_name': DISPLAY_NAMES.get(viewname, viewname.title()),
        'current_date': current_date,
        'canonical_count': canonical_count,
        'copy_count': copy_count,
        'verified_copy_count': verified_copy_count,
        'unverified_copy_count': unverified_copy_count,
        'fragment_copy_count': fragment_copy_count,
        'estc_copy_count': estc_copy_count,
        'non_estc_copy_count': non_estc_copy_count,
        'facsimile_copy_count': facsimile_copy_count,
        'facsimile_copy_percent': f'{facsimile_copy_percent}%',
    }

    try:
        page = models.StaticPageText.objects.get(viewname=viewname)
    except models.StaticPageText.DoesNotExist:
        raise Http404("Page not found")

    raw = page.content or ''
    try:
        formatted_content = raw.format(**context)
    except Exception:
        formatted_content = raw  # fall back if placeholders don't match

    context = {'content': [formatted_content], **context}
    return render(request, 'census/info.html', context)
    
    
# --- CSV Exports ---

def location_copy_count_csv_export(request):
    locations = models.Copy.objects.filter(canonical_query).values('location')
    locations = locations.annotate(total=Count('location')).order_by('location__name')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="location_copy_count.csv"'

    writer = csv.writer(response)
    writer.writerow(['Location', 'Number of Copies'])

    for loc in locations:
        writer.writerow([models.Location.objects.get(pk=loc['location']).name, loc['total']])

    return response

def title_copy_count_csv_export(request):
    titles = models.Copy.objects.filter(canonical_query).values('issue__edition__title')
    titles = titles.annotate(total=Count('id'))

    title_map = {
        t.id: t for t in models.Title.objects.filter(
            id__in=[e['issue__edition__title'] for e in titles]
        )
    }
    for e in titles:
        e['title_obj'] = title_map[e['issue__edition__title']]
    titles = sorted(titles, key=lambda e: title_sort_key(e['title_obj']))

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="title_copy_count.csv"'

    writer = csv.writer(response)
    writer.writerow(['Title', 'Number of Copies'])

    for entry in titles:
        title = entry['title_obj']
        writer.writerow([title.title, entry['total']])

    return response

def edition_copy_count_csv_export(request):
    editions = models.Copy.objects.filter(canonical_query).values('issue__edition')
    editions = editions.annotate(total=Count('id'))

    edition_map = {
        ed.id: ed for ed in models.Edition.objects.select_related('title').filter(
            id__in=[e['issue__edition'] for e in editions]
        )
    }
    for e in editions:
        e['edition'] = edition_map[e['issue__edition']]
    def edition_sort_key(e):
        ed = e['edition']
        try:
            num = int(ed.edition_number)
        except (ValueError, TypeError):
            num = float('inf')
        return (ed.title.title.lower(), num)

    editions = sorted(editions, key=edition_sort_key)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="edition_copy_count.csv"'

    writer = csv.writer(response)
    writer.writerow(['Edition', 'Number of Copies'])

    for entry in editions:
        ed = entry['edition']
        writer.writerow([f"{ed.title.title} Edition {ed.edition_number}", entry['total']])

    return response

def issue_copy_count_csv_export(request):
    issues = models.Copy.objects.filter(canonical_query).values('issue')
    issues = issues.annotate(total=Count('id')).order_by('issue__edition__title__title', 'issue__estc')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="issue_copy_count.csv"'

    writer = csv.writer(response)
    writer.writerow(['Issue (Title + ESTC)', 'Number of Copies'])

    for entry in issues:
        issue = models.Issue.objects.get(pk=entry['issue'])
        writer.writerow([f"{issue.edition.title.title} (ESTC {issue.estc})", entry['total']])

    return response

def provenance_name_copy_count_csv_export(request):
    ownerships = models.ProvenanceOwnership.objects.filter(
        copy__in=models.Copy.objects.filter(canonical_query)
    ).values('owner').annotate(total=Count('copy')).order_by('owner__name')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="provenance_name_copy_count.csv"'

    writer = csv.writer(response)
    writer.writerow(['Provenance Name', 'Bio', 'VIAF', 'Gender', 'Start Century', 'End Century', 'Number of Copies'])

    for entry in ownerships:
        owner = models.ProvenanceName.objects.get(pk=entry['owner'])
        writer.writerow([owner.name, owner.bio, owner.viaf, owner.gender, owner.start_century, owner.end_century, entry['total']])

    return response
