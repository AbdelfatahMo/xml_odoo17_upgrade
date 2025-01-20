import os
import re
import xml.etree.ElementTree as ET


# Provide the directory path where your XML files are located
directory_path = "/home/dev/Desktop/Abdo/xml_odoo17_upgrade/account"


def iterate_xml_comments_substrings(input_string):
    # Define the regular expression pattern to match substrings
    pattern = r'<comment.*?/>'
    # Find all substrings matching the pattern
    for match in re.finditer(pattern, input_string):
        yield match.group()


def iterate_xml_comment_list_substrings(input_string):
    # Define the regular expression pattern to match substrings
    pattern = r'<!--.*?-->'
    # Find all substrings matching the pattern
    for match in re.finditer(pattern, input_string):
        yield match.group()

def convert_to_17_format(domain, operator):
    print(domain)
    # Get domain of invisible,readonly,, in attrs
    if type(domain) == bool:
        return f"{domain}"
    # If have one domain
    elif len(domain) == 1:
        field = domain[0][0]
        oper = domain[0][1]
        value = domain[0][2]
        value = f"'{value}'" if type(value) == str else value
        return f"{field} {operator[oper]} {value}"
    # If have more than one domain and don't have or operator
    elif len(domain) > 1 and '|' not in domain:
        converted = []
        for tuple in domain:
            if tuple == '&':
                continue
            field = tuple[0]
            oper = tuple[1]
            value = tuple[2]
            value = f"'{value}'" if type(value) == str else value
            converted.append(
                f"{field} {operator[oper]} {value}")
        return " and ".join(converted)
    # Manage complex domain
    else:
        converted = []
        counter = 0
        returned_value = ""
        domain_len = len(domain)
        or_cond = 0
        for item in domain:
            counter += 1
            if item == '|':
                or_cond += 1
            else:
                if item == '&':
                    continue
                field = item[0]
                oper = item[1]
                value = item[2]
                value = f"'{value}'" if type(value) == str else value
                if or_cond > 0:
                    returned_value += f"{field} {operator[oper]} {value} or "
                    or_cond -= 1
                else:
                    if counter == domain_len:
                        returned_value += f"{field} {operator[oper]} {value}"
                    else:
                        returned_value += f"{field} {operator[oper]} {value} and "
        return returned_value


def read_xml_files(directory):
    for directory_path, directory_names, filenames in os.walk(directory):
        for filename in filenames:
            if filename.endswith('.xml'):
                file_path = os.path.join(directory_path, filename)
                try:
                    comments = []
                    with open(file_path, 'r+') as file:
                        content = file.read()
                        comments = list(iterate_xml_comment_list_substrings(content))
                        counter = 0
                        for comment in comments:
                            counter += 1
                            content = content.replace(comment, f'<comment{counter} />')
                        file.seek(0)
                        file.write(content)
                        file.truncate()
                    # print("---------------------")
                    tree = ET.parse(file_path)
                    root_element = tree.getroot()
                    # Convert old operators
                    operator = {
                        '=': '==',
                        '&gt;=': '>=',
                        '&lt;=': '<=',
                        '&gt;': '>',
                        '&lt;': '<',
                        'in': 'in',
                        'not in': 'not in',
                        '!=': '!=',
                        '<': '<',
                        '>': '>',
                        '<>': '!=',
                        '>=': '>=',
                        '<=': '<='
                    }
                    parent = None
                    # Loop on every element on xml file
                    for elem in root_element.iter():
                        # If element has attrs attribute
                        # print(elem.attrib)
                        # get elem parent of attribute tag
                        if elem.attrib.get('position') == 'attributes':
                            parent = elem
                        if elem.tag == 'attribute' and elem.attrib.get('name') == 'attrs':
                            # print(elem.text)
                            dic = dict(eval(elem.text.replace(' ','')))
                            # print('xpath',dic)
                            for key in dic.keys():
                                new = ET.SubElement(parent,'attribute',{'name':str(key)})
                                new.text=convert_to_17_format(dic.get(key),operator)
                            parent.remove(elem)
                            # print(elem.attrib)
                            # print(elem.tag)
                            # print(eval(elem.text))
                            # print(type(eval(elem.text)))
                        if 'attrs' in elem.attrib.keys():
                            # Convert attrs to Dictionary
                            attrs = eval(elem.attrib.get("attrs"))
                            for key in attrs.keys():
                                # print("attrs",key ,attrs.get(key))
                                elem.attrib[key] = convert_to_17_format(attrs.get(key), operator)
                                # print("Converted")
                            # print(elem.attrib)
                            # Remove attrs
                            elem.attrib.pop('attrs')
                            # print(elem.attrib)
                        # Convert states to invisible and manage domain
                        if 'states' in elem.attrib.keys():
                            states = elem.attrib.get('states').split(',')
                            # Add domain with or condition to existing one generated from previous part
                            if 'invisible' in elem.attrib.keys():
                                elem.attrib['invisible'] +=  f" or state not in {states}"
                            else:
                                # Add invisible
                                elem.attrib['invisible'] = f"state not in {states}"
                            # Remove states
                            elem.attrib.pop('states')
                    # Save changes to file
                    tree.write(file_path)
                    with open(file_path, 'r+') as file:
                        content = file.read()
                        # print(file_path)
                        counter = 0
                        for comment in comments:
                            # print('----------------------------------',comment)
                            counter += 1
                            content = content.replace(
                                f'<comment{counter} />', comment)
                        file.seek(0)
                        file.write(
                            '<?xml version="1.0" encoding="utf-8"?>' + '\n' + content)
                        file.truncate()
                except Exception as e:
                    print(e, file_path)


read_xml_files(directory_path)


