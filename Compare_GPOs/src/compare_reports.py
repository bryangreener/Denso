""" Report Comparison Tool

This program takes two .html GPO reports generated by using 'save report' in
GPMC or by using Get-GPOReport in powershell. It then compares every setting
in these two files and generates an HTML file highlighting similarities and
differences between these two GPOs. A text file output is also generated
which shows the same information but in a slightly different format.

Example:
    Perform comparison and generate all forms of output including console
    output for report files at the two relative paths specified.

        C:/> compare_reports.exe gpo1.html gpo2.html

    Perform comparison and only generate the html file output for the
    two report files (one relative path and one absolute path) specified.

        C:/> compare_reports.exe gpo1.html C:/Temp/gpo2.html -q -O

Todo:
    * Verify results in-depth.
    * Clean up code and documentation.
    * Improve efficiency of algorithms.
"""

__author__ = "Bryan Greener"
__email__ = "bryan.greener@denso-diam.com"
__license__ = "See readme in repo root for license info."
__version__ = "1.1.0"
__date__ = "2018-08-01"
__status__ = "Prototype"

import re
import argparse
import urllib.error
from urllib.request import urlopen
from pathlib import Path
from bs4 import BeautifulSoup

class Tree(object):
    """Tree object class used to create n-ary tree nodes."""
    # pylint: disable=too-many-instance-attributes
    # pylint: disable=too-few-public-methods
    def __init__(self):
        self.data = None # Full HTML of container
        self.name = None # String property of spans
        self.inner_html = None # Full HTML of innermost divs for testing
        self.parent = None # Tree object for upward mobility in tree
        self.is_leaf = False
        self.children = [] # List of Tree objects
        self.table = [] # 2D list of table data
        self.comparisons = [] # 2D list of table data comparisons
        self.path = None # List of all parent node names up to root of tree

class Table(object):
    """Table object class used to store table information."""
    # pylint: disable=too-few-public-methods
    def __init__(self, html=None, tags=None, name=None):
        self.html = html
        self.tags = tags
        self.name = name
        self.table = []
        self.paired_tag = None

def build_tree(soup, root, leaf_list):
    """Initialize tree and call recursive build function."""
    # Manually add these entries as they exist in every GPO report.
    c_config = soup.find('span', text='Computer Configuration (Enabled)')
    u_config = soup.find('span', text='User Configuration (Enabled)')

    if c_config:
        c_node = Tree()
        c_node.data = c_config
        c_node.name = c_config.string
        c_node.parent = root
        root.children.append(c_node)

    if u_config:
        u_node = Tree()
        u_node.data = u_config
        u_node.name = u_config.string
        u_node.parent = root
        root.children.append(u_node)

    build_tree_util(root, leaf_list)
    return root, leaf_list

def build_tree_util(root, leaf_list):
    """Recursively build tree."""
    for child in root.children:
        content = child.data.parent.find_next_sibling(
            'div', class_='container')
        siblings = content.next_element.find_next_siblings(
            'div', class_='container')
        # If at leaf node...
        if not siblings:
            child.is_leaf = True
            # Remove all newline chars from inner_html to sanitize environment
            child.inner_html = str(content).replace('\n', '')
            # Populate table of data at leaf node
            #tables = content.find_all('table')
            tables = [x for x
                      in content.find_all('table', recursive=False)]
            tables += [[x for x
                        in y.find_all('table', recursive=False)] for y
                       in content.find_all('div', recursive=False)]
            if not tables:
                tables = content.find('table')
            if tables:
                child.table = [Table(html=x,
                                     tags=x['class'],
                                     name=x.find_previous_sibling('b')) for y
                               in tables for x in y
                               if x and y
                               and x != '\n' and y != '\n'
                               and x.has_attr('class')]
                for table in child.table:
                    # Create paired tag for comparisons util
                    if isinstance(table.html.previous_element, str):
                        table.paired_tag = table.html.previous_element
                    table.table = build_tree_util_add_table(table)
                # List of all leaf nodes to make comparison easier
                leaf_list.append(child)
        else: #otherwise add child nodes
            for i in siblings:
                child.children.append(Tree())
                child.children[-1].parent = child
                child.children[-1].data = i.find_previous_sibling(
                    'div').find_next('span', class_='sectionTitle')
                child.children[-1].name = child.children[-1].data.string
        # Populate path to root for node (makes life easier later)
        temp = child
        temp_list = []
        while temp.parent:
            temp_list.append(temp.name)
            temp = temp.parent
        child.path = temp_list
        build_tree_util(child, leaf_list)

