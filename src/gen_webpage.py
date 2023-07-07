import os
import pdb
import unidecode
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, select_autoescape

import openreview
from openreview import tools


YEAR = datetime.today().year

os.makedirs("output/papers/bib/", exist_ok=True)


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
    client = openreview.api.OpenReviewClient(
        baseurl='https://api2.openreview.net', username=os.environ['OR_USER'], password=os.environ['OR_PASS'])

    ids = client.get_group(id=f'TMLR/Editors_In_Chief').members
    profiles = tools.get_profiles(client, ids)

    eics = []
    for id, profile in zip(ids, profiles):
        if id == '~Fabian_Pedregosa1':
            # Fabian is managing editor but has EIC privileges
            continue
        kw = {}
        try:
            names = sorted(profile.content['names'], key=lambda d: d.get(
                'preferred', False))[-1]
            kw['name'] = names['first'] + ' ' + names['last']
            if 'homepage' in profile.content:
                kw['url'] = profile.content['homepage']
            if 'history' in profile.content:
                kw['affiliation'] = profile.content['history'][0]['institution']['name']
        except:
            print(f'profile {id} not found')
            kw['name'] = id[1:-1].replace('_', ' ')
        kw['last_name'] = kw['name'].split(' ')[-1]
        eics.append(kw)
    eics = sorted(eics, key=lambda d: d['last_name'])
    return eics


def get_aes():
    client = openreview.api.OpenReviewClient(
        baseurl='https://api2.openreview.net', username=os.environ['OR_USER'], password=os.environ['OR_PASS'])

    ids = client.get_group(id=f'TMLR/Action_Editors').members
    #
    profiles = tools.get_profiles(client, ids)
    aes = []
    for profile in profiles:
        kw = {}
        names = sorted(profile.content['names'], key=lambda d: d.get(
            'preferred', False))[-1]
        kw['name'] = names['first'].capitalize() + ' ' + \
            names['last'].capitalize()
        if 'homepage' in profile.content:
            kw['url'] = profile.content['homepage']
        if 'history' in profile.content:
            kw['affiliation'] = profile.content['history'][0]['institution']['name']
        kw['last_name'] = names['last'].capitalize()
        if 'expertise' in profile.content:
            keywords = ', '.join([' '.join(k['keywords'])
                                for k in profile.content['expertise']]) + '.'
        else:
            keywords = ''
        kw['research'] = keywords.capitalize()
        kw['gscholar'] = profile.content.get('gscholar', None)
        kw['id'] = profile.id
        aes.append(kw)

    aes = sorted(aes, key=lambda d: unidecode.unidecode(d['last_name']))
    return aes


def get_expert_reviewers():
    client = openreview.api.OpenReviewClient(
        baseurl='https://api2.openreview.net', username=os.environ['OR_USER'], password=os.environ['OR_PASS'])

    ids = client.get_group(id=f'TMLR/Expert_Reviewers').members
    #
    profiles = tools.get_profiles(client, ids)
    expert_reviewers = []
    for profile in profiles:
        kw = {}
        names = sorted(profile.content['names'], key=lambda d: d.get(
            'preferred', False))[-1]
        kw['name'] = names['first'].capitalize() + ' ' + \
            names['last'].capitalize()
        if 'homepage' in profile.content:
            kw['url'] = profile.content['homepage']
        if 'history' in profile.content:
            kw['affiliation'] = profile.content['history'][0]['institution']['name']
        kw['last_name'] = names['last'].capitalize()
        if 'expertise' in profile.content:
            keywords = ', '.join([' '.join(k['keywords'])
                                for k in profile.content['expertise']]) + '.'
        else:
            keywords = ''
        kw['research'] = keywords.capitalize()
        kw['gscholar'] = profile.content.get('gscholar', None)
        kw['id'] = profile.id
        expert_reviewers.append(kw)

    expert_reviewers = sorted(expert_reviewers, key=lambda d: unidecode.unidecode(d['last_name']))
    return expert_reviewers


def get_papers():
    client = openreview.api.OpenReviewClient(
        baseurl='https://api2.openreview.net', username=os.environ['OR_USER'], password=os.environ['OR_PASS'])

    accepted = tools.iterget_notes(client,
        invitation='TMLR/-/Accepted',
        sort='pdate:desc')
    # accepted = client.get_all_notes(invitation='TMLR/-/Accepted', sort='mdate')
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

        paper['certifications'] = []
        # certifications = s.content['certifications']['value']
        # if 'Survey Certification' in certifications:
        #     paper['survey_certification'] = True
        #     paper['certifications'].append('survey')
        # if 'Reproducibility Certification' in certifications:
        #     paper['reproducibility_certification'] = True
        #     paper['certifications'].append('reproducibility')
        # if 'Featured Certification' in certifications:
        #     paper['featured_certification'] = True
        #     paper['certifications'].append('featured')

        if 'code' in s.content:
            paper['code'] = s.content['code']['value']

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
        'expert_reviewers': get_expert_reviewers(),
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
            "expert-reviewers.html"
    ]:
        render_webpage(env, page, base_url, context)
