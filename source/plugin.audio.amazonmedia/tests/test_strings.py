"""The language files against each other and against the code that uses them."""

import glob
import os
import re
import unittest
import xml.etree.ElementTree as ElementTree

from .support import LANGUAGE_FOLDER, ROOT, SOURCE_LANGUAGE, TRANSLATIONS

_ENTRY = re.compile(r'^msgctxt "#(\d+)"\nmsgid (".*")\nmsgstr (".*")$', re.M)


def entries(language):
    path = os.path.join(LANGUAGE_FOLDER, 'resource.language.%s' % language, 'strings.po')
    with open(path, encoding='utf-8') as handle:
        body = handle.read()
    found = {int(number): (msgid, msgstr) for number, msgid, msgstr in _ENTRY.findall(body)}
    # A string wrapped over several lines would be dropped by the pattern
    # rather than reported, which would make every test below pass wrongly.
    assert len(found) == body.count('\nmsgctxt '), language
    return found


def ids_in_use():
    """Every string id the add-on refers to, in its code and in its settings."""
    used = set()
    for path in glob.glob(os.path.join(ROOT, 'resources', 'lib', '*.py')):
        with open(path, encoding='utf-8') as handle:
            used.update(int(number) for number in re.findall(r'\b(3\d{4})\b', handle.read()))
    with open(os.path.join(ROOT, 'resources', 'settings.xml'), encoding='utf-8') as handle:
        used.update(int(number) for number in re.findall(r'(?:label|help)="(3\d{4})"', handle.read()))
    return used


class Code(unittest.TestCase):
    def test_every_string_the_add_on_uses_exists(self):
        self.assertEqual(ids_in_use() - set(entries(SOURCE_LANGUAGE)), set())

    def test_no_string_is_left_behind_unused(self):
        self.assertEqual(set(entries(SOURCE_LANGUAGE)) - ids_in_use(), set())


class Languages(unittest.TestCase):
    def test_a_translation_carries_the_same_ids(self):
        for language in TRANSLATIONS:
            with self.subTest(language=language):
                self.assertEqual(set(entries(language)), set(entries(SOURCE_LANGUAGE)))

    def test_a_translation_keeps_the_english_source(self):
        english = entries(SOURCE_LANGUAGE)
        for language in TRANSLATIONS:
            with self.subTest(language=language):
                differing = {number for number, (msgid, _) in entries(language).items()
                             if msgid != english[number][0]}
                self.assertEqual(differing, set())

    def test_english_is_the_source_and_translates_nothing(self):
        translated = {number for number, (_, msgstr) in entries(SOURCE_LANGUAGE).items() if msgstr != '""'}
        self.assertEqual(translated, set())

    def test_a_translation_leaves_nothing_in_english(self):
        # A single word, such as "Albums" in French, may be the same in both languages.
        for language in TRANSLATIONS:
            with self.subTest(language=language):
                english = {number: msgid for number, (msgid, msgstr) in entries(language).items()
                           if msgstr == '""' or (msgstr == msgid and ' ' in msgid.strip('"'))}
                self.assertEqual(english, {})

    def test_a_german_setting_says_what_it_does_in_the_infinitive(self):
        # "Farbige Einträge zeigen" rather than the imperative "Zeige farbige Einträge".
        settings = ElementTree.parse(os.path.join(ROOT, 'resources', 'settings.xml')).getroot()
        german = entries('de_de')
        for setting in settings.iter('setting'):
            if setting.get('type') in ('boolean', 'action'):
                label = german[int(setting.get('label'))][1].strip('"')
                with self.subTest(label=label):
                    self.assertRegex(re.sub(r'\s*\(.*\)$', '', label), r'e[lr]?n$')

    def test_german_spells_addon_without_a_hyphen(self):
        hyphenated = {number: msgstr for number, (_, msgstr) in entries('de_de').items() if 'Add-on' in msgstr}
        self.assertEqual(hyphenated, {})


if __name__ == '__main__':
    unittest.main()