def build_tree_util_add_table(table):
    """Helper for build_tree that adds tables to nodes."""
    for row in table.html.find_all('tr', recursive=False):
        temp_row = []
        for head in row.find_all('th', recursive=False):
            temp_row.append(head)
        for data in row.find_all('td', recursive=False):
            if data.find('table'):
                # Create new Table object and add to row
                temp_row.append(Table(html=data.find('table'),
                                      tags=data.find('table')['class']))
                # Get pair string for table and add to Table object
                temp_row[-1].paired_tag = pair_table(temp_row[-1].html)
                # Recursive call to catch sub-tables
                temp_row[-1].table = build_tree_util_add_table(temp_row[-1])
            else:
                temp_row.append(data)
        table.table.append(temp_row)
    return table.table

def pair_table(current_row):
    """Function to find an identifier element to identify a table."""
    # Find previous row that isnt a header and doesn't contain a table.
    previous_row = [x for x in current_row.find_all_previous('tr')
                    if x.find('td') and not x.find('td').find('table')][0]
    ret = str(previous_row.find_all('td')[0])
    # Remove any style tags in ret to prevent incorrect mismatching.
    return re.sub(r'style=\".*\"', '', ret)

def compare_trees(leaf_list1, leaf_list2):
    """Function to compare two trees which uses util function."""
    # ([a1,a2,..,an],[b1,b2,...,bn]) same settings in both tables
    temp_list = [x for x in [[y.table, z.table] for y
                             in leaf_list1 for z
                             in leaf_list2 if y.path == z.path]]
    # For each combination of like tables.
    for i, j in [c for d
                 in [[[a, b] for a in x for b in y
                      if a.name == b.name
                      and a.tags == b.tags
                      and a.paired_tag == b.paired_tag] for x, y
                     in temp_list] for c in d]:
        # i is table in table1 j is table in table2
        compare_trees_util(i, j)

def compare_trees_util(i, j):
    """Utility function that compares items in rows and updates style.
    Thought process here is to go row by row recursively through table1 and
    compare row to every row in table2, deleting table2 row matches afterwards.
    Finally, go through all remaining rows in table2 and add to table1 with
    color coding to show that this row doesn't exist in table1."""
    # pylint: disable=too-many-branches
    for row_i in i.table:
        if row_i[0].name == 'th':
            if row_i in j.table:
                continue #same table structure, skip header
            else:
                for row in i.table[1:]: #subtable only in table1
                    comparison_handler(1, row)
                return #not same table. skip
        # if table, recursive call
        elif isinstance(row_i[0], Table): #if row contains subtable
            if row_i[0].paired_tag:#compare paired tags in tables
                row_j = [x for x
                         in j.table if x[0].paired_tag == row_i[0].paired_tag]
                if row_j: #compare both subtables
                    compare_trees_util(row_i[0], row_j[0][0])
                else:
                    compare_trees_util(row_i[0], Table())
            else: #recursive call with subtable compared to nothing
                compare_trees_util(row_i[0], Table())
        elif row_i[0] in [x for y in j.table for x in y]: #if row in table2
            row_j = j.table[[x[0] for x in j.table].index(row_i[0])] #search
            # Ignore comment column if exists.
            if row_i == row_j or (row_i[:-1] == row_j[:-1] and \
                                  (i.table[0][0].name == 'th' and \
                                   'Comment' in i.table[0][-1])):
                comparison_handler(0, row_i)
            else: #same setting different values
                comparison_handler(3, row_i)
            # Delete from table2 to prevent overwriting
            del j.table[j.table.index(row_j)]
        else: # setting only exists in table1
            comparison_handler(1, row_i)
    # Clean up remaining items in table j. Similar to previous loop
    for row_j in j.table:
        if row_j and i.table:
            if row_j[0].name == 'th':
                if row_j in i.table:
                    continue
                else:
                    for row in j.table[1:]:
                        comparison_handler(2, row, i)
                    return
            elif isinstance(row_j[0], Table):
                compare_trees_util(Table(), row_j[0])
            else:
                comparison_handler(2, row_j, i)


def comparison_handler(comparison, row, table=None):
    """Util function to change style of rows in input table/rows."""
    if table and not table.html.name:
        return
    if row and not isinstance(row, list):
        row = [row] # Prevents issues with NavigableString elements
    if not isinstance(row[0], Table) and row[0].name and \
        not row[0].has_attr('style'):
        if comparison == 0: # same in both
            for data in row:
                data['style'] = 'background:#82E0AA'
        elif comparison == 1: # exists only in 1
            for data in row:
                data['style'] = 'background:#F1948A'
        elif comparison == 2: # exists only in 2
            # Need to add rows to table 1 for output
            soup = BeautifulSoup('', 'lxml')
            t_row = soup.new_tag('tr')
            for data in row:
                data['style'] = 'background:#BB8FCE'
                t_row.append(data)
            table.table.append(row)
            table.html.append(t_row)
        else: # exists but different
            for data in row:
                data['style'] = 'background:#F7DC6F'

