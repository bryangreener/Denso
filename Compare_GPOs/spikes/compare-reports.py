"""This program updates an html GPO report, highlighting comparisons."""
# AUTHOR: Bryan Greener
# COMPANY: Denso
# DATE: 2018-07-10
# See readme in repo root for license info.

from urllib.request import urlopen
from pathlib import Path
import argparse
from bs4 import BeautifulSoup

#### TODO
#    Fix parsing of nested tables.
#    Clean up code and comment more.
#    Reduce repeated loops

class Tree(object):
    """ Tree object used to create n-ary tree. """
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

def build_tree(soup, root, leaf_list):
    """ Initialize tree and call recursive build function """
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
    """ Recursively build tree """
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
            # List of all leaf nodes to make comparison easier
            leaf_list.append(child)

            #### FIXME
            # Need to account for sub-tables recursively.
            # Populate table of data at leaf node
            tables = content.find_all('table')
            build_tree_util_add_table(child, tables)
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

def build_tree_util_add_table(root, tables):
    """ Helper for build_tree that adds tables to nodes """
    root.table.append(tables)
    for table in tables:
        for row in table.find_all('tr'):
            if table is not None:
                if row.find_all('th'):
                    col = row.find_all('th')
                else:
                    col = row.find_all('td')
                root.table.append([x.string for x in col])

def compare_trees(leaf_list1, leaf_list2):
    """ Element-wise comparison between both trees going both directions. """
    comparisons = []
    for i in leaf_list1:
        for j in leaf_list2:
            if i.path == j.path: #verify using same setting
                # Below checks duplicate settings based on rules below
                #1 = setting exists in GPO1 but not in GPO2
                #2 = setting exists in GPO2 but not in GPO1
                #= = setting is equal in both
                #! = setting exists in both but has different value
                results = []
                for row_i in i.table[1:]:
                    for row_j in j.table[1:]:
                        if row_j[0] in [x[0] for x in i.table[1:]]:
                            if row_j == i.table[1:][
                                    [x[0] for x
                                     in i.table[1:]].index(row_j[0])]:
                                results.append([row_j[0], '='])
                                update_html_tables(i.table[0], row_j, '=')
                            else:
                                results.append([row_j[0], '!'])
                                update_html_tables(i.table[0], row_j, '!')
                        else:
                            results.append([row_j[0], 1])
                            update_html_tables(i.table[0], row_j, '1')
                for row_j in j.table[1:]:
                    for row_i in i.table[1:]:
                        if row_i[0] in  [x[0] for x in j.table[1:]]:
                            if row_i == j.table[1:][
                                    [x[0] for x
                                     in j.table[1:]].index(row_i[0])]:
                                results.append([row_i[0], '='])
                                update_html_tables(i.table[0], row_i, '=')
                            else:
                                results.append([row_i[0], '!'])
                                update_html_tables(i.table[0], row_i, '!')
                        else:
                            results.append([row_i[0], 2])
                            update_html_tables(i.table[0], row_i, 2)
                # Remove duplicates created by process above
                temp = []
                for res in results:
                    if res not in temp and res[0] is not None:
                        temp.append(res)
                if temp:
                    comparisons.append([i, temp])
                    i.comparisons = comparisons[-1]
    return comparisons

def update_html_tables(tables, row, comparison):
    """ Update tables in HTML with color codes. """
    for t_row in [table.find_all('tr') for table in tables]:
        if row[0] in [x.string for x in t_row.find_all('th')]:
            return # Skip headers
        if row[0] in [x.string for x in t_row.find_all('td')]:
            if str(comparison) == '1':
                t_row['style'] = 'background:#BB8FCE'
            elif str(comparison) == '2':
                t_row['style'] = 'background:#F1948A'
            elif str(comparison) == '!':
                t_row['style'] = 'background:#F7DC6F'
            elif str(comparison) == '=':
                t_row['style'] = 'background:#82E0AA'
            return
    # If row doesnt exist in html 1, add row.
    soup = BeautifulSoup('', 'lxml')
    new_tr = soup.new_tag('tr')
    for i in row:
        new_td = soup.new_tag('td')
        if i:
            new_td.string = i
        else:
            new_td.string = ''
        new_tr.append(new_td)
        if str(comparison) == '1':
            new_tr['style'] = 'background:#BB8FCE'
        elif str(comparison) == '2':
            new_tr['style'] = 'background:#F1948A'
    tables[0].append(new_tr)

def update_html_general_section(soup, gpo1, gpo2):
    """ Update HTML General section with color key and remove other info """
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
    """ Update HTML by deleting all sections not included in comparison """
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
    """ Util which recursively builds path_list """
    if root.path:
        path_list.append(root.path)
    for child in root.children:
        update_html_delete_extra_util(child, path_list)

