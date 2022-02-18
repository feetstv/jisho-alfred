#!/usr/bin/env python3
# encoding: utf-8
from __future__ import annotations

import os
import sys

import json
import urllib.request, urllib.parse

# setup access to the local .site-packages
sys.path.insert(0, os.path.dirname(__file__) + "/.site-packages")  # noqa


from workflow import Workflow3, ICON_WEB, ICON_INFO, ICON_NOTE, ICON_ERROR

API_URL = 'https://jisho.org/api/v1/search/words'
MAX_NUM_RESULTS = 50  # Maximum number of results to show in Alfred.
SEP_COMMA = u'、 '    # Separator between Japanese characters and words.
SEP_BAR = u' | '      # Separator between different info: kana and definitions.


def get_results(query):
    """Fetches query search results from Jisho.org API.
    Args:
        query: A string representing the search query for Jisho.org.
    Returns:
        An array of JSON results from Jisho.org based on search query.
    """
    request = urllib.request.urlopen(API_URL + "?keyword=" + urllib.parse.quote(query, encoding='utf-8'))
    # Parse response as JSON and extract results.
    data = request.read()
    encoding = request.info().get_content_charset('utf-8')
    json_obj = json.loads(data.decode(encoding))

    return json_obj['data']


def add_alfred_result(wf, result):
    """Adds the result to Alfred.
    Args:
        wf: An instance of Workflow.
        result: A dict representation of info about the Japanese word.
    """
    # Contains kanji and kana for the result.
    japanese = result['japanese']

    # Contains info like English definitions and parts of speech.
    senses = result['senses']

    # Combined English definitions string.
    combined_eng_defs = combine_english_defs(senses)

    # First Japanese word and reading. Likely the most common word and reading.
    word_reading = japanese[0]

    # Determine title and subtitle based on if there is kanji and kana.
    if has_kanji_and_kana(word_reading):
        title = word_reading['word']  # Kanji.
        kana_reading = word_reading['reading']
        subtitle = kana_reading + SEP_BAR + combined_eng_defs
    elif has_just_kanji(word_reading):
        title = word_reading['word']  # Kanji.
        subtitle = combined_eng_defs
    else:
        title = word_reading['reading']  # Kana. No kanji, so kana title.
        subtitle = combined_eng_defs

    # Add Alfred result item based on info above.
    wf.add_item(title=title, subtitle=subtitle, arg=title, valid=True,
                largetext=title, icon=ICON_WEB)


def has_kanji_and_kana(word_reading):
    """Returns True if there is both kanji and kana in the word reading.
    Args:
        word_reading: A dict that might have a 'word' or 'reading' key.
    Returns:
        True if 'word' and 'reading' are keys in the dict.
    """
    return 'word' in word_reading and 'reading' in word_reading


def has_just_kanji(word_reading):
    """Returns True if there is just kanji in the word reading.
    Args:
        word_reading: A dict that might have a 'word' or 'reading' key.
    Returns:
        True if 'reading' in not a key and 'word' is a key in the dict.
    """
    return 'reading' not in word_reading and 'word' in word_reading


def combine_english_defs(senses, separator=u', '):
    """Combines the English definitions in senses.
    Args:
        senses: An array with dict elements with English info.
    Returns:
        A string of English definitions separated by the separator.
    """
    # Each sense contains a list of English definitions. e.g. [[], [], []]
    eng_defs_lists = [sense['english_definitions'] for sense in senses
                      if 'english_definitions' in sense]

    # Combine the inner lists of English definitions into one list.
    combined_eng_defs = [eng_def for eng_def_list in eng_defs_lists for eng_def in eng_def_list]
    return separator.join(combined_eng_defs)


def is_valid_query(query):
    """Returns True if the query is not just a single quote.
    Args:
        query: A string representing the search query for Jisho.org.
    Returns:
        True if the query is not just a single- or double-quotation mark.
    """
    sanitized_query = query.strip()
    return not (sanitized_query == u'"' or sanitized_query == u"'")


def main(wf: Workflow3):
    """Main function to handle query and request info from Jisho.org.
    Args:
        wf: An instance of Workflow.
    """
    # Get query from Alfred.
    query = wf.args[0] if len(wf.args) else None

    # Add query result if there is an update.
    if wf.update_available:
        wf.add_item('A newer version of Jisho Alfred Workflow is available',
                    'Action this item to download and install the new version',
                    autocomplete='workflow:update',
                    icon=ICON_INFO)

    try:
        # Only fetch results from Jisho.org if it is a valid query.
        results = get_results(query) if is_valid_query(query) else []

        if results:
            # Add results to Alfred, up to the maximum number of results.
            for i in range(min(len(results), MAX_NUM_RESULTS)):
                add_alfred_result(wf, results[i])
        else:
            # Add an error result if there was an issue getting results.
            error_msg = "Could not find anything matching '%s'" % (query)
            wf.add_item(error_msg, arg=query, valid=True, icon=ICON_NOTE)
    except Exception as e:
        # Add an error result if there was an issue getting results.
        error_msg = "There was an issue retrieving Jisho results"
        print(e)
        wf.add_item(error_msg, arg=query, valid=True, icon=ICON_ERROR)

    # Send the results to Alfred as XML.
    wf.send_feedback()

if __name__ == "__main__":
    # Create a global `Workflow3` object
    wf = Workflow3()
    wf.logger.info(__name__)
    # Call your entry function via `Workflow3.run()` to enable its
    # helper functions, like exception catching, ARGV normalization,
    # magic arguments etc.
    wf.run(main)
