import csv
import codecs
import pprint
import re
import xml.etree.cElementTree as ET

import cerberus

import schema


OSM_PATH = "map.osm"

NODES_PATH = "nodes.csv"
NODE_TAGS_PATH = "nodes_tags.csv"
WAYS_PATH = "ways.csv"
WAY_NODES_PATH = "ways_nodes.csv"
WAY_TAGS_PATH = "ways_tags.csv"

LOWER_COLON = re.compile(r'^([a-z]|_)+:([a-z]|_)+')
PROBLEMCHARS = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

SCHEMA = schema.schema

# Make sure the fields order in the csvs matches the column order in the sql table schema
NODE_FIELDS = ['id', 'lat', 'lon', 'user', 'uid', 'version', 'changeset', 'timestamp']
NODE_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_FIELDS = ['id', 'user', 'uid', 'version', 'changeset', 'timestamp']
WAY_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_NODES_FIELDS = ['id', 'node_id', 'position']


# Brought in functions written in Wrangle_osm to update street names and postcode

def shape_element(element, node_attr_fields=NODE_FIELDS, way_attr_fields=WAY_FIELDS,
                  problem_chars=PROBLEMCHARS, default_tag_type='regular'):
    
    node_attribs = {}
    way_attribs = {}
    way_nodes = []
    tags = []

    
    if element.tag == 'node':
        # Set value of each element attrib to be written into dictionary
        for field in NODE_FIELDS: 
            v_field = element.attrib[field]
            node_attribs[field] = v_field
            
            
        for child in element:
            tag = {}
            vk = child.attrib['k']
            tag['id'] = node_attribs['id']
            if PROBLEMCHARS.search(vk):
                continue
            elif LOWER_COLON.search(vk): 
                vk_split = vk.split(':', 1)
                tag['type'] = vk_split[0]
                tag['key'] = vk_split[1]
                tag['value'] = child.attrib['v']
            
            # Otherwise, assign attribute value to the keys accordingly
            else: 
                tag['key'] = vk
                tag['value'] = child.attrib['v']
                tag['type'] = default_tag_type

            
            tags.append(tag)
        
        return {'node': node_attribs, 'node_tags': tags}
        
    elif element.tag == 'way':

        # Set value of each element attrib to be written into dictionary
        for field in WAY_FIELDS:
            v_field = element.attrib[field]
            way_attribs[field] = v_field
        
        counter = 0
        for child in element:
            tag = {}
            if child.tag == 'tag':
                vk = child.attrib['k']
                tag['id'] = way_attribs['id']
                if PROBLEMCHARS.search(vk): #ignores all problemetic lines
                    continue
                # For k attribute containing ":", take the part before the 1st colon as type 
                #and the rest as key
                elif LOWER_COLON.search(vk): 
                    vk_split = vk.split(':', 1)
                    tag['type'] = vk_split[0]
                    tag['key'] = vk_split[1]
                    tag['value'] = child.attrib['v']
                
                # Otherwise, assign attribute value to the keys accordingly
                else: 
                    tag['key'] = vk
                    tag['value'] = child.attrib['v']
                    tag['type'] = default_tag_type

                
                tags.append(tag)
            
            if child.tag =='nd': #
                way_node = {}
                way_node['id'] = way_attribs['id']
                way_node['node_id'] = child.attrib['ref']
                way_node['position'] = counter
                counter += 1
                way_nodes.append(way_node)
                
        return {'way': way_attribs, 'way_nodes': way_nodes, 'way_tags': tags}


# Additional functions

def get_element(osm_file, tags=('node', 'way', 'relation')):
    
    context = ET.iterparse(osm_file, events=('start', 'end'))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()

# Raise Validation Error if element does not match schema
def validate_element(element, validator, schema=SCHEMA):
    
    if validator.validate(element, schema) is not True:
        field, errors = next(validator.errors.iteritems())
        message_string = "\nElement of type '{0}' has the following errors:\n{1}"
        error_string = pprint.pformat(errors)
        
        raise Exception(message_string.format(field, error_string))

# Extend csv.DictWriter so that it can handle unicode
class UnicodeDictWriter(csv.DictWriter, object):
    
    def writerow(self, row):
        super(UnicodeDictWriter, self).writerow({
            k: (v.encode('utf-8') if isinstance(v, unicode) else v) for k, v in row.items()
        })

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)


# Main Function for processing/converting
# Iteratively process each XML element and write to correspondin csv files
def process_map(file_in, validate):
    
    with codecs.open(NODES_PATH, 'w') as nodes_file, \
         codecs.open(NODE_TAGS_PATH, 'w') as nodes_tags_file, \
         codecs.open(WAYS_PATH, 'w') as ways_file, \
         codecs.open(WAY_NODES_PATH, 'w') as way_nodes_file, \
         codecs.open(WAY_TAGS_PATH, 'w') as way_tags_file:

        nodes_writer = UnicodeDictWriter(nodes_file, NODE_FIELDS)
        node_tags_writer = UnicodeDictWriter(nodes_tags_file, NODE_TAGS_FIELDS)
        ways_writer = UnicodeDictWriter(ways_file, WAY_FIELDS)
        way_nodes_writer = UnicodeDictWriter(way_nodes_file, WAY_NODES_FIELDS)
        way_tags_writer = UnicodeDictWriter(way_tags_file, WAY_TAGS_FIELDS)

        nodes_writer.writeheader()
        node_tags_writer.writeheader()
        ways_writer.writeheader()
        way_nodes_writer.writeheader()
        way_tags_writer.writeheader()

        validator = cerberus.Validator()

        for element in get_element(file_in, tags=('node', 'way')):
            x = shape_element(element)
            if x:
                if validate is True:
                    validate_element(el, validator)

                if element.tag == 'node':
                    nodes_writer.writerow(el['node'])
                    node_tags_writer.writerows(el['node_tags'])
                elif element.tag == 'way':
                    ways_writer.writerow(el['way'])
                    way_nodes_writer.writerows(el['way_nodes'])
                    way_tags_writer.writerows(el['way_tags'])


if __name__ == '__main__':
    # sample of the map when validating.
    process_map(OSM_PATH, validate=True)