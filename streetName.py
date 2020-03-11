### Classes for finding/improving street names

def is_street_name(elem):
    return (elem.attrib['k'] == "addr:street")


def update_street_name(name, mapping):
    
    name = string.capwords(name)
    m = street_type_re.search(name)
    
    if m:
        street_type = m.group()
        if street_type not in expected and street_type in mapping:
            name = re.sub(street_type_re, mapping[street_type], name)
    else:
        print("Odd Street Name: " % name)