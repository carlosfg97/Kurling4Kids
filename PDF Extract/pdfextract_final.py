#!/usr/bin/env python
# coding: utf-8

# In[10]:


import fitz
import string
import pandas as pd
from difflib import SequenceMatcher
import re


# In[2]:


filepath_full = '../Data/REP-EDC-2020_Fusion_Final.pdf'


# In[51]:


class ExtractionToolSimple:
    #Initiator: 
    ##filepath
    def __init__(self, filepath):
        self.filepath = filepath
        
    def openPDFasTextDict(self):
        """
        Opens PDF as XML dict
        """
        text_dict = []
        with fitz.open(self.filepath) as doc:
            for page in doc:
                text_dict.append(page.get_text("dict", sort=False))
        self.text_dict = text_dict
        
    def inputStringstoRemove(self, banned_strings: list):
        while True:
            
            cont = input("Are there lines that you would like the extraction tool to avoid? Y/N")
            if cont not in ("Y","N"):
                print("Please type Y or N")
                continue
            if cont == "Y":   
                banned_strings.append(input("Please copy-paste the line here: "))
            if cont == "N":
                break
                
        self.banned_strings = banned_strings
        
    @staticmethod
    def removePuncandSpace(text):
        """
        Removes punctuation and spaces from a string
        Used in extractFromTextDict
        """
        return text.translate(str.maketrans('', '', string.punctuation)).strip()
    
    def extractFromTextDict(self):
        ##
        # Get an idea of looping through text
        # For every page
        # Extract additional information about the text as well: font and font size
        # Store in list of dictionaries
        ##
        bannedStrings = self.banned_strings
        org_list = []
        foundation_list = []
        org_id = -1
        foundation_id = -1
        charitable_foundation = False

        for count_page, page in enumerate(self.text_dict):
            for count_block_list, block_list in enumerate(page["blocks"]):
                for count_line_list, line_list in enumerate(block_list["lines"]):
                    for count_spans_list, spans_list in enumerate(line_list["spans"]):

                        #Remove empty text
                        if spans_list['text'].isspace():
                            continue
                        #Skip if trash text
                        if spans_list['text'].strip() in bannedStrings:
                            continue


                        ### Organizations ####
                        #Check if font & size are that of org number or new org
                        if (spans_list['font'] == 'Helvetica-Bold') & (int(float(spans_list['size'])) == 11):
                            charitable_foundation = False
                            #Check if start of new org
                            try :
                                #Throws ValueError if name of org
                                int(spans_list['text'])
                            except ValueError:
                                #Only triggers when name of org
                                org_list[org_id]['Name'] = spans_list['text'].strip()                   
                            else:
                                #If not name of org then org number
                                if (spans_list['font'] == 'Helvetica-Bold') & (int(float(spans_list['size'])) == 11):
                                    org_number = spans_list['text'].strip()
                                    org_list.append({'id' : org_number,
                                                     'isFoundation' : 'No'})
                                    org_id += 1

                        #Check if not in charitable organisation
                        if not charitable_foundation:

                            #Check if font & size are that of org address
                            #Uses round to filter more text: other text has size that rounds to 8
                            if (spans_list['font'] == 'Helvetica') & (round(float(spans_list['size'])) == 9):
                                #Catch if no orgs created
                                if org_id < 0:
                                    continue
                                #If key Address doesn't already exist, create it
                                if 'Address' not in org_list[org_id].keys():
                                    org_list[org_id]['Address'] = ''
                                    org_list[org_id]['Address'] += spans_list['text']
                                else:
                                    #Strip here to avoid unnecessary blank space
                                    #Maybe handle this later?
                                    org_list[org_id]['Address'] += spans_list['text'].strip()

                            #Check if font & size are that of field name
                            if (spans_list['font'] == 'ArialNarrow') & (int(float(spans_list['size'])) == 8):
                                #Catch if no orgs created
                                if org_id < 0:
                                    continue
                                #If key field doesn't already exist, create it. Checks if length string > 1 to remove bad text
                                if (ExtractionToolSimple.removePuncandSpace(spans_list['text']) not in org_list[org_id].keys()) & (len(ExtractionToolSimple.removePuncandSpace(spans_list['text'])) > 1):
                                    org_list[org_id][ExtractionToolSimple.removePuncandSpace(spans_list['text'])] = ''
                                #If field already exists, create new field with convention i - Name where i is number of fields with the same name +1
                                elif (ExtractionToolSimple.removePuncandSpace(spans_list['text']) in org_list[org_id].keys()):
                                    num_instances = list(org_list[org_id].keys()).count(ExtractionToolSimple.removePuncandSpace(spans_list['text']))
                                    org_list[org_id][f"{num_instances + 1} - {ExtractionToolSimple.removePuncandSpace(spans_list['text'])}"] = ''

                            #Check if font & size are that of field text
                            if (spans_list['font'] == 'Helvetica-Bold') & (round(float(spans_list['size'])) == 8):
                                #Catch if no orgs created
                                if org_id < 0:
                                    continue

                                #Place in last dict key: will always be something there, non-generalizable method
                                org_list[org_id][list( org_list[org_id])[-1]] += spans_list['text']

                        ### Foundations ####
                        #Check if text indicates charitable foundation
                        if (spans_list['font'] == 'ArialNarrow') & (round(float(spans_list['size'])) == 7) & (spans_list['text'][:23] == "L'entreprise possède un"): 

                            charitable_foundation = True

                            #Foundations always start with lines of Helvetica Bold.  
                            #Use that as a trigger with the boolean var start_foundation
                            start_foundation = True
                            foundation_list.append({'id' : org_number,
                                             'isFoundation' : 'Yes'})
                            foundation_id +=1

                        #Check if are in charitable foundation
                        if charitable_foundation:
                            #Trigger for name and address to differentiate from other text
                            if start_foundation:
                                #Check if font & size are foundation name
                                if (spans_list['font'] == 'Helvetica-Bold') & (round(float(spans_list['size'])) >= 9):
                                     #If key Name doesn't already exist, create it
                                    if 'Name' not in foundation_list[foundation_id].keys():
                                        foundation_list[foundation_id]['Name'] = ''
                                        foundation_list[foundation_id]['Name'] += spans_list['text']

                                        lineToSkip = count_line_list
                                    #else:
                                        #Strip here to avoid unnecessary blank space
                                        #foundation_list[foundation_id]['Name'] += spans_list['text'].strip()

                                #Check if font & size are address
                                if (spans_list['font'] == 'Helvetica-Bold') & ((round(float(spans_list['size'])) == 8) | (round(float(spans_list['size'])) >= 9)):
                                    #Check if are on different line than Name, meaning are on Address line
                                    if count_line_list > lineToSkip:
                                         #If key Address doesn't already exist, create it
                                        if 'Address' not in foundation_list[foundation_id].keys():
                                            foundation_list[foundation_id]['Address'] = ''
                                            foundation_list[foundation_id]['Address'] += spans_list['text'].strip()
                                        else:
                                            foundation_list[foundation_id]['Address'] += ' ' +spans_list['text'].strip()



                            #Check if font & size are that of field name
                            #Outside of if start_foundation
                            if ((spans_list['font'] == 'ArialNarrow') or (spans_list['font'] == 'Helvetica')) & (int(float(spans_list['size'])) == 8):
                                #Trigger on first catch of non-address text
                                start_foundation = False

                                #Catch if no orgs created
                                if foundation_id < 0:
                                    continue
                                #If key field doesn't already exist, create it. Checks if length string > 1 to remove bad text
                                if (ExtractionToolSimple.removePuncandSpace(spans_list['text']) not in foundation_list[foundation_id].keys()) & (len(ExtractionToolSimple.removePuncandSpace(spans_list['text'])) > 1):
                                    foundation_list[foundation_id][ExtractionToolSimple.removePuncandSpace(spans_list['text'])] = ''

                            #Check if outside of adress
                            if not start_foundation:
                                #Check if font & size are that of field text
                                if ((spans_list['font'] == 'ArialNarrow,Bold') or (spans_list['font'] == 'Helvetica-Bold')) & (round(float(spans_list['size'])) == 8):
                                    #Catch if no orgs created
                                    if foundation_id < 0:
                                        continue

                                    #Place in last dict key: will always be something there, non-generalizable method
                                    foundation_list[foundation_id][list( foundation_list[foundation_id])[-1]] += spans_list['text']

        return org_list, foundation_list


