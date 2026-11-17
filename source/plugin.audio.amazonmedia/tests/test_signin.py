"""Signing in: the domain an account ends up on, and approval on another device."""

import os
import unittest

import xbmcgui


from .support import AddonTest, Kodi
from resources.lib import browser
from resources.lib.logon import AMlogon

# The approval page as Amazon serves it, cut down to what the add-on reads.
APPROVAL_PAGE = '''<html><body><div class="a-section chimera-body-container">
<div class="a-section a-spacing-medium"><span class="a-size-base-plus transaction-approval-word-break a-text-bold">
Genehmige zu deiner Sicherheit die Benachrichtigung, die an folgende Adresse gesendet wurde:</span></div>
<div id="channelDetailsWithImprovedLayout" class="a-section">
<div class="a-section a-spacing-extra-large">
<div class="a-row a-spacing-small"><div class="a-column a-span4"><span class="a-color-tertiary">Geltungsbereich</span></div>
<div class="a-column a-span8 a-span-last">          Amazon Music, Smartphone
</div></div>
</div></div>
<form id="pollingForm" method="get" action="/ap/cvf/approval/poll"><input type="hidden" name="arb" value="x"/></form>
</div></body></html>'''

# The page as Amazon serves it when it sent a message to the smartphone and also offers a code.
CODE_FORM = '<form id="verification-code-form" method="post"><input type="tel" name="otpCode"/></form>'
APPROVAL_OR_CODE_PAGE = APPROVAL_PAGE.replace('</div></body>', CODE_FORM + '</div></body>')

# What submitting the polling form returns while the user has not answered yet.
PENDING = '<html><body><input type="hidden" name="transactionApprovalStatus" value="TransactionPending"/></body></html>'

COMPLETED = '<html><body><input type="hidden" name="transactionApprovalStatus" value="TransactionCompleted"/></body></html>'
EXPIRED = '<html><body><input type="hidden" name="transactionApprovalStatus" value="TransactionExpired"/></body></html>'

# What the approval page turns into once the user has approved.
SIGNED_IN = '<html><body>Amazon Music</body></html>'


def app_config(territory):
    return {'accessToken': 'token', 'csrf': {'token': 'csrf', 'ts': '1', 'rnd': '2'},
            'deviceId': 'device-id', 'customerId': 'customer-id', 'marketplaceId': 'marketplace-id',
            'deviceType': 'device-type', 'musicTerritory': territory, 'displayLanguage': 'en_GB',
            'siteRegion': 'EU', 'tier': 'PRIME'}


class Domain(AddonTest):
    def test_a_uk_account_stays_on_the_uk_domain(self):
        logon = AMlogon()
        logon._appConfig(app_config('GB'))
        self.assertEqual(logon.credentials.USERTLD, 'co.uk')

    def test_a_territory_that_is_its_own_domain_is_kept(self):
        logon = AMlogon()
        logon._appConfig(app_config('FR'))
        self.assertEqual(logon.credentials.USERTLD, 'fr')


class Browser:
    """The part of the browser the approval step uses, fed with fixed pages."""

    url = 'https://www.amazon.de/ap/cvf/approval?openid.return_to=https%3A%2F%2Fmusic.amazon.de%2F'

    def __init__(self, logon):
        self.logon = logon
        self.form = None
        self.polled = 0

    def select_form(self, selector):
        if selector.split('#')[-1] not in self.logon._content:
            raise browser.LinkNotFoundError()
        self.form = selector


