import argparse
from datetime import datetime
import os
from jinja2 import Template

TEXT = '''---
layout: {{layout}}
title: {{title}}
author: {{author}}
---

Enter blog text here
'''


def generate_post(args):
    title = args.title

    name = '{}-{}.md'.format(datetime.now().strftime('%Y-%m-%d'), title)
    p = os.path.join(os.path.dirname(__file__), '_posts', name)
    if os.path.isfile(p):
        print '{} already exists'.format(name)
        return

    temp = Template(TEXT)
    author = args.author
    layout = args.layout
    txt = temp.render(title=title,
                      author=author,
                      layout=layout)

    with open(p, 'w') as fp:
        fp.write(txt)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Make a pychron application')
    parser.add_argument('-t', '--title',
                        type=str,
                        default='blank',
                        help='set title for this post')
    parser.add_argument('-a', '--author',
                        type=str,
                        default='Jake Ross',
                        help='set author for this post')
    parser.add_argument('-l', '--layout',
                        type=str,
                        default='post',
                        help='set layout for this post')
    # if args:
    # title = args[0]
    # else:
    #     title = 'blank'
    args = parser.parse_args()
    generate_post(args)
