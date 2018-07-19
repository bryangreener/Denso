# AUTHOR: Bryan Greener
# COMPANY: Denso
# DATE: 2018-07-10
# See readme in repo root for license info.

from bs4 import BeautifulSoup
from urllib.request import urlopen
from pathlib import Path

import argparse

#### TODO
#    Fix parsing of nested tables.
#    Clean up code and comment more.


# Tree object used to create n-ary tree
class Tree(object):
    def __init__(self):
        # Full HTML of container
        self.data = None
        # String property of spans
        self.name = None
        # Full HTML of innermost divs for testing
        self.inner_HTML = None
        # Tree object for upward mobility in tree
        self.parent = None
        self.is_leaf = False
        # List of Tree objects
        self.children = []
        # 2D list of table data
        self.table = []
        # 2D list of table data comparisons
        self.comparisons = []
        # List of all parent node names up to root of tree
        self.path = None

# Initialize tree and call recursive build function
def build_tree(soup, root, leaf_list):
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

# Recursively build tree
def build_tree_util(root, leaf_list):
    for child in root.children:
        content = child.data.parent.find_next_sibling('div', class_='container')
        siblings = content.next_element.find_next_siblings('div', class_='container')
        # If at leaf node...
        if not siblings:
            child.is_leaf = True
            # Remove all newline chars from inner_HTML to sanitize environment
            child.inner_HTML = str(content).replace('\n', '')
            # List of all leaf nodes to make comparison easier
            leaf_list.append(child)
            
            #### FIXME
            #### Need to account for sub-tables recursively.
            # Populate table of data at leaf node
            tables = content.find_all('table')
            child.table.append(tables)
            for table in tables:
                if table is not None:
                    for row in table.find_all('tr'):
                        if row.find_all('th'):
                            col = row.find_all('th')
                        else:
                            col = row.find_all('td')
                        child.table.append([x.string for x in col])
        else: #otherwise add child nodes
            for i in siblings:
                child.children.append(Tree())
                child.children[-1].parent = child
                child.children[-1].data = i.find_previous_sibling('div').find_next('span', class_='sectionTitle')
                child.children[-1].name = child.children[-1].data.string
                
        # Populate path to root for node (makes life easier later)
        temp = child
        temp_list = []
        while temp.parent:
            temp_list.append(temp.name)
            temp = temp.parent
        child.path = temp_list
            
        build_tree_util(child, leaf_list)

# Element-wise comparison between both trees going both directions.
def compare_trees(leaf_list1, leaf_list2):
    comparisons = []
    for i, ii in enumerate(leaf_list1):
        for j, jj in enumerate(leaf_list2):
            if ii.path == jj.path: #verify using same setting
                # Below checks duplicate settings based on rules below
                #1 = setting exists in GPO1 but not in GPO2
                #2 = setting exists in GPO2 but not in GPO1
                #= = setting is equal in both
                #! = setting exists in both but has different value
                results = []
                for row_i in ii.table[1:]:
                    for row_j in jj.table[1:]:
                        if row_j[0] in [x[0] for x in ii.table[1:]]:
                            if row_j == ii.table[1:][[x[0] for x in ii.table[1:]].index(row_j[0])]:
                                results.append([row_j[0], '='])
                                update_html(ii.table[0], row_j, '=')
                            else:
                                results.append([row_j[0], '!'])
                                update_html(ii.table[0], row_j, '!')
                        else:
                            results.append([row_j[0], 1])
                            update_html(ii.table[0], row_j, '1')
                for row_j in jj.table[1:]:
                    for row_i in ii.table[1:]:
                        if row_i[0] in  [x[0] for x in jj.table[1:]]:
                            if row_i == jj.table[1:][[x[0] for x in jj.table[1:]].index(row_i[0])]:
                                results.append([row_i[0], '='])
                                update_html(ii.table[0], row_i, '=')
                            else:
                                results.append([row_i[0], '!'])
                                update_html(ii.table[0], row_i, '!')
                        else:
                            results.append([row_i[0], 2])
                            update_html(ii.table[0], row_i, 2)
                # Remove duplicates created by process above
                temp = []
                for r in results:
                    if r not in temp and r[0] is not None:
                        temp.append(r)
                if temp:
                    comparisons.append([ii, temp])
                    ii.comparisons = comparisons[-1]
    return comparisons

