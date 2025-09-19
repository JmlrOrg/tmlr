import os
import re
import pdb
import requests
import unidecode
from collections import defaultdict
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, select_autoescape

import openreview
from openreview import tools


YEAR = datetime.today().year

os.makedirs("output/papers/bib/", exist_ok=True)

client = openreview.api.OpenReviewClient(
    baseurl='https://api2.openreview.net',
    username=os.environ['OR_USER'],
    password=os.environ['OR_PASS']
)

def render_webpage(env, page, base_url, template_kw={}):
    with open(os.path.join("output", page), "w") as f:
        template = env.get_template(page)
        out = template.render(
            **template_kw,
            year=YEAR,
            base_url=base_url,
            home_active=(page == "index.html"),
            editorial_board_active=(page == "editorial-board.html"),
            stats_active=(page == "stats.html")
        )
        f.write(out)


def get_eics():
    ids = client.get_group(id=f'TMLR/Editors_In_Chief').members
    profiles = tools.get_profiles(client, ids)

    eics = []
    for profile in profiles:
        kw = {}
        try:
            names = sorted(
                profile.content['names'],
                key=lambda d: d.get('preferred', False)
            )[-1]
            kw['name'] = names['first'] + ' ' + names['last']
            if 'homepage' in profile.content:
                kw['url'] = profile.content['homepage']
            if 'history' in profile.content:
                kw['affiliation'] = profile.content['history'][0]['institution']['name']
            kw['last_name'] = kw['name'].split(' ')[-1]
            eics.append(kw)
        except:
            print('Issue with profile {}'.format(profile))
    eics = sorted(eics, key=lambda d: d['last_name'])
    return eics


def get_aes():
    ids = client.get_group(id=f'TMLR/Action_Editors').members
    #
    profiles = tools.get_profiles(client, ids)
    aes = []
    for profile in profiles:
        kw = {}
        names = sorted(profile.content['names'], key=lambda d: d.get(
            'preferred', False))[-1]
        # kw['name'] = names['first'] + ' ' + names['last']
        kw['name'] = names['fullname']
        if 'homepage' in profile.content:
            kw['url'] = profile.content['homepage']
        if 'history' in profile.content:
            kw['affiliation'] = profile.content['history'][0]['institution']['name']
        if 'expertise' in profile.content:
            keywords = ', '.join([' '.join(k['keywords'])
                                for k in profile.content['expertise']]) + '.'
        else:
            keywords = ''

        if 'first' not in names or 'last' not in names:
            name_parts = names['fullname'].rsplit(' ', 1)
            names['first'] = name_parts[0]
            names['last'] = name_parts[1]

        kw['last_name'] = names['last']

        kw['research'] = keywords.capitalize()
        kw['gscholar'] = profile.content.get('gscholar', None)
        kw['id'] = profile.id
        aes.append(kw)

    aes = sorted(aes, key=lambda d: unidecode.unidecode(d['last_name'].capitalize()))
    return aes


def get_expert_reviewers(expert_reviewers_group):
    ids = client.get_group(id=expert_reviewers_group).members
    #
    profiles = tools.get_profiles(client, ids)
    expert_reviewers = []
    for profile in profiles:
        kw = {}
        names = sorted(profile.content['names'], key=lambda d: d.get(
            'preferred', False))[-1]
        # kw['name'] = names['first'].capitalize() + ' ' + \
        #     names['last'].capitalize()
        kw['name'] = names['fullname']
        if 'homepage' in profile.content:
            kw['url'] = profile.content['homepage']
        if 'history' in profile.content:
            kw['affiliation'] = profile.content['history'][0]['institution']['name']
        if 'expertise' in profile.content:
            keywords = ', '.join([' '.join(k['keywords'])
                                for k in profile.content['expertise']]) + '.'
        else:
            keywords = ''

        if 'first' not in names or 'last' not in names:
            name_parts = names['fullname'].rsplit(' ', 1)
            names['first'] = name_parts[0]
            names['last'] = name_parts[1]

        kw['last_name'] = names['last']

        kw['research'] = keywords.capitalize()
        kw['gscholar'] = profile.content.get('gscholar', None)
        kw['id'] = profile.id
        expert_reviewers.append(kw)

    expert_reviewers = sorted(expert_reviewers, key=lambda d: unidecode.unidecode(d['last_name'].capitalize()))
    return expert_reviewers


def get_all_reviewers():
    all_groups = { g.id: g for g in client.get_all_groups(prefix='TMLR/Paper') }

    num_failures = 0
    reviewers_in_year = defaultdict(set)

    submissions = client.get_all_notes(invitation='TMLR/-/Submission', details='replies')
    for submission in submissions:
      replies = [openreview.api.Note.from_json(reply) for reply in submission.details['replies']]
      reviews = [r for r in replies if r.invitations[0].endswith('/-/Review')]
      date_submitted = datetime.fromtimestamp(submission.cdate / 1000.0)

      if reviews:
        for review in reviews:
          try:
            signature = review.signatures[0]
            reviewer_id = all_groups[signature].members[0]
            reviewers_in_year[date_submitted.year].add(reviewer_id)
          except:
            print('Failure in all_groups!')
            num_failures += 1

    # Get reviewer names
    # ----------------------------------------------------------------
    reviewer_names_in_year = {}
    for year in reviewers_in_year:
        reviewers = []
        profiles = tools.get_profiles(client, reviewers_in_year[year])
        for profile in profiles:
            kw = {}
            names = sorted(
                profile.content['names'],
                key=lambda d: d.get('preferred', False)
            )[-1]
            kw['name'] = names['fullname']

            if 'first' not in names or 'last' not in names:
                name_parts = names['fullname'].rsplit(' ', 1)
                names['first'] = name_parts[0]
                names['last'] = name_parts[1]

            kw['last_name'] = names['last']
            if kw not in reviewers:
                reviewers.append(kw)

        reviewers_sorted = sorted(reviewers, key=lambda d: unidecode.unidecode(d['last_name'].capitalize()))
        reviewer_names_in_year[year] = [r['name'] for r in reviewers_sorted]

    return reviewer_names_in_year


