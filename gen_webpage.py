import json
import os
from datetime import datetime
from glob import glob
from jinja2 import Environment, FileSystemLoader, select_autoescape
import utils


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


if __name__ == "__main__":

        base_url = ""
        env = Environment(
            loader=FileSystemLoader("templates"),
            autoescape=select_autoescape(["html", "xml"]),
        )

        render_webpage(env, "index.html", base_url)
        for page in [
                "author-info.html",
                "contact.html",
                "editorial-board.html",
                "editorial-board-reviewers.html",
                "news.html",
                "reviewer-guide.html",
                "stats.html",
                "faq.html",
        ]:
            render_webpage(env, page, base_url)