def update_html(tables, row, comparison):
    for table in tables:
        for r in table.find_all('tr'):
            if row[0] in [x.string for x in r.find_all('th')]:
                return # Skip headers
            if row[0] in [x.string for x in r.find_all('td')]:
                if str(comparison) == '1':
                    r['style'] = 'background:#BB8FCE'
                elif str(comparison) == '2':
                    r['style'] = 'background:#F1948A'
                elif str(comparison) == '!':
                    r['style'] = 'background:#F7DC6F'
                elif str(comparison) == '=':
                    r['style'] = 'background:#82E0AA'
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
    s = soup.find('div', class_='gposummary')
    s = s.next_element.find_next_sibling('div', class_='container')
    # Delete useless fields, leaving first table in details section.
    for i in [x for x in s.next_element.find_next_sibling('div', class_='container').next_siblings]:
        if i == '\n':
            i = ''
        else:
            i.decompose()
    
    t = s.find('table')
    s = t.parent
    # Delete old table.
    t.decompose()
    
    soup = BeautifulSoup('', 'lxml')
    class_attr = {'class': 'info3', 'style': 'width:auto'}
    table = soup.new_tag('table', **class_attr)
    # Headers for GPO titles
    tr = soup.new_tag('tr')
    td = soup.new_tag('th', scope='col')
    td.string = "GPO 1"
    tr.append(td)
    td = soup.new_tag('th', scope='col')
    td.string = "GPO 2"
    tr.append(td)
    table.append(tr)
    # Row for GPO titles
    tr = soup.new_tag('tr')
    td = soup.new_tag('td')
    td.string = gpo1
    tr.append(td)
    td = soup.new_tag('td')
    td.string = gpo2
    tr.append(td)
    table.append(tr)
    
    s.append(table)
    
    table = soup.new_tag('table', **class_attr)
    # Header for color key
    tr = soup.new_tag('tr')
    td = soup.new_tag('th', scope='col')
    td.string = "Color Key"
    tr.append(td)
    table.append(tr)
    # Rows for colors
    #ROW 1
    tr = soup.new_tag('tr')
    td = soup.new_tag('td', style='background:#F1948A')
    td.string = "Setting exists in GPO 1 but not in GPO 2."
    tr.append(td)
    table.append(tr)
    #ROW 2
    tr = soup.new_tag('tr')
    td = soup.new_tag('td', style='background:#BB8FCE')
    td.string = "Setting exists in GPO 2 but not in GPO 1."
    tr.append(td)
    table.append(tr)
    #ROW 3
    tr = soup.new_tag('tr')
    td = soup.new_tag('td', style='background:#F7DC6F')
    td.string = "Setting exists in both GPOs but has a different value."
    tr.append(td)
    table.append(tr)
    #ROW 4
    tr = soup.new_tag('tr')
    td = soup.new_tag('td', style='background:#82E0AA')
    td.string = "Setting is the same in both GPOs."
    tr.append(td)
    table.append(tr)
    
    s.append(table)
    
def update_html_delete_extra(soup, root1, root2):
    soup = soup.find('span', text='Computer Configuration (Enabled)').parent
    pl1, pl2 = [], []
    update_html_delete_extra_util(root1, pl1)
    update_html_delete_extra_util(root2, pl2)
    pl1 = set([tuple(x) for x in pl1])
    pl2 = set([tuple(x) for x in pl2])
    # List of paths to be deleted from html
    path_list = list((pl1 - pl2).union(pl2 - pl1))
    s = [x.find_all('span', class_='sectionTitle') for x in soup.next_siblings if x != '\n']
    s_list = [x for y in s for x in y]
    to_del = [x[0].parent.parent for x in path_list if x[0] in [y.text for y in s_list]]
    for d in to_del:
        temp = d.find_next_sibling('div', class_='container')
        if temp:
            temp.decompose()
        d.decompose()
        
def update_html_delete_extra_util(root, path_list):
    if root.path:
        path_list.append(root.path)
    for c in root.children:
        update_html_delete_extra_util(c, path_list)
    
# Print comparison results for each leaf node.
def print_comparison(comparisons, outfile, quiet=False):
    with open(outfile, 'a') as file:
        file.write('================\n'
                   'COMPARISONS ONLY\n'
                   '================\n')
        # Get longest string in comparisons (used for ljust)
        for i in comparisons:
            if not quiet:
                print([x for x in reversed(i[0].path)])
            file.write('{}\n'.format([x for x in reversed(i[0].path)]))
            max_length = max([x for y in [[[len(str(c)) for c in b] for b in a] for a in i[1:]] for x in y])[0]
            for j in i[1:][0]:
                s = j[0]
                j[0] = j[0].ljust(max_length + 1, '-')
                if not quiet:
                    print("\t", '| '.join(str(x) for x in j))
                file.write('\t{}\n'.format('| '.join(str(x) for x in j)))
                j[0] = s
            if not quiet:
                print('')
            file.write('\n')

