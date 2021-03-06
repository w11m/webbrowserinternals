import tkinter
import tkinter.font
import re
import shlex
import layout
from globalDeclare import Variables


class Text:
    def __init__(self, text):
        self.text = text

class Tag:
    def __init__(self, text):
        # keep space between the quotes
        parts = shlex.split(text)
        self.tag = parts[0].lower()
        self.attributes = {}
        for attrpair in parts[1:]:
            if "=" in attrpair:
                key, value = attrpair.split("=", 1)
                self.attributes[key.lower()] = value
            else:
                self.attributes[attrpair.lower()] = ""
        
class ElementNode:
    def __init__(self, tag, attributes, parent):
        self.tag = tag
        self.children = []
        self.attributes = attributes
        self.parent = parent

        self.style = {}
        for pair in self.attributes.get("style", "").split(";"):
            if ":" not in pair: continue
            prop, val = pair.split(":")
            self.style[prop.strip().lower()] = val.strip()

    def __repr__(self):
        return "<" + self.tag + ">"

class TextNode:
    def __init__(self, text, parent):
        self.text = text
        self.parent = parent

    def __repr__(self):
        return self.text

def lex(body):
    '''classity with Text (take out < and >) and Tag -> out: list'''
    out, text, in_tag = [], "", False
    for c in body:
        if c == "<":
            in_tag = True
            if text: out.append(Text(text))
            text = ""
        elif c == ">":
            in_tag = False
            out.append(Tag(text))
            text = ""
        else:
            text += c
            for entity in Variables.ENTITIES:
                idx = text.find(entity)
                if idx >= 0:
                    text = text[:idx] + Variables.ENTITIES[entity] + text[idx+len(entity):]
    if not in_tag and text:
        out.append(Text(text))
    return out

class ParseTree:
    def parse(self, tokens):
        currently_open = []
        for tok in tokens:
            # add the implicit tag to currently_open
            currently_open = self.implicit_tags(tok, currently_open)
            if isinstance(tok, Text):
                node = TextNode(tok.text, currently_open[-1])
                if not currently_open: continue
                currently_open[-1].children.append(node)
            elif tok.tag.startswith("/"):
                node = currently_open.pop()
                if not currently_open: 
                    return node
                currently_open[-1].children.append(node)
                
            elif tok.tag in Variables.SELF_CLOSING_TAGS:
                node = ElementNode(tok.tag, tok.attributes, currently_open[-1])
                currently_open[-1].children.append(node)

            elif tok.tag.startswith("!"):
                continue
            else:
                node = None
                if currently_open == []:
                    node = ElementNode(tok.tag, tok.attributes, None)
                else:
                    node = ElementNode(tok.tag, tok.attributes, currently_open[-1])
                currently_open.append(node)

    
        while currently_open:
            node = currently_open.pop()
            if not currently_open: return node
            currently_open[-1].children.append(node)
        

    def implicit_tags(self, tok, currently_open):
        tag = tok.tag if isinstance(tok, Tag) else None
        while True:
            open_tags = [node.tag for node in currently_open]
            if open_tags == [] and tag != "html":
                currently_open.append(ElementNode("html", {}, None))
            elif open_tags == ["html"] and tag not in ["head", "body", "/html"]:
                if tag in Variables.HEAD_TAGS:
                    implicit = "head"
                else:
                    implicit = "body"
                currently_open.append(ElementNode(implicit, {}, currently_open[-1]))
            elif open_tags == ["html", "head"] and tag not in ["/head"] + HEAD_TAGS:
                node = currently_open.pop()
                currently_open[-1].children.append(node)
                currently_open.append(ElementNode("body", {}, currently_open[-1]))
            else: break
        return currently_open
    
    

