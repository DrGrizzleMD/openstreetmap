# create a dictionary of tags with tag name as key and quantity of each tags as value

import xml.etree.cElementTree as ET

def count_tags(osm_file):
    tags = {}
        
    for event, elem in  ET.iterparse(osm_file): 
        if elem.tag in tags:
            tags[elem.tag] += 1
        else:
            tags[elem.tag] = 1
            
    return tags

        
def iter_parse():

    tags = count_tags(osm_file)
    pprint.pprint(tags)