"""The browser of the sign-in: what it sends for a form, as a real browser would."""

import unittest
from unittest import mock

from .support import AddonTest
from resources.lib import browser

PAGE = '''<html><body>
<form name="other" action="/other"><input name="x" value="1"></form>
<form name="signIn" id="sign-in" class="auth-form cvf-widget-form" method="post" action="/ap/signin">
  <input type="hidden" name="appActionToken" value="token">
  <input type="email" name="email" value="">
  <input type="password" name="password">
  <input type="checkbox" name="rememberMe" value="true">
  <input type="radio" name="option" value="sms" checked>
  <input type="radio" name="option" value="email">
  <select name="device"><option value="a">A</option><option value="b">B</option></select>
  <input type="text" name="off" value="no" disabled>
  <input type="submit" name="continue" value="Weiter">
  <input type="submit" name="cancel" value="Abbrechen">
  <button type="button" name="help">?</button>
</form></body></html>'''


class Answer:
    def __init__(self, text, url):
        self.text, self.url = text, url


class Forms(AddonTest):
    def setUp(self):
        super().setUp()
        self.browser = browser.StatefulBrowser()
        self.get = self.patch(self.browser.session, 'get', return_value=Answer(PAGE, 'https://www.amazon.de/ap/signin?x=1'))
        self.post = self.patch(self.browser.session, 'post', return_value=Answer('<html>done</html>', 'https://www.amazon.de/next'))
        self.browser.open('https://www.amazon.de/ap/signin?x=1')

    def test_a_form_is_found_by_name_id_or_class(self):
        for selector in ('form[name="signIn"]', 'form#sign-in', 'form.cvf-widget-form'):
            with self.subTest(selector=selector):
                self.assertEqual(self.browser.select_form(selector).form.get('name'), 'signIn')

    def test_a_form_the_page_does_not_have_is_reported(self):
        with self.assertRaises(browser.LinkNotFoundError):
            self.browser.select_form('form#pollingForm')

    def test_a_control_the_form_does_not_have_is_reported(self):
        self.browser.select_form('form[name="signIn"]')
        with self.assertRaises(browser.LinkNotFoundError):
            self.browser['otpCode'] = '123456'

    def test_the_form_is_sent_as_a_browser_sends_it(self):
        self.browser.select_form('form[name="signIn"]')
        self.browser['email'] = 'me@example.com'
        self.browser['password'] = 'secret'
        self.browser['option'] = 'email'
        self.browser['device'] = 'b'
        self.browser.form.set_checkbox({'rememberMe': True})
        answer = self.browser.submit_selected()
        self.assertEqual(self.post.call_args.args[0], 'https://www.amazon.de/ap/signin')
        self.assertEqual(self.post.call_args.kwargs['headers'], {'Referer': 'https://www.amazon.de/ap/signin?x=1'})
        # Hidden fields go along; a disabled field, the second submit button and plain buttons do not.
        self.assertEqual(self.post.call_args.kwargs['data'], [
            ('appActionToken', 'token'), ('email', 'me@example.com'), ('password', 'secret'),
            ('rememberMe', 'true'), ('option', 'email'), ('device', 'b'), ('continue', 'Weiter')])
        self.assertEqual((answer.text, self.browser.url), ('<html>done</html>', 'https://www.amazon.de/next'))

    def test_a_box_that_is_not_ticked_and_the_first_option_of_a_list_are_sent_as_a_browser_does(self):
        self.browser.select_form('form[name="signIn"]')
        self.browser.submit_selected()
        sent = dict(self.post.call_args.kwargs['data'])
        self.assertNotIn('rememberMe', sent)
        self.assertEqual((sent['option'], sent['device'], sent['password']), ('sms', 'a', ''))

    def test_a_form_without_a_method_is_sent_as_a_query(self):
        self.browser.select_form('form[name="other"]')
        self.browser.submit_selected()
        self.assertEqual(self.get.call_args.args[0], 'https://www.amazon.de/other')
        self.assertEqual(self.get.call_args.kwargs['params'], [('x', '1')])


if __name__ == '__main__':
    unittest.main()
