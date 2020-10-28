import tkinter
import layout
import parse

from connect import request, stripoutUrl
from globalDeclare import Variables
from layout import CSSParser, InputLayout
from parse import TextNode, ElementNode

class Browser:
    def __init__(self):
        self.scroll = 0
        self.window = tkinter.Tk()
        self.window.title("Yu-Ching Hsu's Browser")
        self.canvas = tkinter.Canvas( self.window, width = Variables.WIDTH, height = Variables.HEIGHT)
        self.canvas.pack(expand=True, fill="both")
        self.window.bind("<Down>", self.scrolldown)
        self.window.bind("<Up>", self.scrollup)
        self.window.bind("<Configure>", self.windowresize)
        self.window.bind("<Button-1>", self.handle_click)
        self.window.bind("<Key>", self.keypress)
        self.window.bind("<Return>", self.pressenter)
        self.window.bind("<BackSpace>", self.backspace)
        self.gif_grinFace = tkinter.PhotoImage(file='resize_griningFace.gif')
        self.history = []
        self.future = []
        self.curridx = 0
        self.focus = None
        self.address_bar = ""

    def backspace(self, e):
        if self.focus == "address bar":
            if self.address_bar:
                self.address_bar = self.address_bar[:-1]
                self.render()
        elif self.focus:
            text = self.focus.node.attributes.get("value", "")
            if text != "":
                self.focus.node.attributes["value"] = text[:-1]
                self.layout(self.document.node)
                self.render()
    
    def pressenter(self, e):
        if self.focus == "address bar":
            self.focus = None
            self.future = []
            self.load(self.address_bar)
        elif self.focus: # is an obj (form)
            self.submit_form(self.focus.node)
            self.focus = None
            self.render()


    def keypress(self, e):
        if len(e.char) != 1 or ord(e.char) < 0x20 or 0x7f <= ord(e.char):
            return
        if not self.focus: return
        if self.focus == "address bar":
            if len(e.char) == 1 and 0x20 <= ord(e.char) < 0x7f:
                self.address_bar += e.char
                self.render()
        elif isinstance(self.focus, InputLayout):
            self.focus.node.attributes["value"] += e.char
            self.layout(self.document.node)

    def handle_click(self, e):
        self.focus = None
        if e.y < 60: # Browser chrome
            # click "back" button
            if 10 <= e.x < 35 and 10 <= e.y < 50:
                self.go_back()
            # click "forward" button
            elif 45 <= e.x < 70 and 10 <= e.y < 50:
                self.go_forward()
            # click address bar
            elif 80 <= e.x < 800 and 10 <= e.y < 50:
                self.focus = "address bar"
                self.address_bar = ""
                self.render()

        else: # page content
            x, y = e.x, e.y - 60 + self.scroll
            obj = find_layout(x, y, self.document)
            if not obj: return
            elt = obj.node

            # press on <input>
            if is_input(elt): 
                self.click_input(elt)
                self.focus = obj
                self.layout(self.document.node)

            while elt and not is_link(elt) and elt.tag != "button":
                elt = elt.parent
            if not elt:
                pass
            elif is_link(elt):
                temp = self.url
                if isinstance(self.url, str):
                    temp = stripoutUrl(self.url)
                url = relative_url(elt.attributes["href"], temp)
                self.future = []
                self.load(url)
            elif elt.tag == "button":
                self.submit_form(elt)

    def submit_form(self, elt):
        while elt and elt.tag != 'form':
            elt = elt.parent
        if not elt: return
        inputs = find_inputs(elt, [])
        body = ""
        for input in inputs:
            name = input.attributes['name']
            value = input.attributes.get('value', '')
            body += "&" + name + "="
            body += value.replace(" ", "%20")
        body = body[1:]
     
        if isinstance(self.url, str):
            self.url = stripoutUrl(self.url)
        url = relative_url(elt.attributes['action'], self.url)

        self.load(url, body)



    def click_input(self, elt):
        # elt = obj.node
        elt.attributes["value"] = ""

    def go_back(self):
        if len(self.history) > 1: # if no previous page, then not enter
            self.future.append(self.history.pop())
            back = self.history.pop()
            self.load(back)

    def go_forward(self):
        if self.future:
            self.load(self.future.pop())

    def scrolldown(self, e):
        self.scroll = self.scroll + Variables.SCROLL_STEP
        self.scroll = min(self.scroll, self.max_y)
        self.scroll = max(0, self.scroll)
        self.render()

    def scrollup(self, e):
        self.scroll -= Variables.SCROLL_STEP
        self.render()

    def windowresize(self, e):
        Variables.WIDTH = e.width
        Variables.HEIGHT = e.height
        self.layout(self.tree)
    
    def layout(self, tree):
        self.tree = tree
    
        self.document = layout.DocumentLayout(tree)
        self.document.layout()
        self.display_list = []
        self.document.draw(self.display_list)
        self.render()
        self.max_y = self.document.h

        # _print_tree(self.tree, "  ")

    def render(self):
        self.canvas.delete("all")
        for cmd in self.display_list:
            if cmd.y1 > self.scroll + Variables.HEIGHT: continue
            if cmd.y2 < self.scroll: continue
            cmd.draw(self.scroll - 60, self.canvas)

        # address bar
        self.canvas.create_rectangle(80, 0, 800, 60, width=0, fill='light gray')
        self.canvas.create_rectangle(Variables.ADDR_START, 10, 790, 50)
        
        font = tkinter.font.Font(family="Courier", size=20)
        url = self.url
        if not isinstance(url, str):
            url = self.url.scheme+"://"+self.url.host+self.url.path
        self.canvas.create_text(Variables.ADDR_START+5, 15, anchor='nw', text=self.address_bar, font=font)
    
        # back button
        if len(self.history)>1: button_color = "black"
        else: button_color = "gray"
        self.canvas.create_rectangle(10, 10, 35, 50)
        self.canvas.create_polygon(15, 30, 30, 20, 30, 40, fill=button_color)
        
        # forward button x1,y1,x2,y2
        if self.future: button_color = "black"
        else: button_color = "gray"
        self.canvas.create_rectangle(45, 10, 70, 50)
        self.canvas.create_polygon(50, 20, 65, 30, 50, 40, fill=button_color)
        if self.focus == "address bar":
            w = font.measure(self.address_bar)
            self.canvas.create_line(Variables.ADDR_START+5 + w, 15, Variables.ADDR_START+5 + w, 45)

        # <input> cursor
        if isinstance(self.focus, InputLayout):
            text = self.focus.node.attributes.get("value", "")
            x = self.focus.x + self.focus.font.measure(text)
            y = self.focus.y
            # add 60px to make up the address bar
            self.canvas.create_line(x, y+60, x, y + self.focus.h + 60)


    def load(self, url, body=None): # body: encode form for params
        self.url = url

        if isinstance(url, str):
            self.address_bar = url
            url = stripoutUrl(url)
        else: 
            self.address_bar = url.scheme+"://"+url.host+url.path
        
        self.history.append(url)

        response = request(url, body)
        header, body = response.headers, response.body
        tokens = parse.lex(body)
        nodes = parse.ParseTree().parse(tokens)

        with open("browser.css") as f:
            browser_style = f.read()
            rules = CSSParser(browser_style).parse()

        for link in find_links(nodes, []):
            cssurl = relative_url(link, url)
            cssurl = stripoutUrl(cssurl)
            response = request(cssurl)
            header, body = response.headers, response.body
            rules.extend(CSSParser(body).parse())

        rules.sort(key=lambda t:t[0].priority(),
            reverse=True)
        style(nodes, rules, None)
        self.layout(nodes)