# In[9]:


class ExtractionToolComplex:
    #Initiator: 
    ##filepath
    def __init__(self, filepath):
        self.filepath = filepath
        
    def openPDFasTextDict(self):
        """
        Opens PDF as XML dict
        """
        text_dict = []
        with fitz.open(self.filepath) as doc:
            for page in doc:
                text_dict.append(page.get_text("dict", sort=False))
        self.text_dict = text_dict

    def inputStringstoRemove(self, banned_strings: list):
        while True:
            
            cont = input("Are there lines that you would like the extraction tool to avoid? Y/N")
            if cont not in ("Y","N"):
                print("Please type Y or N")
                continue
            if cont == "Y":   
                banned_strings.append(input("Please copy-paste the line here: "))
            if cont == "N":
                break
                
        self.banned_strings = banned_strings
        
    @staticmethod
    def removePuncandSpace(text):
        """
        Removes punctuation and spaces from a string
        Used in extractFromTextDict
        """
        return text.translate(str.maketrans('', '', string.punctuation)).strip()
    
    @staticmethod
    def isListEmpty(inList):
        if isinstance(inList, list): # Is a list
            return all( map(ExtractionToolComplex.isListEmpty, inList) )
        return False # Not a list
    
    def getFontInfo(self, text_dict = None):
        
        if text_dict is None:
            text_dict = self.text_dict
            
        foundation_present = input("Are there any charitable foundations present in your document? Y/N")    

        if foundation_present == 'Y':
            foundation_check = True
        if foundation_present == 'N':
            foundation_check = False

        company_name_acquired = False
        company_address_acquired = False
        company_field_acquired = False
        company_text_acquired = False
        foundation_separator_acquired = False
        foundation_name_acquired = False
        foundation_address_acquired = False
        foundation_field_acquired = False
        foundation_text_acquired = False

        if foundation_check:
            output = {'CompanyName' : {'font': [],
                                      'size': []},
                      'CompanyAddress' : {'font': [],
                                     'size': []},
                      'CompanyField' : {'font': [],
                                     'size': []},
                      'CompanyText' : {'font': [],
                                     'size': []},
                      'FoundationSeparator' : {'font':[],
                                              'size':[],
                                              'text':[]},
                      'FoundationName' : {'font': [],
                                      'size': []},
                      'FoundationAddress' : {'font': [],
                                     'size': []},
                      'FoundationField' : {'font': [],
                                     'size': []},
                      'FoundationText' : {'font': [],
                                     'size': []},

                     }
        else:
            output = {'CompanyName' : {'font': [],
                                      'size': []},
                      'CompanyAddress' : {'font': [],
                                     'size': []},
                      'CompanyField' : {'font': [],
                                     'size': []},
                      'CompanyText' : {'font': [],
                                     'size': []}

                     }

        while True:
            if not company_name_acquired:
                sample_company_name_temp = re.sub(r"(^[^\w]+)|([^\w]+$)", "", input("Please copy-paste a line of company name"))
                sample_company_name = [sample_company_name_temp]
                while True:
                    if input("Do you want to copy-paste more in order to ensure more data is captured? Y/N") == 'N':
                        break
                    else:
                        sample_company_name.append(input("Please copy-paste another line of company name"))
            if not company_address_acquired:
                sample_company_address_temp = re.sub(r"(^[^\w]+)|([^\w]+$)", "",input("Please copy-paste a line of company address"))
                sample_company_address = [sample_company_address_temp]
                while True:
                    if input("Do you want to copy-paste more in order to ensure more data is captured? Y/N") == 'N':
                        break
                    else:
                        sample_company_address.append(input("Please copy-paste another line of company address"))
            if not company_field_acquired:
                sample_company_field_temp = re.sub(r"(^[^\w]+)|([^\w]+$)", "",input("Please copy-paste a company field name"))
                sample_company_field = [sample_company_field_temp]
                while True:
                    if input("Do you want to copy-paste more in order to ensure more data is captured? Y/N") == 'N':
                        break
                    else:
                        sample_company_field.append(input("Please copy-paste another company field name"))
            if not company_text_acquired:
                sample_company_text_temp = re.sub(r"(^[^\w]+)|([^\w]+$)", "",input("Please copy-paste the text after the company field name"))
                sample_company_text = [sample_company_text_temp]
                while True:
                    if input("Do you want to copy-paste more in order to ensure more data is captured? Y/N") == 'N':
                        break
                    else:
                        sample_company_text.append(input("Please copy-paste another line of text after the company field name"))

            if foundation_check:
                if not foundation_separator_acquired:
                    sample_foundation_separator_temp = re.sub(r"(^[^\w]+)|([^\w]+$)", "", input("Please copy-paste the line that indicates the start of a foundation"))
                    sample_foundation_separator = [sample_foundation_separator_temp]
                    while True:
                        if input("Do you want to copy-paste more in order to ensure more data is captured? Y/N") == 'N':
                            break
                        else:
                            sample_foundation_separator.append(input("Please copy-paste another foundation separator"))

                if not foundation_name_acquired:
                    sample_foundation_name_temp = re.sub(r"(^[^\w]+)|([^\w]+$)", "", input("Please copy-paste a foundation name"))
                    sample_foundation_name = [sample_foundation_name_temp]
                    while True:
                        if input("Do you want to copy-paste more in order to ensure more data is captured? Y/N") == 'N':
                            break
                        else:
                            sample_foundation_name.append(input("Please copy-paste another foundation name"))

                if not foundation_address_acquired:
                    sample_foundation_address_temp = re.sub(r"(^[^\w]+)|([^\w]+$)", "",input("Please copy-paste a foundation address"))
                    sample_foundation_address = [sample_foundation_address_temp]
                    while True:
                        if input("Do you want to copy-paste more in order to ensure more data is captured? Y/N") == 'N':
                            break
                        else:
                            sample_foundation_address.append(input("Please copy-paste another foundation address"))

                if not foundation_field_acquired:
                    sample_foundation_field_temp = re.sub(r"(^[^\w]+)|([^\w]+$)", "",input("Please copy-paste a field name unique to foundations"))
                    sample_foundation_field = [sample_foundation_field_temp]
                    while True:
                        if input("Do you want to copy-paste more in order to ensure more data is captured? Y/N") == 'N':
                            break
                        else:
                            sample_foundation_field.append(input("Please copy-paste another foundation field name"))

                if not foundation_text_acquired:
                    sample_foundation_text_temp = re.sub(r"(^[^\w]+)|([^\w]+$)", "",input("Please copy-paste the text after the foundation field name"))
                    sample_foundation_text = [sample_foundation_text_temp]
                    while True:
                        if input("Do you want to copy-paste more in order to ensure more data is captured? Y/N") == 'N':
                            break
                        else:
                            sample_foundation_text.append(input("Please copy-paste more text following a foundation field name"))

            for count_page, page in enumerate(text_dict):
                for count_block_list, block_list in enumerate(page["blocks"]):
                    for count_line_list, line_list in enumerate(block_list["lines"]):
                        for count_line, line in enumerate(line_list["spans"]):

                            pdf_text = re.sub(r"(^[^\w]+)|([^\w]+$)", "", line['text'])

                            #Company Name
                            if pdf_text in sample_company_name:
                                if line['font'] in output['CompanyName']['font'] and line['size'] in output['CompanyName']['size']:
                                    continue
                                else:
                                    output['CompanyName']['font'].append(line['font'])
                                    output['CompanyName']['size'].append(line['size'])

                            #Company Address
                            if pdf_text in sample_company_address:
                                if line['font'] in output['CompanyAddress']['font'] and line['size'] in output['CompanyAddress']['size']:
                                    continue
                                else:
                                    output['CompanyAddress']['font'].append(line['font'])
                                    output['CompanyAddress']['size'].append(line['size'])

                            #Field name
                            if pdf_text in sample_company_field:
                                if line['font'] in output['CompanyField']['font'] and line['size'] in output['CompanyField']['size']:
                                    continue
                                else:
                                    output['CompanyField']['font'].append(line['font'])
                                    output['CompanyField']['size'].append(line['size'])

                            #Field text
                            if pdf_text in sample_company_text:
                                if line['font'] in output['CompanyText']['font'] and line['size'] in output['CompanyText']['size']:
                                    continue
                                else:
                                    output['CompanyText']['font'].append(line['font'])
                                    output['CompanyText']['size'].append(line['size'])

                            #Foundation Check
                            if foundation_check:
                                #Foundation Separator
                                if pdf_text in sample_foundation_separator:
                                    if line['font'] in output['FoundationSeparator']['font'] and line['size'] in output['FoundationSeparator']['size'] and line['text'] in output['FoundationSeparator']['text']:
                                        continue
                                    else:
                                        output['FoundationSeparator']['font'].append(line['font'])
                                        output['FoundationSeparator']['size'].append(line['size'])
                                        output['FoundationSeparator']['text'].append(line['text'])


                                #Foundation Name
                                if pdf_text in sample_foundation_name:
                                    if line['font'] in output['FoundationName']['font'] and line['size'] in output['FoundationName']['size']:
                                        continue
                                    else:
                                        output['FoundationName']['font'].append(line['font'])
                                        output['FoundationName']['size'].append(line['size'])


                                #Foundation Address
                                if pdf_text in sample_foundation_address:
                                    if line['font'] in output['FoundationAddress']['font'] and line['size'] in output['FoundationAddress']['size']:
                                        continue
                                    else:
                                        output['FoundationAddress']['font'].append(line['font'])
                                        output['FoundationAddress']['size'].append(line['size'])

                                #Field name
                                if pdf_text in sample_foundation_field:
                                    if line['font'] in output['FoundationField']['font'] and line['size'] in output['FoundationField']['size']:
                                        continue
                                    else:
                                        output['FoundationField']['font'].append(line['font'])
                                        output['FoundationField']['size'].append(line['size'])

                                #Field text
                                if pdf_text in sample_foundation_text:
                                    if line['font'] in output['FoundationText']['font'] and line['size'] in output['FoundationText']['size']:
                                        continue
                                    else:
                                        output['FoundationText']['font'].append(line['font'])
                                        output['FoundationText']['size'].append(line['size'])


            #Check if have all required data, if so break out of while True
            if not any([ExtractionToolComplex.isListEmpty(value) for values in output.values() for value in values.values()]):
                break

            #Company name
            if any([ExtractionToolComplex.isListEmpty(values) for values in output['CompanyName'].values()]):
                print("Failed to get data for company name.")
            else:
                company_name_acquired = True

            #Company Address
            if any([ExtractionToolComplex.isListEmpty(values) for values in output['CompanyAddress'].values()]):
                print("Failed to get data for company address.")
            else:
                company_address_acquired = True

            #Company Field
            if any([ExtractionToolComplex.isListEmpty(values) for values in output['CompanyField'].values()]):
                print("Failed to get data for company field name.")
            else:
                company_field_acquired = True

            #Company Text
            if any([ExtractionToolComplex.isListEmpty(values) for values in output['CompanyText'].values()]):
                print("Failed to get data for company text.")
            else:
                company_text_acquired = True

            #Foundation Check
            if foundation_check:
                #Foundation separator
                if any([ExtractionToolComplex.isListEmpty(values) for values in output['FoundationSeparator'].values()]):
                    print("Failed to get data for line that indicates the start of a foundation.")
                else:
                    foundation_separator_acquired = True

                #Foundation name
                if any([ExtractionToolComplex.isListEmpty(values) for values in output['FoundationName'].values()]):
                    print("Failed to get data for foundation name.")
                else:
                    foundation_name_acquired = True

                #Foundation Address
                if any([ExtractionToolComplex.isListEmpty(values) for values in output['FoundationAddress'].values()]):
                    print("Failed to get data for foundation address.")
                else:
                    foundation_address_acquired = True

                #Foundation Field
                if any([ExtractionToolComplex.isListEmpty(values) for values in output['FoundationField'].values()]):
                    print("Failed to get data for foundation field.")
                else:
                    foundation_field_acquired = True

                #Foundation Text
                if any([iExtractionToolComplex.sListEmpty(values) for values in output['FoundationText'].values()]):
                    print("Failed to get data for foundation text.")
                else:
                    foundation_text_acquired = True

            print('\n')   
            print(output)
            
        self.fontinfo = output

    def extractTextFromTextDict(self, text_dict = None):
        
        if text_dict is None:
            text_dict = self.text_dict
            
        output_list = []
        bannedStrings = banned_string
        
        for count_page, page in enumerate(text_dict):
            for count_block_list, block_list in enumerate(page["blocks"]):
                for count_line_list, line_list in enumerate(block_list["lines"]):
                    for count_line, line in enumerate(line_list["spans"]):

                         #Remove empty text
                        if line['text'].isspace():
                            continue
                        #Skip if trash text
                        if line['text'].strip() in bannedStrings:
                            continue

                        #If not then populate output_list with dict containing:
                        #size, font, text, line_number
                        output_list.append({'text' : line['text'],
                                           'size' : float(line['size']),
                                           'font' : line['font'],
                                           'line_number' : count_line_list})
        self.extracted_text = output_list

    def convertExtracttoTable(self, extracted_text = None, fontsize_data = None):
        
        if extracted_text is None:
            extracted_text = self.extracted_text
        if fontsize_data is None:
            fontsize_data = self.fontinfo
            
        #Initialize needed vars
        org_list = []
        foundation_list = []
        org_number = 0
        org_id = -1
        foundation_id = -1
        charitable_foundation = False

        #Loop through the extracted list-dict structure
        for line in extracted_text:


            #### Organizations #####
            #Check if font & size are that of org number / new org
            if (line['font'] in fontsize_data['CompanyName']['font']) & (int(line['size']) in [int(elem) for elem in fontsize_data['CompanyName']['size']]):
                charitable_foundation = False
                #Check if start of new org
                try :
                    #Throws ValueError if name of org
                    int(line['text'])
                except ValueError:
                    #Catch if no orgs created
                    if org_id < 0:
                        continue
                    #Only triggers when name of org
                    org_list[org_id]['Name'] = line['text'].strip()                   
                else:
                    #If not name of org then org number
                    if (line['font'] in fontsize_data['CompanyName']['font']) & (int(line['size']) in [int(elem) for elem in fontsize_data['CompanyName']['size']]):
                        org_number = line['text'].strip()
                        org_list.append({'id' : org_number,
                                         'isFoundation' : 'No'})
                        org_id += 1
             #Check if not in charitable organisation
            if not charitable_foundation:
                #Check if font & size are that of org address
                #Uses round to filter more text: other text has size that rounds to 8
                if (line['font'] in fontsize_data['CompanyAddress']['font']) & (round(line['size']) in [round(elem) for elem in fontsize_data['CompanyAddress']['size']]):
                    #Catch if no orgs created
                    if org_id < 0:
                        continue
                    #If key Address doesn't already exist, create it
                    if 'Address' not in org_list[org_id].keys():
                        org_list[org_id]['Address'] = ''
                        org_list[org_id]['Address'] += line['text']
                    else:
                        #Strip here to avoid unnecessary blank space
                        #Maybe handle this later?
                        org_list[org_id]['Address'] += line['text'].strip()

            #Check if font & size are that of field name
            if (line['font'] in fontsize_data['CompanyField']['font']) & (int(line['size']) in [int(elem) for elem in fontsize_data['CompanyField']['size']]):
                #Catch if no orgs created
                if org_id < 0:
                    continue

                #If key field doesn't already exist, create it. Checks if length string > 1 to remove bad text
                if (ExtractionToolComplex.removePuncandSpace(line['text']) not in org_list[org_id].keys()) & (len(ExtractionToolComplex.removePuncandSpace(line['text'])) > 1):
                    org_list[org_id][ExtractionToolComplex.removePuncandSpace(line['text'])] = ''

                #If field already exists, create new field with convention i - Name where i is number of fields with the same name +1
                elif (ExtractionToolComplex.removePuncandSpace(line['text']) in org_list[org_id].keys()):
                    num_instances = list(org_list[org_id].keys()).count(ExtractionToolComplex.removePuncandSpace(line['text']))
                    org_list[org_id][f"{num_instances + 1} - {ExtractionToolComplex.removePuncandSpace(line['text'])}"] = ''

            #Check if font & size are that of field text
            if (line['font'] in fontsize_data['CompanyText']['font']) & (round(line['size']) in [round(elem) for elem in fontsize_data['CompanyText']['size']]):
                #Catch if no orgs created
                if org_id < 0:
                    continue

                #Place in last dict key: will always be something there
                org_list[org_id][list( org_list[org_id])[-1]] += line['text']




            ### Foundations ####
            #Check if text indicates charitable foundation
            if (
                (line['font'] in fontsize_data['FoundationSeparator']['font']) & \
                (round(line['size']) in [round(elem) for elem in fontsize_data['FoundationSeparator']['size']]) & \
                (any([ExtractionToolComplex.removePuncandSpace(line['text']) in ExtractionToolComplex.removePuncandSpace(elem) for elem in fontsize_data['FoundationSeparator']['text']])) or (any([ExtractionToolComplex.removePuncandSpace(elem) in ExtractionToolComplex.removePuncandSpace(line['text']) for elem in fontsize_data['FoundationSeparator']['text']]))
               ):
                charitable_foundation = True

                #Foundations always start with lines of Helvetica Bold.  
                #Use that as a trigger with the boolean var start_foundation
                start_foundation = True
                foundation_list.append({'id' : org_number,
                                 'isFoundation' : 'Yes'})
                foundation_id +=1

            #Check if are in charitable foundation
            if charitable_foundation:
                #Trigger for name and address to differentiate from other text
                if start_foundation:
                    #Check if font & size are foundation name
                    if (line['font'] in fontsize_data['FoundationName']['font']) & any([round(line['size']) >= round(elem) for elem in fontsize_data['FoundationName']['size']]):
                         #If key Name doesn't already exist, create it
                        if 'Name' not in foundation_list[foundation_id].keys():
                            foundation_list[foundation_id]['Name'] = ''
                            foundation_list[foundation_id]['Name'] += line['text']

                            lineToSkip = line['line_number']


                    #Check if font & size are address
                    if (line['font'] in fontsize_data['FoundationAddress']['font']) & any([round(line['size']) >= round(elem) for elem in fontsize_data['FoundationAddress']['size']]):
                        #Check if are on different line than Name, meaning are on Address line
                        if line['line_number'] > lineToSkip:
                             #If key Address doesn't already exist, create it
                            if 'Address' not in foundation_list[foundation_id].keys():
                                foundation_list[foundation_id]['Address'] = ''
                                foundation_list[foundation_id]['Address'] += line['text'].strip()
                            else:
                                foundation_list[foundation_id]['Address'] += ' ' +line['text'].strip()



                #Check if font & size are that of field name
                #Outside of if start_foundation
                if (line['font'] in fontsize_data['FoundationField']['font']) & ((int(line['size']) in [int(elem) for elem in fontsize_data['FoundationField']['size']])):
                    #Trigger on first catch of non-address text
                    start_foundation = False

                    #Catch if no orgs created
                    if foundation_id < 0:
                        continue
                    #If key field doesn't already exist, create it. Checks if length string > 1 to remove bad text
                    if (ExtractionToolComplex.removePuncandSpace(line['text']) not in foundation_list[foundation_id].keys()) & (len(ExtractionToolComplex.removePuncandSpace(line['text'])) > 1):
                        foundation_list[foundation_id][ExtractionToolComplex.removePuncandSpace(line['text'])] = ''

                #Check if outside of adress
                if not start_foundation:
                    #Check if font & size are that of field text
                    if (line['font'] in fontsize_data['FoundationText']['font']) & (round(line['size']) in [round(elem) for elem in fontsize_data['FoundationText']['size']]):
                        #Catch if no orgs created
                        if foundation_id < 0:
                            continue

                        #Place in last dict key: will always be something there, non-generalizable method
                        foundation_list[foundation_id][list( foundation_list[foundation_id])[-1]] += line['text']

        return org_list, foundation_list


