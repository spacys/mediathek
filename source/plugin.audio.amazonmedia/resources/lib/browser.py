#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
A browser for the sign-in pages: opens a page, fills in a form and submits it.

It offers the part of mechanicalsoup the sign-in uses, on top of requests and
BeautifulSoup, which Kodi's own repository carries. mechanicalsoup itself is
not in that repository, so the add-on could not be installed where it was missing.
"""

import re
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


class LinkNotFoundError(Exception):
    """The page has no such form, or the form no such control"""


class Form(object):
    """A form of the current page, as BeautifulSoup parsed it"""

    def __init__( self, form ):
        self.form = form

    def _controls( self, name ):
        found = self.form.find_all(['input', 'select', 'textarea'], attrs={'name': name})
        if not found:
            raise LinkNotFoundError('No control named {}'.format(name))
        return found

    def set( self, name, value ):
        """
        Fill in the control of that name: a text is typed, a radio button or an option is chosen
        by its value, a checkbox is ticked or cleared
        """
        controls = self._controls(name)
        first = controls[0]
        kind = (first.get('type') or 'text').lower()
        if first.name == 'textarea':
            first.string = value
        elif first.name == 'select':
            options = first.find_all('option')
            chosen = [o for o in options if o.get('value', o.get_text()) == value]
            if not chosen:
                raise LinkNotFoundError('No option {} in {}'.format(value, name))
            for option in options:
                option.attrs.pop('selected', None)
            chosen[0]['selected'] = 'selected'
        elif kind == 'radio':
            chosen = [c for c in controls if c.get('value') == value]
            if not chosen:
                raise LinkNotFoundError('No radio button {} in {}'.format(value, name))
            for control in controls:
                control.attrs.pop('checked', None)
            chosen[0]['checked'] = 'checked'
        elif kind == 'checkbox':
            self.set_checkbox({name: value})
        else:
            first['value'] = value

    def set_checkbox( self, data ):
        """
        Tick or clear checkboxes
        :param dict data: name of the checkbox and True or False, or the value of the box to tick
        """
        for name, value in data.items():
            for box in self._controls(name):
                if value is True or (value is not False and box.get('value') == value):
                    box['checked'] = 'checked'
                else:
                    box.attrs.pop('checked', None)

    def data( self ):
        """
        What a browser sends for this form: every control with a name, without disabled ones,
        boxes that are not ticked and all buttons but the first one that submits
        """
        data = []
        submitted = False
        for control in self.form.find_all(['input', 'select', 'textarea', 'button']):
            name = control.get('name')
            kind = (control.get('type') or '').lower()
            submits = (control.name == 'button' and kind in ('', 'submit')) or \
                      (control.name == 'input' and kind in ('submit', 'image'))
            if submits:
                # The first button that submits is the one a click on "continue" presses.
                if submitted:
                    continue
                submitted = True
            if not name or control.has_attr('disabled') or kind in ('button', 'reset', 'file'):
                continue
            if control.name == 'select':
                options = control.find_all('option')
                chosen = [o for o in options if o.has_attr('selected')] or options[:1]
                for option in chosen:
                    data.append((name, option.get('value', option.get_text())))
            elif control.name == 'textarea':
                data.append((name, control.get_text()))
            elif kind in ('checkbox', 'radio'):
                if control.has_attr('checked'):
                    data.append((name, control.get('value', 'on')))
            else:
                data.append((name, control.get('value', '')))
        return data


class StatefulBrowser(object):
    """Keeps the cookies, the current page and the form that was selected on it"""

    def __init__( self, soup_config=None, timeout=None ):
        self.session = requests.Session()
        self.timeout = timeout
        self.soup_config = soup_config or {'features': 'html.parser'}
        self.url = None
        self.page = None
        self.form = None

    def set_cookiejar( self, cookiejar ):
        self.session.cookies = cookiejar

    def _keep( self, response ):
        self.url = response.url
        self.page = BeautifulSoup(response.text, **self.soup_config)
        self.form = None
        return response

    def open( self, url ):
        return self._keep( self.session.get(url, timeout=self.timeout) )

    # tag, #id, .class and [attribute="value"] of one element; no need for a CSS engine here
    SELECTOR = re.compile(r'^(?P<tag>[\w-]+)?(?:#(?P<id>[\w-]+))?(?:\.(?P<cls>[\w-]+))?(?:\[(?P<attr>[\w-]+)="(?P<value>[^"]*)"\])?$')

    def _select( self, selector ):
        match = self.SELECTOR.match(selector.strip())
        if not match:
            raise ValueError('Selector not supported: {}'.format(selector))
        attrs = {}
        if match.group('id'):
            attrs['id'] = match.group('id')
        if match.group('attr'):
            attrs[match.group('attr')] = match.group('value')
        found = self.page.find_all(match.group('tag') or True, attrs=attrs)
        cls = match.group('cls')
        return [tag for tag in found if not cls or cls in (tag.get('class') or [])]

    def select_form( self, selector='form' ):
        found = self._select(selector) if self.page is not None else []
        if not found:
            raise LinkNotFoundError('No form matches {}'.format(selector))
        self.form = Form(found[0])
        return self.form

    def __setitem__( self, name, value ):
        if self.form is None:
            raise LinkNotFoundError('No form selected')
        self.form.set(name, value)

    def submit_selected( self ):
        if self.form is None:
            raise LinkNotFoundError('No form selected')
        form = self.form.form
        url = urljoin(self.url, form.get('action') or self.url)
        data = self.form.data()
        headers = {'Referer': self.url}
        if (form.get('method') or 'get').lower() == 'post':
            return self._keep( self.session.post(url, data=data, headers=headers, timeout=self.timeout) )
        return self._keep( self.session.get(url, params=data, headers=headers, timeout=self.timeout) )