def load_html_from_url(url):
  try:
    response = requests.get(url)
    response.raise_for_status()
    return response.text
  except requests.exceptions.RequestException as e:
    print(f'Error fetching URL: {e}')
    return None


def get_papers():
    accepted = tools.iterget_notes(client,
        invitation='TMLR/-/Accepted',
        sort='pdate:desc'
    )

    inf_conf_url = 'https://tmlr.infinite-conf.org/index.html'
    html_content = load_html_from_url(inf_conf_url)
    if html_content:
      paper_ids_with_videos = re.findall(r'"paper_pages/(\w+).html"', html_content)
      paper_ids_with_videos = set(paper_ids_with_videos)

    papers = []
    for s in accepted:
        paper = {}
        paper['id'] = s.forum
        paper['title'] = s.content['title']['value']
        paper['openreview'] = f"https://openreview.net/forum?id={s.forum}"
        paper['pdf'] = f"https://openreview.net/pdf?id={s.forum}"
        paper['bibtex'] = s.content['_bibtex']['value']

        # there's a bug in the bib produced by openreview, in that it
        # says Transactions *of* instead of Transactions *on*
        paper['bibtex'] = paper['bibtex'].replace(
            'Transactions of',
            'Transactions on')
        paper['authors'] = ', '.join(s.content['authors']['value'])
        date = datetime.fromtimestamp(s.pdate / 1000.)
        paper['intdate'] = s.pdate

        paper['year'] = date.year
        paper['month'] = date.strftime("%B")

        # Certifications
        # --------------------------
        paper['certifications'] = []
        try:
            certifications = s.content['certifications']['value']
        except:
            certifications = {}

        if 'Survey Certification' in certifications:
            paper['survey_certification'] = True
            paper['certifications'].append('survey')
        if 'Reproducibility Certification' in certifications:
            paper['reproducibility_certification'] = True
            paper['certifications'].append('reproducibility')
        if 'Featured Certification' in certifications:
            paper['featured_certification'] = True
            paper['certifications'].append('featured')
        if 'Expert Certification' in certifications:
            paper['expert_certification'] = True
            paper['certifications'].append('expert')
        if 'Outstanding Certification' in certifications:
            paper['outstanding_certification'] = True
            paper['certifications'].append('outstanding')
        # --------------------------

        # Event certifications
        # --------------------------
        paper['event_certifications'] = []
        try:
            event_certifications = s.content['event_certifications']['value']
            for i in range(len(event_certifications)):
                if 'AutoML/2023' in event_certifications[i]:
                    event_certifications[i] = 'AutoML 2023'
                if 'CoLLAs/2023' in event_certifications[i]:
                    event_certifications[i] = 'CoLLAs 2023'
        except:
            event_certifications = {}

        if event_certifications:
            paper['event_certification'] = True
            paper['certifications'].append('event')
            # if 'CoLLAs 2023' in event_certifications:
            #     paper['collas_certification'] = True
            paper['which_event'] = ', '.join(event_certifications)
        # --------------------------


        if 'code' in s.content:
            paper['code'] = s.content['code']['value']

        if s.forum in paper_ids_with_videos:
            paper['video'] = f'https://tmlr.infinite-conf.org/paper_pages/{s.forum}.html'

        papers.append(paper)
    #sorted(papers, key=lambda d: d['intdate'])
    return papers


def gen_bibtex(env, context):
    """Generate bibtex."""
    for p in context['papers']:
        paper_id = p['id']
        with open(os.path.join("output", "papers", "bib", f"{paper_id}.bib"), "w") as f:
            f.write(p['bibtex'])



if __name__ == "__main__":

    base_url = ""
    env = Environment(
        loader=FileSystemLoader("templates"),
        autoescape=select_autoescape(["html", "xml"]),
    )

    context = {
        'editors_in_chief': get_eics(),
        'action_editors': get_aes(),
        'expert_reviewers_2023': get_expert_reviewers('TMLR/Expert_Reviewers/2023'),
        'expert_reviewers_2024': get_expert_reviewers('TMLR/Expert_Reviewers/2024'),
        'expert_reviewers_2025': get_expert_reviewers('TMLR/Expert_Reviewers/2025'),
        # 'reviewers': get_all_reviewers(),
        'papers': get_papers()
    }
    gen_bibtex(env, context)
    render_webpage(env, "index.html", base_url, context)
    for page in [
            "submissions.html",
            "contact.html",
            "editorial-board.html",
            "reviewer-guide.html",
            "author-guide.html",
            "acceptance-criteria.html",
            "ae-guide.html",
            "editorial-policies.html",
            "code.html",
            "faq.html",
            "news/index.html",
            "news/2022/launch.html",
            "papers/index.html",
            "ethics.html",
            # "reviewers.html",
    ]:
        render_webpage(env, page, base_url, context)
