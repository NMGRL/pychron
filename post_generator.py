import argparse
from datetime import datetime
import os
from jinja2 import Template

TEXT = '''---
layout: {{layout}}
title: {{title}}
author: {{author}}
comments: {{use_comments}}
---

<!--========================== Blog =========================-->
Enter blog text here
<!--=========================== EOF =========================-->
'''


def generate_post(args):
    title = args.title

    name = '{}-{}.md'.format(datetime.now().strftime('%Y-%m-%d'), title)
    p = os.path.join(os.path.dirname(__file__), '_posts', name)
    if os.path.isfile(p):
        print '{} already exists'.format(name)
        return

    temp = Template(TEXT)

    print 'Rendering template'
    for ai in dir(args):
        if not ai.startswith('_'):
            print '    {:<15s}= {}'.format(ai, getattr(args, ai))

    txt = temp.render(title=title,
                      author=args.author,
                      layout=args.layout,
                      use_comments=not args.nocomments)

    print 'Generated Blog boilerplate\n'
    print txt

    if not args.dryrun:
        print 'Writing blog boilerplate to {}'.format(p)
        with open(p, 'w') as fp:
            fp.write(txt)
    else:
        print 'Dry Run. Not writing boilerplate'

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

    parser.add_argument('-n', '--nocomments',
                        action="store_true",
                        help='Do not use Disqus comments for this post')
    parser.add_argument('-d','--dryrun',
                        action="store_true",
                        help='Do a dry run. Do not write file.')
    # if args:
    # title = args[0]
    # else:
    # title = 'blank'
    args = parser.parse_args()
    generate_post(args)