def update_html_general_section(soup, gpo1, gpo2):
    """Update HTML General section with color key and remove other info."""
    # pylint: disable=too-many-statements
    summary = soup.find('div', class_='gposummary')
    summary = summary.next_element.find_next_sibling('div', class_='container')
    # Delete useless fields, leaving first table in details section.
    for i in [x for x in summary.next_element.find_next_sibling(
            'div', class_='container').next_siblings]:
        if i == '\n':
            i = ''
        else:
            i.decompose()

    tab = summary.find('table')
    summary = tab.parent
    # Delete old table.
    tab.decompose()

    soup = BeautifulSoup('', 'lxml')
    class_attr = {'class': 'info3', 'style': 'width:auto'}
    table = soup.new_tag('table', **class_attr)
    # Headers for GPO titles
    t_row = soup.new_tag('tr')
    t_dat = soup.new_tag('th', scope='col')
    t_dat.string = "GPO 1"
    t_row.append(t_dat)
    t_dat = soup.new_tag('th', scope='col')
    t_dat.string = "GPO 2"
    t_row.append(t_dat)
    table.append(t_row)
    # Row for GPO titles
    t_row = soup.new_tag('tr')
    t_dat = soup.new_tag('td')
    t_dat.string = gpo1
    t_row.append(t_dat)
    t_dat = soup.new_tag('td')
    t_dat.string = gpo2
    t_row.append(t_dat)
    table.append(t_row)

    summary.append(table)

    table = soup.new_tag('table', **class_attr)
    # Header for color key
    t_row = soup.new_tag('tr')
    t_dat = soup.new_tag('th', scope='col')
    t_dat.string = "Color Key"
    t_row.append(t_dat)
    table.append(t_row)
    # Rows for colors
    #ROW 1
    t_row = soup.new_tag('tr')
    t_dat = soup.new_tag('td', style='background:#F1948A')
    t_dat.string = "Setting exists in GPO 1 but not in GPO 2."
    t_row.append(t_dat)
    table.append(t_row)
    #ROW 2
    t_row = soup.new_tag('tr')
    t_dat = soup.new_tag('td', style='background:#BB8FCE')
    t_dat.string = "Setting exists in GPO 2 but not in GPO 1."
    t_row.append(t_dat)
    table.append(t_row)
    #ROW 3
    t_row = soup.new_tag('tr')
    t_dat = soup.new_tag('td', style='background:#F7DC6F')
    t_dat.string = "Setting exists in both GPOs but has a different value."
    t_row.append(t_dat)
    table.append(t_row)
    #ROW 4
    t_row = soup.new_tag('tr')
    t_dat = soup.new_tag('td', style='background:#82E0AA')
    t_dat.string = "Setting is the same in both GPOs."
    t_row.append(t_dat)
    table.append(t_row)

    summary.append(table)

def update_html_delete_extra(soup, root1, root2):
    """Update HTML by deleting all sections not included in comparison."""
    soup = soup.find('span', text='Computer Configuration (Enabled)').parent
    pl1, pl2 = [], []
    update_html_delete_extra_util(root1, pl1)
    update_html_delete_extra_util(root2, pl2)
    pl1 = set([tuple(x) for x in pl1])
    pl2 = set([tuple(x) for x in pl2])
    # List of paths to be deleted from html
    path_list = list((pl1 - pl2).union(pl2 - pl1))
    spans = [x.find_all('span', class_='sectionTitle') for x
             in soup.next_siblings if x != '\n']
    s_list = [x for y in spans for x in y]
    to_del = [x[0].parent.parent for x
              in path_list if x[0] in [y.text for y in s_list]]
    for t_d in to_del:
        temp = t_d.find_next_sibling('div', class_='container')
        if temp:
            temp.decompose()
        t_d.decompose()

def update_html_delete_extra_util(root, path_list):
    """Utility function which recursively builds path_list."""
    if root.path:
        path_list.append(root.path)
    for child in root.children:
        update_html_delete_extra_util(child, path_list)

