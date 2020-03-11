### Custom classes for auditing street name data

import xml.etree.cElementTree as ET
from collections import defaultdict
import streetName
import pprint


street_types = defaultdict(set)

def audit(osm_file):
    
    for event, elem in ET.iterparse(osm_file, events=("start",)):

        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"):
                if is_street_name(tag):
                    audit_street_type(street_types, tag.attrib['v'])
    return street_types
    pprint.pprint(dict(street_types))
    
# Custom class for finding odd street names  
def audit_street_type(street_types, street_name):
    m = street_type_re.search(street_name)
    if m:
        street_type = m.group()
        if street_type not in expected:
            street_types[street_type].add(street_name)
            
# Custom class for correcting street names    
def fix_street(osm_file):
    street_types = audit(osm_file)
    print(street_types)
    for street_type, ways in street_types.items():
        for name in ways:
            if street_type in mapping:
                better_name = name.replace(street_type, mapping[street_type])
                print(name, "=>", better_name)
    pprint.pprint(dict(street_types))