# Print tree structure for testing and validation of tree building process.
# Modified from:
# stackoverflow.com/questions/1649027/how-do-i-print-out-a-tree-structure
def print_tree(root, indent, last, outfile, quiet=False):
    out_str = ("%s +- %s" % (indent, root.name))
    if not quiet:
        print(out_str)
    with open(outfile, 'a') as file:
        file.write(out_str)
    if root.is_leaf:
        for i in root.comparisons[1:]:
            # Longest str len in output used for padding
            max_length = max([[len(str(x)) for x in y] for y in i])[0]
            for j in i:
                s = j[0]
                j[0] = j[0].ljust(max_length + 1, '-')
                out_str = "%s    -> %s" % (indent,'| '.join(str(x) for x in j))
                if not quiet:
                    print(out_str)
                with open(outfile, 'a') as file:
                    file.write(out_str)
                j[0] = s
    indent += "   " if last else "|  "
    for i in range(len(root.children)):
        print_tree(root.children[i], indent, i == len(root.children)-1, 
                   outfile, quiet)

# =============================================================================
# =============================================================================
if __name__ == '__main__':
    # Lists used to store all leaf nodes. Makes life easier in comparison.
    leaf_list1 = []
    leaf_list2 = []
    
    # =================
    # Argument Handling
    # =================
    parser = argparse.ArgumentParser(description='Compare two GPOs.')
    parser.add_argument('gpos', nargs=2, 
                        help='Two GPO .html file paths to compare.')
    parser.add_argument('-o', '--output', default='comparison_output.txt',
                        help='Filepath in which to save results.')
    parser.add_argument('-q', '--quiet', action='store_true',
                        help='Boolean switch to suppress command line output.')
    args = parser.parse_args()
    
    # ================
    # Input Validation
    # ================
    
    if Path(args.gpos[0]).exists():
        url1 = "file:" + args.gpos[0]
    else:
        raise OSError('GPO file {} does not exist.'.format(args.gpos[0]))
    if Path(args.gpos[1]).exists():
        url2 = "file:" + args.gpos[1]
    else:
        raise OSError('GPO file {} does not exist.'.format(args.gpos[1]))
    
    # =================
    # Output Validation
    # =================
    
    outfile = args.output
    try:
        with open(outfile, 'w') as file:
            file.write('')
    except IOError:
        print('Output file error for {}.'.format(outfile))
    
    # ==================
    # BS4 Initialization
    # ==================
    
    response1 = urlopen(url1).read()
    soup1 = BeautifulSoup(response1, 'lxml')
    body1 = soup1.find('body')
    
    response2 = urlopen(url2).read()
    soup2 = BeautifulSoup(response2, 'lxml')
    body2 = soup2.find('body')
    
    
    
    # ===============
    # Tree Generation
    # ===============
    
    root = Tree()
    root.name = url1 + ' v ' + url2
    tree1, leaf_list1 = build_tree(body1, root, leaf_list1)
    
    root = Tree()
    root.name = url2 + ' v ' + url1
    tree2, leaf_list2 = build_tree(body2, root, leaf_list2)
    
    # Compare the two trees and update their node contents.
    comparison = compare_trees(leaf_list1, leaf_list2)
    
    # ===============
    # HTML Generation
    # ===============
    
    update_html_general_section(soup1, args.gpos[0], args.gpos[1])
    update_html_delete_extra_util(soup1, tree1, tree2)
    
    html_out = soup1.prettify('utf-8')
    with open('updated_{}'.format(args.gpos[0]), 'wb') as file:
        file.write(html_out)
        
    # ================
    # Text File Output
    # ================
    
    with open(outfile, 'w') as file:
        file.write('KEY\n'
                   'GPO1: {}\n'.format(url1) +
                   'GPO2: {}\n'.format(url2) +
                   '1: Setting exists in GPO1 but not in GPO2\n'
                   '2: Setting exists in GPO2 but not in GPO1\n'
                   '=: Setting is the same in both GPOs\n'
                   '!: Setting exists in both GPOs but has different values.\n'
                   '________________________________________________________\n')
        
    print_tree(tree1, '', True, outfile, args.quiet)
    print_comparison(comparison, outfile, args.quiet)