# In[1]:


class ColumnMerger:
    
    def __init__(self, df):
        self.df = df
    
    @staticmethod
    def similar(a, b):
        return SequenceMatcher(None, a, b).ratio()
    
    #Very inefficient but it probably works :)
    def similarityColnames(self, threshold, verbose = True):
        
        df = self.df
        
        i = 0
        output = []
        for j, col1 in enumerate(df.columns):
            output.append([col1])
            for col2 in df.columns:
                if col1 == col2:
                    continue

                if ColumnMerger.similar(col1, col2) >= threshold:
                    i += 1
                    output[j].append(col2)
                    if verbose:
                        print(f"{i}) {col1} - {col2}: {str(ColumnMerger.similar(col1,col2))}")

        #Remove 1 element lists and sort alphabetically
        output = [sorted(nested) for nested in output if len(nested)>1]
        #Remove duplicates
        cleaned_output = []
        for elem in output:
            if elem not in cleaned_output:
                cleaned_output.append(elem)
        
        self.similarity_scores = cleaned_output
        
    #Dumb way of concating similar columns with a threshold: doesn't check if there are values in both columns
    def concatSimilarStringColumns(self, df = None, scores = None, threshold = 0.8, drop = True, user_input = True):
        """ 
        Uses the output from similarityColnames
        Can be set to use user input or not. If no input from user, will merge every set of columns using first name in list
        Can be set to drop merged columns or not
        ------------
        NOTE: edge case exists where new name provided by user is same as old name. 
        ------------
        """
        #Use class variables
        if df is None:
            df = self.df
        if scores is None:
            scores = self.similarity_scores
        
        #If there are no scores, immediately return the df
        if len(scores) ==  0:
            return df
        
        #If user doesn't want to input anything
        if not user_input:
            while True:
                i = 0

                #Merge        
                #If want to keep first name in list, merge on col of that name
                df[scores[i][0]] = df[scores[i][0]].fillna('')
                for name in scores[i]:
                    if name != scores[i][0]:
                        df[scores[i][0]] += df[name].fillna('')


                #Then need to drop the merged columns
                if drop:
                    df = df.drop(scores[i][1:], axis=1)

                #Once done with merge, up counter
                i+=1

                #Once done with every column, finish
                if i == len(scores):
                    break

        #If user_input
        else:
            i = 0
            while True:
                #Get user input for if they want to merge columns in similarity list or not
                mergeResponse = input(f"Do you want to merge the columns in this list: {scores[i]}? Y/N\n")
                if mergeResponse not in ('Y','N'):
                    print("\nERROR: Please enter one of Y or N")
                    continue

                #Go to next if merge not desired
                if mergeResponse == 'N':
                    i+=1

                #Merge
                else:
                    #Get user input for desired name of column
                    while True:
                        nameResponse = input("If you want to keep the first name in this list, press 1. Else, press 2.")
                        if nameResponse not in ('1','2'):
                            print("\nERROR: Please enter one of 1 or 2")
                            continue
                        else:
                            break

                    #If want to keep first name in list, merge on col of that name
                    if nameResponse == '1':
                        df[scores[i][0]] = df[scores[i][0]].fillna('')
                        for name in scores[i]:
                            if name != scores[i][0]:
                                df[scores[i][0]] += df[name].fillna('')


                        #Then need to drop the merged columns
                        if drop:
                            df = df.drop(scores[i][1:], axis=1)
                    #If want to input a new name, merge by creating new column with inputed name
                    else:
                        newName = input("Input desired name for column.")

                        df[newName] = df[scores[i][0]].fillna('')
                        for name in scores[i]:
                            df[newName] += df[name].fillna('')

                        #Then need to drop the merged columns
                        if drop:
                            df = df.drop(scores[i], axis=1)


                    #Once done with merge, up counter
                    i+=1

                #Once done with every column, finish
                if i == len(scores):
                        break

        return df

