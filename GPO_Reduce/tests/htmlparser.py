# AUTHOR: Bryan Greener
# COMPANY: Denso
# DATE: 2018-07-10
# See readme in repo root for license info.

from bs4 import BeautifulSoup
from urllib.request import urlopen
from xml.etree import ElementTree as ET
from pathlib import Path

import argparse

#### TODO
#    Update HTML generator to output prettier page.
#    Fix parsing of nested tables.
#    Clean up code and comment more.


# Tree object used to create n-ary tree
class Tree(object):
    def __init__(self):
        # Full HTML of container
        self.data = None
        # String property of spans
        self.name = None
        # Full HTML of innermost divs
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
def build_tree(soup, file_name, leaf_list):
    root = Tree()
    
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
    root.name = file_name
    
    build_tree_util(root, leaf_list)
    
    return root, leaf_list

# Recursively build tree
def build_tree_util(root, leaf_list):
    for child in root.children:
        content = child.data.parent.find_next_sibling('div', class_='container')
        # If at leaf node...
        if not content.next_element.find_next_siblings('div', class_='container'):
            child.is_leaf = True
            # Remove all newline chars from inner_HTML to sanitize environment
            child.inner_HTML = str(content).replace('\n', '')
            # List of all leaf nodes to make comparison easier
            leaf_list.append(child)
            # Populate path to root for leaf node (makes life easier later)
            temp = child
            temp_list = []
            while temp.parent:
                temp_list.append(temp.name)
                temp = temp.parent
            child.path = temp_list
            #### FIXME
            #### Need to account for subtables recursively.
            # Populate table of data at leaf node
            table = child.data.parent.find_next_sibling('div', class_='container').find('table')
            if table is not None:
                for row in table.find_all('tr'):
                    if row.find_all('th'):
                        col = row.find_all('th')
                    else:
                        col = row.find_all('td')
                    child.table.append([x.string for x in col])
        else: #otherwise add child nodes
            for i in content.next_element.find_next_siblings('div', class_='container'):
                child.children.append(Tree())
                child.children[-1].parent = child
                child.children[-1].data = i.find_previous_sibling('div').find_next('span', class_='sectionTitle')
                child.children[-1].name = child.children[-1].data.string
        build_tree_util(child, leaf_list)

# Element-wise comparison between both trees going both directions.
def compare_trees(leaf_list1, leaf_list2):
    comparisons = []
    for i, ii in enumerate(leaf_list1):
        for j, jj in enumerate(leaf_list2):
            if ii.path == jj.path: #verify using same setting
                # Below checks duplicate settings based on rules below
                #0 = setting doesn't exist in 2
                #1 = setting is equal in both
                #2 = setting exists in both but has different value
                results = []
                for row_i in ii.table:
                    for row_j in jj.table:
                        if row_j[0] in [x[0] for x in ii.table]:
                            if row_j == ii.table[[x[0] for x in ii.table].index(row_j[0])]:
                                results.append([row_j[0], 1])
                            else:
                                results.append([row_j[0], 2])
                        else:
                            results.append([row_j[0], 0])
                for row_j in jj.table:
                    for row_i in ii.table:
                        if row_i[0] in  [x[0] for x in jj.table]:
                            if row_i == jj.table[[x[0] for x in jj.table].index(row_i[0])]:
                                results.append([row_i[0], 1])
                            else:
                                results.append([row_i[0], 2])
                        else:
                            results.append([row_i[0], 0])
                # Remove duplicates created by process above
                temp = []
                for r in results:
                    if r not in temp and r[0] is not None:
                        temp.append(r)
                if temp:
                    comparisons.append([ii, temp])
                    ii.comparisons = comparisons[-1]
    return comparisons

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
    if not quiet: #quiet switch specified
        print("%s +- %s" % (indent, root.name))
    with open(outfile, 'a') as file:
        file.write("%s +- %s\n" % (indent, root.name)) #out to file
    if root.is_leaf:
        for i in root.comparisons[1:]:
            max_length = max([[len(str(x)) for x in y] for y in i])[0]
            for j in i:
                s = j[0]
                j[0] = j[0].ljust(max_length + 1, '-')
                if not quiet: #quiet switch specified
                    print("%s    -> %s" % 
                          (indent, '| '.join(str(x) for x in j)))
                with open(outfile, 'a') as file:
                    file.write("%s    -> %s\n" % (indent, '| '.join(str(x)for x in j)))
                j[0] = s
    indent += "   " if last else "|  "
    for i in range(len(root.children)):
        print_tree(root.children[i], indent, i == len(root.children)-1, 
                   outfile, quiet)