if __name__ == '__main__':
    INPUT_FILES = []
    URL1, URL2, BIN = None, None, None
    # =================
    # Argument Handling
    # =================

    PARSER = argparse.ArgumentParser(
        description='Compare two GPO html report files.')
    PARSER.add_argument('bin_folder',
                        help='Path to bin folder containing html reports.')
    PARSER.add_argument('html_output',
                        help='Folder in which to save output reports.')
    PARSER.add_argument('--gpos', nargs=2, default=['', ''],
                        help='Two GPO .html file paths to compare.')
    ARGS = PARSER.parse_args()

    # ================
    # Input Validation
    # ================
    if ARGS.bin_folder and ARGS.html_output and ARGS.gpos[0] and ARGS.gpos[1]:
        PARSER.error('bin_folder, html_output, and two gpos specified. Only'
                     'specify bin_folder and html_output or specify two'
                     'gpos. Do not specify both sets.')
    if ARGS.bin_folder and ARGS.html_output:
        if Path(ARGS.bin_folder).exists():
            BIN = ARGS.bin_folder
            # Get all files in bin folder and create all combinations for comparison.
            INPUT_FILES = [p for p in Path(BIN).iterdir() if p.is_file() and
                           str(p).split('.')[-1] == 'html']
            INPUT_FILES = [x for x
                           in [("file:" + str(y),
                                "file:" + str(z),
                                ARGS.html_output + "\\" + "{}_vs_{}.html".format(
                                    y.name.split('.')[0],
                                    z.name.split('.')[0]).replace(
                                        ' ', '_')) for y
                               in INPUT_FILES for z
                               in INPUT_FILES if y != z]]
        else:
            raise OSError('Filepath {} does not exist.'.format(
                ARGS.bin_folder))
    elif ARGS.gpos[0] and ARGS.gpos[1]:
        if Path(ARGS.gpos[0]).exists():
            URL1 = "file:" + ARGS.gpos[0]
        else:
            raise OSError('GPO file {} does not exist.'.format(ARGS.gpos[0]))
        if Path(ARGS.gpos[1]).exists():
            URL2 = "file:" + ARGS.gpos[1]
        else:
            raise OSError('GPO file {} does not exist.'.format(ARGS.gpos[1]))

        INPUT_FILES = [(URL1, URL2, "{}_vs_{}.html".format(
            URL1.split('.')[0], URL2.split('.')[0]))]
    else:
        PARSER.error('Either both bin_folder and html_output, or '
                     'two gpo paths must be specified. Neither set '
                     'was specified')

    for URL1, URL2, HTML_OUTFILE in [x for x in INPUT_FILES]:
        # Lists used to store all leaf nodes. Makes life easier in comparison.
        LEAF_LIST1 = []
        LEAF_LIST2 = []
        print("START: {}".format(HTML_OUTFILE))
        # ==================
        # BS4 Initialization
        # ==================
        try: #Test first html file
            RESPONSE1 = urlopen(URL1).read()
            SOUP1 = BeautifulSoup(RESPONSE1, 'lxml')
        except urllib.error.HTTPError as ex:
            print('HTTPError: ' + str(ex.code))
        except urllib.error.URLError as ex:
            print('URLError: ' + str(ex.reason))
        except IOError as ex:
            print('IOError: ' + str(ex))

        try: # Test second html file
            RESPONSE2 = urlopen(URL2).read()
            SOUP2 = BeautifulSoup(RESPONSE2, 'lxml')
        except urllib.error.HTTPError as ex:
            print('HTTPError: ' + str(ex.code))
        except urllib.error.URLError as ex:
            print('URLError: ' + str(ex.reason))
        except IOError as ex:
            print('IOError: ' + str(ex))

        BODY1 = SOUP1.find('body')
        BODY2 = SOUP2.find('body')

        # ===============
        # Tree Generation
        # ===============
        ROOT = Tree()
        ROOT.name = URL1 + ' v ' + URL2
        TREE1, LEAF_LIST1 = build_tree(BODY1, ROOT, LEAF_LIST1)
        #print("FINISH TREE 1")

        ROOT = Tree()
        ROOT.name = URL2 + ' v ' + URL1
        TREE2, LEAF_LIST2 = build_tree(BODY2, ROOT, LEAF_LIST2)
        #print("FINISH TREE 2")

        # Compare the two trees and update their node contents.
        #COMPARISON = compare_trees(LEAF_LIST1, LEAF_LIST2)
        compare_trees(LEAF_LIST1, LEAF_LIST2)

        # ===============
        # HTML Generation
        # ===============
        try:
            update_html_general_section(SOUP1, URL1, URL2)
            update_html_delete_extra(SOUP1, TREE1, TREE2)

            HTML_OUT = SOUP1.prettify('utf-8')
            with open(HTML_OUTFILE, 'wb') as file:
                file.write(HTML_OUT)
        except IOError:
            print('Output file error for {}.'.format(HTML_OUTFILE))

        # =============
        # Clean Up Data
        # =============
        # This prevents slowdown over time from variables not being GC'd
        del SOUP1, SOUP2
        del RESPONSE1, RESPONSE2
        del BODY1, BODY2
        del ROOT
        del TREE1, TREE2
        del LEAF_LIST1[:], LEAF_LIST1, LEAF_LIST2[:], LEAF_LIST2
        del HTML_OUT
