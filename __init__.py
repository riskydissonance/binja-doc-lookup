import requests
from urllib.parse import unquote
from lxml import html

from binaryninja.settings import Settings
from binaryninjaui import UIAction, UIActionHandler
from PySide6.QtGui import QDesktopServices, QKeySequence, Qt, QCursor
from PySide6.QtWidgets import QToolTip

def register_settings():
    Settings().register_group("doc_lookup", "Binja Doc Lookup")
    Settings().register_setting("doc_lookup.search_url", """
        {
            "title" : "Search URL",
            "type" : "string",
            "default" : "https://duckduckgo.com/?q=%5csite%3Alearn.microsoft.com+%22{search_term}%22",
            "description" : "The URL to search for the token. Use {search_term} as a placeholder for the token.",
            "ignore" : ["SettingsProjectScope", "SettingsResourceScope"]
        }
        """)
    Settings().register_setting("doc_lookup.tooltip_xpaths", """
        {
            "title" : "Tooltip Structure",
            "type" : "array",
            "elementType": "string",
            "default" : [
                        "/html/body/div[2]/div/section/div/div[1]/main/div[3]/p[1]",
                        "/html/body/div[2]/div/section/div/div[1]/main/div[3]/pre"
                        ],
            "description" : "The XPaths to the content to display in the tooltip.",
            "ignore" : ["SettingsProjectScope", "SettingsResourceScope"]
        }
        """)
    Settings().register_setting("doc_lookup.user_agent", """
        {
            "title" : "User Agent",
            "type" : "string",
            "default" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0",
            "description" : "The User-Agent to use for requests.",
            "ignore" : ["SettingsProjectScope", "SettingsResourceScope"]
        }
        """)


def action_token_tooltip(action_context):
    cursor_pos = QCursor.pos()
    headers = {
        'User-Agent': Settings().get_string('doc_lookup.user_agent'),
    }

    url = f"{Settings().get_string('doc_lookup.search_url').replace('{search_term}', action_context.token.token.text)}"
    response = requests.get(url, allow_redirects=True, headers=headers)
    if response.status_code == 200:
        if "window.location.replace(" in response.text:
            # Parse JS redirect
            new_url = response.text.split("window.location.replace('")[1].split("')")[0]
            new_url = new_url.split("&")[0]
            new_url = unquote(new_url[new_url.index("http"):])
            response = requests.get(new_url, allow_redirects=True, headers=headers)

        tree = html.fromstring(response.text)
        content = ""
        for xpath in Settings().get_string_list('doc_lookup.tooltip_xpaths'):
            elements = tree.xpath(xpath)
            if elements:
                content += elements[0].text_content() + "\n\n"
        QToolTip.showText(cursor_pos, content)
    else:
        QToolTip.showText(cursor_pos, f"Error: {response.status_code}")


def action_lookup_token(action_context):
    QDesktopServices.openUrl(f"{Settings().get_string('doc_lookup.search_url').replace('{search_term}', action_context.token.token.text)}")


def register_actions():
    action_text = "Binja Doc Lookup"
    UIAction.registerAction(action_text, QKeySequence(Qt.CTRL | Qt.SHIFT | Qt.Key_Q))
    UIActionHandler.globalActions().bindAction(action_text, UIAction(action_lookup_token))

    action_text = "Binja Doc Tooltip"
    UIAction.registerAction(action_text, QKeySequence(Qt.CTRL | Qt.Key_Q))
    UIActionHandler.globalActions().bindAction(action_text, UIAction(action_token_tooltip))


def main():
    register_settings()
    register_actions()

main()
