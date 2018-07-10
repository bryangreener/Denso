# AUTHOR: Bryan Greener
# COMPANY: Denso
# DATE: 2018-07-10
# See readme in repo root for license info.
from bs4 import BeautifulSoup
from urllib.request import urlopen

# Tree object used to create n-ary tree
class Tree(object):
    def __init__(self):
        self.data = None
        self.name = None
        self.inner_HTML = None
        self.parent = None
        self.is_leaf = False
        self.children = []
        self.table = []
        self.path = None

# Initialize tree and call recursive build function
def build_tree(soup, file_name, leaf_list):
    root = Tree()
    
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

# Print tree structure for testing and validation of tree building process.
#https://stackoverflow.com/questions/1649027/how-do-i-print-out-a-tree-structure
def print_tree(root, indent, last):
    print("%s +- %s" % (indent, root.name))
    indent += "   " if last else "|  "
    for i in range(len(root.children)):
        print_tree(root.children[i], indent, i == len(root.children)-1)
    
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
                    if r not in temp:
                        temp.append(r)
                comparisons.append([ii, temp])
    return comparisons

def print_comparison(comparisons):
    for i in comparisons:
        print([x for x in reversed(i[0].path)])
        for j in i[1:]:
            for k in j:
                print("\t", k)
        print("_____________________________________________________________")

# Edit with two filenames to compare
url1 = "file:GPO1.html"
url2 = "file:GPO2.html"

response1 = urlopen(url1).read()
soup1 = BeautifulSoup(response1, 'lxml').find('body')

response2 = urlopen(url2).read()
soup2 = BeautifulSoup(response2, 'lxml').find('body')

# Lists used to store all leaf nodes. Makes life easier in comparison.
leaf_list1 = []
leaf_list2 = []

tree1, leaf_list1 = build_tree(soup1, url1, leaf_list1)
tree2, leaf_list2 = build_tree(soup2, url2, leaf_list2)

#used for testing. prints structure.
#print_tree(tree1, '', True)
#print_tree(tree2, '', True)

comparison = compare_trees(leaf_list1, leaf_list2)
print_comparison(comparison)
    