class Approval(AddonTest):
    def signing_in(self, polls, opened=SIGNED_IN, content=APPROVAL_PAGE):
        """polls: what the polling form answers, one answer per poll; opened: the page the sign-in returns to"""
        logon = AMlogon()
        logon._br = Browser(logon)
        logon._content = content
        answers = list(polls)

        def poll():
            logon._br.polled += 1
            logon._content = answers.pop(0)
        self.patch(logon, '_open', side_effect=lambda url: setattr(logon, '_content', opened))
        self.patch(logon, '_getLogonResponse', side_effect=poll)
        return logon

    def test_the_prompt_says_where_the_notification_went(self):
        logon = AMlogon()
        message = logon._approvalMessage(logon._parseHTML(APPROVAL_PAGE))
        self.assertEqual(message.split(os.linesep), [
            'Genehmige zu deiner Sicherheit die Benachrichtigung, die an folgende Adresse gesendet wurde:',
            'Geltungsbereich: Amazon Music, Smartphone'])

    def test_the_waiting_dialog_shows_the_whole_prompt(self):
        logon = self.signing_in([COMPLETED])
        logon._checkMFA()
        self.assertIn('Geltungsbereich: Amazon Music, Smartphone', Kodi.progress[0])

    def test_the_sign_in_goes_on_once_the_request_is_approved(self):
        logon = self.signing_in([PENDING, COMPLETED])
        self.assertTrue(logon._checkMFA())
        self.assertEqual((logon._content, logon._br.polled), (SIGNED_IN, 2))

    def test_the_polling_form_is_not_loaded_again_between_polls(self):
        logon = self.signing_in([PENDING, COMPLETED])
        opened = []
        self.patch(logon, '_open', side_effect=opened.append)
        logon._checkMFA()
        self.assertEqual(len(opened), 1)    # only the return to the music page after the approval

    def test_an_expired_request_ends_the_sign_in(self):
        logon = self.signing_in([EXPIRED])
        self.assertFalse(logon._checkMFA())

    def code_page(self, choice):
        logon = self.signing_in([], content=APPROVAL_OR_CODE_PAGE)
        dialog = self.patch(xbmcgui.Dialog, 'yesnocustom', return_value=choice)
        self.patch(logon, '_getLogonResponse', side_effect=lambda: setattr(logon, '_content', SIGNED_IN))
        return logon, dialog

    def test_a_code_page_asks_with_ok_and_does_not_wait_for_an_approval(self):
        logon, dialog = self.code_page(1)
        asked = self.patch(logon, 'getUserInput', return_value='123456')
        self.patch(logon, '_selectForm', return_value=True)
        self.patch(logon, '_setControl', return_value=True)
        self.assertTrue(logon._checkMFA())
        dialog.assert_called_once()
        asked.assert_called_once()
        self.assertEqual(Kodi.progress, [])

    def test_cancelling_the_code_dialog_ends_the_sign_in(self):
        logon, dialog = self.code_page(-1)
        asked = self.patch(logon, 'getUserInput', return_value='123456')
        self.assertFalse(logon._checkMFA())
        asked.assert_not_called()

    def test_the_code_can_be_sent_again(self):
        logon, dialog = self.code_page(0)
        selected = self.patch(logon, '_selectForm', return_value=True)
        self.patch(logon, '_hasControl', return_value=True)
        controls = []
        self.patch(logon, '_setControl', side_effect=lambda n, v: controls.append(n) or True)
        logon._approvalCode(AMlogon._parseHTML(APPROVAL_OR_CODE_PAGE))
        selected.assert_called_with('form#resend-approval-form')
        self.assertEqual(controls, ['isResend'])

    def test_whatsapp_can_be_chosen(self):
        logon, dialog = self.code_page(2)
        self.patch(logon, '_selectForm', return_value=True)
        self.patch(logon, '_hasControl', return_value=True)
        controls = []
        self.patch(logon, '_setControl', side_effect=lambda n, v: controls.append(n) or True)
        logon._approvalCode(AMlogon._parseHTML(APPROVAL_OR_CODE_PAGE))
        self.assertIn('isRedirectForWhatsapp', controls)

    def test_the_text_of_a_verification_page_is_logged_without_scripts(self):
        page = AMlogon._parseHTML('<html><script>var secret=1</script><body><p>Wir haben einen Code per WhatsApp gesendet.</p></body></html>')
        self.assertEqual(AMlogon._visibleText(page), 'Wir haben einen Code per WhatsApp gesendet.')


class Diagnosis(unittest.TestCase):
    """What is logged of a verification page: the names of its forms and controls, never a value."""

    def test_values_stay_out_of_the_log(self):
        page = '''<form id="verification-code-form" method="post"><input type="hidden" name="arb" value="secret-token">
                  <input type="text" name="otpCode"><a id="resend-link" href="/ap/x?token=secret">Erneut senden</a>
                  <button type="submit" name="continue">Weiter</button></form><script>send()</script>'''
        described = AMlogon._describeForms(AMlogon._parseHTML(page))
        self.assertEqual(described, {'forms': [{'form': 'verification-code-form', 'method': 'post',
                                                'controls': ['hidden:arb', 'text:otpCode', 'submit:continue'],
                                                'links': ['resend-link']}], 'scripts': 1})
        self.assertNotIn('secret', str(described))


if __name__ == '__main__':
    unittest.main()