def print_comparison(comparisons, outfile, quiet=False):
    """ Print comparison results for each leaf node """
    with open(outfile, 'a') as o_file:
        o_file.write('================\n'
                   'COMPARISONS ONLY\n'
                   '================\n')
        # Get longest string in comparisons (used for ljust)
        for i in comparisons:
            if not quiet:
                print([x for x in reversed(i[0].path)])
            o_file.write('{}\n'.format([x for x in reversed(i[0].path)]))
            max_length = max([x for y in [
                [[len(str(c)) for c
                  in b] for b in a] for a in i[1:]] for x in y])[0]
            for j in i[1:][0]:
                temp_j = j[0]
                j[0] = j[0].ljust(max_length + 1, '-')
                if not quiet:
                    print("\t", '| '.join(str(x) for x in j))
                o_file.write('\t{}\n'.format('| '.join(str(x) for x in j)))
                j[0] = temp_j
            if not quiet:
                print('')
            o_file.write('\n')

def print_tree(root, indent, last, outfile, quiet=False):
    """
    Print tree structure for testing and validation of tree building process.
    Modified from:
    stackoverflow.com/questions/1649027/how-do-i-print-out-a-tree-structure
    """
    out_str = ("%s +- %s" % (indent, root.name))
    if not quiet:
        print(out_str)
    with open(outfile, 'a') as o_file:
        o_file.write(out_str)
    if root.is_leaf:
        for i in root.comparisons[1:]:
            # Longest str len in output used for padding
            max_length = max([[len(str(x)) for x in y] for y in i])[0]
            for j in i:
                temp_j = j[0]
                j[0] = j[0].ljust(max_length + 1, '-')
                out_str = "%s    -> %s" % (indent, '| '.join(str(x) for x
                                                             in j))
                if not quiet:
                    print(out_str)
                with open(outfile, 'a') as o_file:
                    o_file.write(out_str)
                j[0] = temp_j
    indent += "   " if last else "|  "
    for i in range(len(root.children)):
        print_tree(root.children[i], indent, i == len(root.children)-1,
                   outfile, quiet)

if __name__ == '__main__':
    # Lists used to store all leaf nodes. Makes life easier in comparison.
    LEAF_LIST1 = []
    LEAF_LIST2 = []

    # =================
    # Argument Handling
    # =================

    PARSER = argparse.ArgumentParser(description='Compare two GPOs.')
    PARSER.add_argument('gpos', nargs=2,
                        help='Two GPO .html file paths to compare.')
    PARSER.add_argument('-o', '--output', default='comparison_output.txt',
                        help='Filepath in which to save results.')
    PARSER.add_argument('-q', '--quiet', action='store_true',
                        help='Boolean switch to suppress command line output.')
    ARGS = PARSER.parse_args()

    # ================
    # Input Validation
    # ================

    if Path(ARGS.gpos[0]).exists():
        URL1 = "file:" + ARGS.gpos[0]
    else:
        raise OSError('GPO file {} does not exist.'.format(ARGS.gpos[0]))
    if Path(ARGS.gpos[1]).exists():
        URL2 = "file:" + ARGS.gpos[1]
    else:
        raise OSError('GPO file {} does not exist.'.format(ARGS.gpos[1]))

    # =================
    # Output Validation
    # =================

    OUTFILE = ARGS.output
    try:
        with open(OUTFILE, 'w') as file:
            file.write('')
    except IOError:
        print('Output file error for {}.'.format(OUTFILE))

    # ==================
    # BS4 Initialization
    # ==================

    RESPONSE1 = urlopen(URL1).read()
    SOUP1 = BeautifulSoup(RESPONSE1, 'lxml')
    BODY1 = SOUP1.find('body')

    RESPONSE2 = urlopen(URL2).read()
    SOUP2 = BeautifulSoup(RESPONSE2, 'lxml')
    BODY2 = SOUP2.find('body')

    # ===============
    # Tree Generation
    # ===============

    ROOT = Tree()
    ROOT.name = URL1 + ' v ' + URL2
    TREE1, LEAF_LIST1 = build_tree(BODY1, ROOT, LEAF_LIST1)

    ROOT = Tree()
    ROOT.name = URL2 + ' v ' + URL1
    TREE2, LEAF_LIST2 = build_tree(BODY2, ROOT, LEAF_LIST2)

    # Compare the two trees and update their node contents.
    COMPARISON = compare_trees(LEAF_LIST1, LEAF_LIST2)

    # ===============
    # HTML Generation
    # ===============

    update_html_general_section(SOUP1, ARGS.gpos[0], ARGS.gpos[1])
    update_html_delete_extra_util(SOUP1, TREE1)

    HTML_OUT = SOUP1.prettify('utf-8')
    with open('updated_{}'.format(ARGS.gpos[0]), 'wb') as file:
        file.write(HTML_OUT)

    # ================
    # Text File Output
    # ================

    with open(OUTFILE, 'w') as file:
        file.write('KEY\n'
                   'GPO1: {}\n'.format(URL1) +
                   'GPO2: {}\n'.format(URL2) +
                   '1: Setting exists in GPO1 but not in GPO2\n'
                   '2: Setting exists in GPO2 but not in GPO1\n'
                   '=: Setting is the same in both GPOs\n'
                   '!: Setting exists in both GPOs but has different values\n'
                   '_______________________________________________________\n')
    print_tree(TREE1, '', True, OUTFILE, ARGS.quiet)
    print_comparison(COMPARISON, OUTFILE, ARGS.quiet)
