from trello import TrelloClient, util
from atlassian import Confluence
from os import listdir, path
import pystache
import datetime
import json
from traceback import print_exc
from time import sleep
from re import sub

try:
    keys = {}
    if path.exists('.keys'):
        with open('.keys') as f:
            keys = json.load(f)

    url = keys.get('url') or input('Confluence URL:').strip()

    email = keys.get('email') or input('Email address:').strip()
    api_key = keys.get('api_key') or input('API Key for Atlassian (https://id.atlassian.com/manage/api-tokens):').strip()

    confluence = Confluence(
        url=url,
        username=email,
        password=api_key
    )

    parent = keys.get('parent') or int(input("Parent page ID:").strip())
    parent_page = confluence.get_page_by_id(parent)
    while not isinstance(parent_page, dict):
        email = input('Email address:').strip()
        api_key = input('API Key for Atlassian (https://id.atlassian.com/manage/api-tokens):').strip()
        confluence = Confluence(
            url=url,
            username=email,
            password=api_key
        )
        parent_page = confluence.get_page_by_id(parent)

    while not input(f"Create page under {parent_page['title']}? [y/n]:").strip().lower().startswith('y'):
        space = input("Confluence Space ID:").strip()
        parent = input("Parent page ID:").strip()
        parent_page = confluence.get_page_by_id(parent)

    boards = None

    while not boards:
        trello_api_key = keys.get('trello_api_key') or input("Trello API Key (https://trello.com/app-key):").strip()
        trello_api_secret = keys.get('trello_api_secret') or input("Trello API Secret (https://trello.com/app-key):").strip()

        if 'oauth_token' not in keys or 'oauth_token_secret' not in keys:
            try:
                oauth_result = util.create_oauth_token('never', 'read,write', trello_api_key, trello_api_secret)
                keys['oauth_token'] = oauth_result['oauth_token']
                keys['oauth_token_secret'] = oauth_result['oauth_token_secret']
            except:
                try:
                    del keys['trello_api_key']
                    del keys['trello_api_secret']
                except:
                    pass

        oauth_token = keys.get('oauth_token')
        oauth_token_secret = keys.get('oauth_token_secret')

        trello = TrelloClient(
            api_key=trello_api_key,
            api_secret=trello_api_secret,
            token=oauth_token,
            token_secret=oauth_token_secret
        )
        try:
            boards = trello.list_boards()
            with open('.keys', 'w') as f:
                json.dump({
                    "url": url,
                    "email": email,
                    "api_key": api_key,
                    "trello_api_key": trello_api_key,
                    "trello_api_secret": trello_api_secret,
                    "parent": parent,
                    "oauth_token": oauth_token,
                    "oauth_token_secret": oauth_token_secret
                }, f)
        except:
            del keys['oauth_token']
            del keys['oauth_token_secret']

    print("\n\nPlease select a board:")
    for i, board in enumerate(boards):
        print(f"{board.name} - {i+1}")
    board_index = int(input("id [1]: ").strip() or 1)

    board = boards[board_index - 1]

    print(f"\nSelected board {board.name}")

    columns = board.get_lists(None)

    templates = listdir('templates')
    print("\n\nPlease select the template for the page")
    for i, template in enumerate(templates):
        print(f"{template} - {i+1}")
    template_index = int(input("\nSelect template to use [1]:").strip() or 1)

    template_filename = path.join("templates", templates[template_index - 1])

    print("\n\nPlease select relevant columns")
    for i, column in enumerate(columns):
        print(f"{column.name} - {i+1}")
    config = {}
    if path.exists('columns.json'):
        with open('columns.json') as f:
            config = json.load(f)
    column_config = config.get(template_filename, {})

    done = False
    column_index = 0
    if column_config:
        print("\n\nCurrent column configuration is:")
        for name, col in column_config.items():
            print(f"{columns[col].name} => {name}")
        done = (input("\nKeep this configuration? [y]:").strip() or 'y').lower().startswith('y')
        if not done:
            column_config = {}
    if not done:
        print("\n\n")
    while not done and column_index < len(columns):
        column_or_done = input(f'Select a column or type n to stop [{column_index + 1}]:').strip()
        if column_or_done.startswith('n'):
            break
        column_index = int(column_or_done or (column_index + 1))
        if column_index > len(columns):
            print(f"Column {column_index} does not exist!")
            continue
        column_name = sub('[^a-z0-9]+', '_', columns[column_index - 1].name.lower())
        column_name = input(f"Select a name for the column [{column_name}]:").strip() or column_name
        column_config[column_name] = column_index - 1

    config[template_filename] = column_config

    with open('columns.json', 'w') as f:
        json.dump(config, f)

    data = {k: columns[i].list_cards() for k, i in column_config.items()}
    with open(template_filename) as f:
        body = pystache.render(f.read(), data)

    print("\n\n####################################################################\n\n")
    print(body)

    ok = input("\nDoes this look good? y/n [n]:").strip() or 'n'

    if not ok.lower().startswith('y'):
        print("\n\nPlease start again")
    else:
        all_cards = [c for v in data.values() for c in v]

        if all_cards:

            today = datetime.date.today()
            title = f"{today.strftime('%d %B %Y')} - {today.strftime('%A')} Retrospective"  #TODO: Make this more generic
            title = input(f"\n\nSelect a page title [{title}]: ").strip() or title

            confluence.create_page(
                space=parent_page['space']['key'],
                title=title,
                parent_id=parent,
                body=body,
                representation='wiki'
            )
        else:
            print("\n\nNo cards to add to page")

        for card in all_cards:
            card.set_closed(True)

except:
    print_exc()
sleep(2)
input("\n\nPress enter to close")