def find_links(node, lst):
    if not isinstance(node, ElementNode): return
    if node.tag == "link" and \
       node.attributes.get("rel", "") == "stylesheet" and \
       "href" in node.attributes:
        lst.append(node.attributes["href"])
    for child in node.children:
        find_links(child, lst)
    return lst

def find_layout(x, y, tree):
    for child in reversed(tree.children):
        result = find_layout(x, y, child)
        if result: return result
    if tree.x <= x < tree.x + tree.w and \
       tree.y <= y < tree.y + tree.h:
        return tree

def relative_url(url, current) -> str: #current: Url
    current = current.scheme+"://"+current.host+current.path
    if "://" in url:
        return url
    elif url.startswith("/"):
        return "/".join(current.split("/")[:3]) + url
    else:
        return current.rsplit("/", 1)[0] + "/" + url

def is_input(elt):
    if isinstance(elt, ElementNode) and \
        elt.tag == "input":
        return True
    return False

def is_link(node):
    return isinstance(node, ElementNode) \
        and node.tag == "a" and "href" in node.attributes

def style(node, rules, parent):
    if isinstance(node, TextNode):
        node.style = parent.style
    else:
        for selector, pairs in rules:
            if selector.matches(node):
                for property in pairs:
                    if property not in node.style:
                        node.style[property] = pairs[property]
    
        for property, default in Variables.INHERITED_PROPERTIES.items():
            if property not in node.style:
                if parent:
                    node.style[property] = parent.style[property]
                else:
                    node.style[property] = default
        
        for child in node.children:
            style(child, rules, node)

def find_inputs(elt, out):
    if not isinstance(elt, ElementNode): return
    if elt.tag == 'input' and 'name' in elt.attributes:
        out.append(elt)
    for child in elt.children:
        find_inputs(child, out)
    return out

def _print_tree(tree, indent_space):
        print(f'{indent_space} {tree}')
        if isinstance(tree, parse.ElementNode):   
            for child in tree.children:    
                _print_tree(child, indent_space + '  ')