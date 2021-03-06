"""
Module containing functions for loading widgets, as well as some basic common
functionality shared by various widgets.
"""
from functools import partial
import os.path
import pkgutil


# This structure will be replaced with dynamic interaction with the server.
GROUPS = {
    "at-a-glance": {
        "widgets": [
            {
                "name": "as-overview",
                "resource-types": ["asn"]
            },
            {
                "name": "prefix-overview",
                "resource-types": ["ip"]
            },
            {
                "name": "geoloc",
                "resource-types": ["ip", "asn"]
            },
            {
                "name": "registry-browser",
                "resource-types": ["ip", "asn"]
            },
            {
                "name": "routing-status",
                "resource-types": ["ip", "asn"]
            }
        ]
    }
}


def get_group_widgets(group_name, resource_type):
    """
    Get a list of widgets for the given group and resource type.
    """
    group_name = group_name.lower()
    group_widgets = GROUPS.get(group_name)
    if group_widgets is None:
        return
    widgets = []
    for widget in group_widgets.get("widgets", []):
        if resource_type in widget["resource-types"]:
            widgets.append(widget["name"])
    return widgets


def get_widget(widget_name):
    """
    Return a text widget if one exists, otherwise return the default data
    call wrapper widget.
    """
    sanitized_name = widget_name.replace("-", "_").replace(" ", "_")
    try:
        module = __import__("ripestat.widgets.%s" % sanitized_name,
                            fromlist=True)
    except ImportError:
        return partial(default_widget, widget_name)
    return module.widget


def get_widget_list():
    """
    Get a list of lines describing every installed widget.
    """
    dirname = os.path.dirname(__file__)
    rows = []
    for _, name, _ in pkgutil.iter_modules([dirname]):
        rows.append(name)
    rows.sort()
    return simple_table(rows)


def get_widget_groups():
    """
    Iterate over tuples of (widget group name, widget list).
    """
    for group, definition in GROUPS.items():
        yield group, definition["widgets"]


def default_widget(widget_name, api, query):
    """
    This 'widget' translates the response of the data call called 'widget_name'
    in to a rudimentary whois format.
    """
    data = api.get_data(widget_name, query)
    items = [
        "'%s' doesn't have a command-line widget yet. Below is a direct "
        "translation of the data response." % widget_name,
        "You can contribute a widget at "
        "https://github.com/RIPE-NCC/ripestat-text",
    ]
    title = widget_name
    resource = data.get("resource")
    if resource:
        items.append((title, data["resource"]))
        del data["resource"]
    for key in sorted(data):
        if key not in ("query_time", "query_starttime", "query_endtime"):
            items.append((key, data[key]))
    return data, items


def simple_table(rows):
    """
    For each sequence in 'rows', yield a string containing properly spaced
    columns.
    """
    # Calculate the column widths
    widths = None
    rows = list(rows)
    for row in rows:
        if not isinstance(row, (list, tuple)):
            continue
        if widths is None:
            widths = [len(col) for col in row]
        else:
            widths = [max(width, len(col)) for (width, col) in
                      zip(widths, row)]

    # Yield the rows
    for row in rows:
        if isinstance(row, (list, tuple)):
            line = "  ".join(p.ljust(width) for (width, p) in zip(widths, row))
            yield line
        else:
            yield row