# Generate an html page to display results in a readable format.
def generate_html(root, outfile):
    html = ET.Element('html')
    head = ET.Element('head')
    body = ET.Element('body')
    link = ET.Element('link', attrib={'rel': 'stylesheet', 
                                      'type': 'text/css',
                                      'href': 'theme.css'})
    html.append(head)
    head.append(link)
    html.append(body)
    
    generate_html_util(root, body, html, outfile)

def generate_html_util(root, tag, html, outfile):
    for child in root.children:
        div = ET.Element('div', attrib={'class': 'node',
                                        'id': child.name})
        tag.append(div)
        span = ET.Element('span', attrib={'class': 'sectionTitle'})
        div.append(span)
        span.text = child.name
        
        if child.table:
            table = ET.Element('table', attrib={'class': 'info'})
            for row in child.table:
                tr = ET.Element('tr')
                for col in row:
                    td = ET.Element('td')
                    td.text = col
                    tr.append(td)
                if child.comparisons:
                    row_idx = [x[0] for x in child.comparisons[-1]].index(row[0])
                    td = ET.Element('td')
                    td.text = str(child.comparisons[-1][row_idx][-1])
                    tr.append(td)
                table.append(tr)
            div.append(table)
        
        generate_html_util(child, div, html, outfile)
    ET.ElementTree(html).write(outfile, encoding='utf8', method='html')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Compare two GPOs.')
    parser.add_argument('gpos', nargs=2, 
                        help='Two GPO .html file paths to compare.')
    parser.add_argument('-o', '--output', default='comparison_output.txt',
                        help='Filepath in which to save results.')
    parser.add_argument('-q', '--quiet', action='store_true',
                        help='Boolean switch to suppress command line output.')
    args = parser.parse_args()
    # Handle input file validation
    if Path(args.gpos[0]).exists():
        url1 = "file:" + args.gpos[0]
    else:
        raise OSError('GPO file {} does not exist.'.format(args.gpos[0]))
    if Path(args.gpos[1]).exists():
        url2 = "file:" + args.gpos[1]
    else:
        raise OSError('GPO file {} does not exist.'.format(args.gpos[1]))
    # Handle output file validation
    outfile = args.output
    try:
        with open(outfile, 'w') as file:
            file.write('')
    except IOError:
        print('Output file error for {}.'.format(outfile))
    
    response1 = urlopen(url1).read()
    soup1 = BeautifulSoup(response1, 'lxml').find('body')
    
    response2 = urlopen(url2).read()
    soup2 = BeautifulSoup(response2, 'lxml').find('body')
    
    # Lists used to store all leaf nodes. Makes life easier in comparison.
    leaf_list1 = []
    leaf_list2 = []
    
    tree1, leaf_list1 = build_tree(soup1, url1, leaf_list1)
    tree2, leaf_list2 = build_tree(soup2, url2, leaf_list2)
    
    comparison = compare_trees(leaf_list1, leaf_list2)
    # Overwrite file
    with open(outfile, 'w') as file:
        file.write('KEY:\n'
                   '0=Setting doesn\'t exist in second GPO.\n'
                   '1=Setting is the same in both GPOs.\n'
                   '2=Setting exists in both GPOs but has different value.\n'
                   '______________________________________________________\n')
    print_tree(tree1, '', True, outfile, args.quiet)
    
    print_comparison(comparison, outfile, args.quiet)
    
    html_outfile = 'html_output.html'
    try:
        with open(html_outfile, 'w') as file:
            file.write('')
    except IOError:
        print('HTML Output file error for {}.'.format(html_outfile))
    
    generate_html(tree1, html_outfile)