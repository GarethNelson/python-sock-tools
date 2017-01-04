"""
Python Sock tools: gen_proto.py - Generate a python module for parsing a custom protocol
Copyright (C) 2016 GarethNelson

This file is part of python-sock-tools

python-sock-tools is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 2 of the License, or
(at your option) any later version.

python-sock-tools is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with python-sock-tools.  If not, see <http://www.gnu.org/licenses/>.


This module is intended to be run as a command-line tool primarily, though a python API is also available.
"""

import eventlet
import argparse
import json
import time
import os

def get_parser():
    """Get a command-line parser for this tool

    This function simply returns a parser object from argparse, it is here only to make generating documentation simpler.

    Returns:
       argparse.ArgumentParser: The populated argument parser
    """
    parser = argparse.ArgumentParser(description='Autogenerate a python module that implements a custom protocol')
    parser.add_argument('-s','--specfile',type=str,help='The specification file to use',required=True)
    parser.add_argument('-t','--template',type=str,help='The location of the templates directory to use')
    parser.add_argument('-o','--output',  type=str,help='Where to write output',default='generated.py')
    return parser

def load_json_file(path):
    """Load and parse a JSON file

    Loads a JSON file from disk and attempts to parse it at the same time - a simple convenience wrapper around json.load().
    No exception handling is done, it is up to the caller to wrap in a try block if required.
    
    Args:
      path (str): Path to the JSON file needing to be loaded, this should usually be an absolute path

    Returns:
      object.object: The toplevel object parsed from the file, usually this is a dict or a list
    """
    json_fd = open(path,'r')
    retval = json.load(json_fd)
    json_fd.close()
    return retval

def load_template(path,template_name):
    """Load a single template

    Loads a single template file into memory, like load_json_file() this is primarily a simple convenience wrapper that handles opening and reading the full contents of a file.
    No exception handling is done, it is up to the caller to wrap in a try block if required.

    Args:
      path (str): The path to the directory containing the template file
      template_name (str): The name of the template to load

    Returns:
      str: The contents of the template file, in future this might be some sort of template object instead
    """
    template_filename = os.path.join(path,template_name)
    fd = open(template_filename,'r')
    retval = fd.read()
    fd.close()
    return retval

def get_template_vars(specdata,filename):
    """Get the template variables and their default values

    Evaluates the data from a specification file and uses it to build a dict of variables and their substitution values.

    Args:
       specdata (dict): The toplevel object from the specification file as loaded from load_json_file()
       filename (str): The absolute path to the specification file

    Returns:
       dict: A dict mapping %%VARIABLE%% tokens to the strings they should be replaced with
    """
    retval = {'%%PROTONAME%%':specdata['protocol_name'],
              '%%PROTOSOCK%%':specdata['protocol_sock'],
              '%%SPECFILE%%': filename,
              '%%DATETIME%%':time.ctime().upper(),
              '%%MIXINS%%':  ','.join(specdata['mixins']),
              '%%IMPORTS%%':'',
              '%%HANDLERS%%':''}
    for modname in specdata['imports']:
        retval['%%IMPORTS%%'] += ('import %s\n' % modname)
    msg_handlers_dict = {}
    for msg in specdata['messages']:
        msg_handlers_dict[msg['msg_type_int']] = '[self._handle_%s]' % msg['msg_type_str']
        param_str = ''
        if specdata['named_fields']:
           param_str = ','.join(map(lambda x: x+'=None',msg['fields']))
           retval['%%HANDLERS%%'] += '\n   def _handle_%s(self,from_addr,msg_type,msg_data):\n       self.handle_%s(from_addr,**msg_data)' % (msg['msg_type_str'],msg['msg_type_str'])
        else:
           param_str = ','.join(msg['fields'])
           retval['%%HANDLERS%%'] += '\n   def _handle_%s(self,from_addr,msg_type,msg_data):\n       self.handle_%s(from_addr,*msg_data)' % (msg['msg_type_str'],msg['msg_type_str'])
        retval['%%HANDLERS%%'] += '\n   def handle_%s(self,from_addr,%s):\n       pass' % (msg['msg_type_str'],param_str)
    msghandlers_str = repr(msg_handlers_dict)
    msghandlers_str = msghandlers_str.replace('u\'','')
    msghandlers_str = msghandlers_str.replace('\'','')
    retval['%%HANDLERS_DICT%%'] = msghandlers_str
    return retval

def load_templates(path):
    """Loads default templates
    
    A simple wrapper around load_template that loads all the default templates needed

    Args:
      path (str): The absolute path to the templates directory

    Returns:
      dict: A dict mapping the template name to the contents
    """
    retval = {'module':load_template(path,'module'),
              'protoclass':load_template(path,'protoclass')}
    return retval

def get_default_template_path():
    """Calculates the default templates path
    
    This function is provided as a convenience for users of the Python API, such as build_example_chat.py

    Returns:
       str: The default templates path
    """
    return os.path.join(os.path.dirname(os.path.abspath(__file__)),'templates')

def render_module(specfile_path,template_path,output_path):
    """Renders the generated python module
    
    This is where the real work happens - this function loads the specification file and templates then renders the module and writes it to disk.

    Args:
      specfile_path (str): Absolute path to the specification file
      template_path (str): Absolute path to the templates directory
      output_path   (str): Absolute path to the output file to create
    """
    specdata      = load_json_file(specfile_path)
    templates     = load_templates(template_path)
    template_vars = get_template_vars(specdata,specfile_path)
    for x in xrange(2):
        for k,v in templates.items():
            for var_k,var_v in template_vars.items():
                if var_k in v:
                   templates[k] = templates[k].replace(var_k,var_v)
            for t_k,t_v in templates.items():
                if ('%%%%%s%%%%' % t_k.upper()) in v:
                   templates[k] = templates[k].replace('%%%%%s%%%%' % t_k.upper(),templates[t_k])
    output_fd = open(output_path,'w')
    output_fd.write(templates['module'])
    output_fd.close()

if __name__=='__main__':
   
   args = get_parser().parse_args()
   if args.template is None:
      template_path = get_default_template_path()
   else:
      template_path = args.template

   specfile_path = os.path.abspath(args.specfile)
   output_path   = os.path.abspath(args.output)
   
   print 'Rendering specification file %s to %s using templates in %s' % (specfile_path,output_path,template_path)
   render_module(specfile_path,template_path,output_path)


