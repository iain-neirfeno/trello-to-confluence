#Tool to move Trello cards to Confluence

Reads a board from Trello and formats the cards within the board using Mustache templates in the /templates directory

##First launch

When first running the application it will gather connection details for both Trello and Confluence. These details are stored in .keys file. Following runs will not ask for these details unless it is unable to connect.

##Configuring for Confluence

You will be asked to provide a parent page id, this is the integer within the URL on Confluence.

##Configuring for Trello

You will be asked to select a board to import cards from. Once selected you will be shown a list of columns, you can then name the columns by index. These names are then used within the template.

##The template

This tool uses Mustache, the names you picked earlier will be the top level keys for the template so as an example if the names you picked were open, in_progress, closed. Then you can have a template like

```
h2. Open
{{#open}}
* {{name}}
{{/open}}

h2. In Progress
{{#in_progress}}
* {{name}}
{{/in_progress}}

h2. Closed
{{#closed}}
* {{name}}
{{/closed}}
```

The template uses wiki markup for confluence

##Cleanup

After the Confluence page has been created, the cards imported will be archived. Any cards not imported as the column was unused will remain on the board. For example if you have a Backlog list.
