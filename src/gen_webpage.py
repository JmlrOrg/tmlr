import os
import unidecode
from datetime import datetime
from glob import glob
from jinja2 import Environment, FileSystemLoader, select_autoescape

import openreview
from  openreview.journal import Journal


YEAR = datetime.today().year


if not os.path.exists("output"):
    os.mkdir("output")


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
    dev_client = openreview.api.OpenReviewClient(
        baseurl = 'https://api.openreview.net', username = os.environ['OR_USER'], password = os.environ['OR_PASS'])

    ids = dev_client.get_group(id=f'TMLR/Editors_In_Chief').members
    eics = []
    for id in ids:
        if id == '~Fabian_Pedregosa1':
            # Fabian is managing editor but has EIC privileges
            continue
        kw = {}
        try:
            profile = dev_client.get_profile(id)
            kw['name'] = profile.content['names'][0]['first'] + ' ' + profile.content['names'][0]['last']
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
    dev_client = openreview.api.OpenReviewClient(
        baseurl = 'https://api.openreview.net', username = os.environ['OR_USER'], password = os.environ['OR_PASS'])

    ids = dev_client.get_group(id=f'TMLR/Action_Editors').members
    aes = []
    for id in ids:
        kw = {}
        profile = dev_client.get_profile(id)
        kw['name'] = profile.content['names'][0]['first'].capitalize() + ' ' + profile.content['names'][0]['last'].capitalize()
        if 'homepage' in profile.content:
            kw['url'] = profile.content['homepage']
        if 'history' in profile.content:
            kw['affiliation'] = profile.content['history'][0]['institution']['name']
        kw['last_name'] = profile.content['names'][0]['last'].capitalize()
        keywords = ', '.join([' '.join(k['keywords']) for k in profile.content['expertise']]) + '.'
        kw['research'] = keywords.capitalize()
        aes.append(kw)

    aes = sorted(aes, key=lambda d: unidecode.unidecode(d['last_name']))
    return aes


if __name__ == "__main__":

        base_url = ""
        env = Environment(
            loader=FileSystemLoader("templates"),
            autoescape=select_autoescape(["html", "xml"]),
        )

        # context = {'editors_in_chief': get_eics(), 'action_editors': get_aes()}
        context = {}
        render_webpage(env, "index.html", base_url, context)
        for page in [
                "submissions.html",
                "contact.html",
                "editorial-board.html",
                "reviewer-guide.html",
                "author-guide.html",
                "ae-guide.html",
                "editorial-policies.html",
                "code.html",
                "news/2022/launch.html",
                "ethics.html"
        ]:
            render_webpage(env, page, base_url, context)
