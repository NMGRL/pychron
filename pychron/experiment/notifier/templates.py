from jinja2 import Template

BASE_TEMPLATE = '''
user           = {{experiment.username}}
computer       = {{shorthost}}({{host}})
Pychron Ver.   = {{version}}
spectrometer   = {{experiment.mass_spectrometer}}
extract device = {{experiment.extract_device}}
timestamp      = {{timestamp}}
last run       = {{last_runid}}
runs           = {{experiment.execution_ratio}}

{%if not log == '' %}
======================== Error ========================
{{error}}
=======================================================
{% endif %}

{%if not log == '' %}
========================  Log  ========================
{{log}}
=======================================================
{% endif %}
'''


def email_template(**kw):
    return _render(BASE_TEMPLATE, **kw)


def success_template(**kw):
    return _render(BASE_TEMPLATE, **kw)


def error_template(**kw):
    return _render(BASE_TEMPLATE, **kw)


def _render(template, **kw):
    temp = Template(template)
    return temp.render(**kw)
