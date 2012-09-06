# -*- coding: UTF-8 -*-
import sublime
import sublime_plugin
import re

# TODO: Better multi line pasting behaviour (esp the bug that if you paste a 2 lines content, a * will be added to the end of the pasting )
#       Just check whether the line is a empty line before inserting
# TODO: Can try to write to keymap files during start of sublime text. So the when one change the settings it will change the keymapping
# TODO: Write a text file in the plugin to indicate whether the settings are updated or not. When updated, write the keymap file accordingly.
# TODO: Also, put instruction text in the keymap file say they shouldn't manage the keymap file directly. If they really want to, they should put a false in the settings file "manage keymap autoamtically" part first.

class Bullet(sublime_plugin.EventListener):
  Modifying = False
  md_enabled = False
  rest_enabled = False
  file_type = 0
  last_line = 0
  last_pos = 0
  #selectors = []
  selector_array = []
  bullet_chars = [
    "",
    "* - > +", # Markdown
    u"* - + \u2022 \u2043 \u2023" # reStructuredText (* - + • ⁃ ‣)
  ]

  def __init__(self):
    s = sublime.load_settings("Bullet.sublime-settings")
    self.md_enabled = s.get("markdown_bullet_enabled", True)
    self.rest_enabled = s.get("restructuredtext_bullet_enabled", False)
    #self.selector_array = selectors.split("|")
    #self.selector_array = ["text.html.markdown"]

  def on_activated(self, view):
    md_score = 0
    rest_score = 0
    if self.md_enabled:
      md_score = view.score_selector(0,'text.html.markdown')
    if self.rest_enabled:
      rest_score = view.score_selector(0,'text.restructuredtext')
    if md_score > 0 and md_score >= rest_score:
      self.file_type = 1
    elif rest_score > 0 and rest_score >= md_score:
      self.file_type = 2
    else:
      self.file_type = 0

    #for x in range(len(self.selector_array)):
    #  if (view.score_selector(0,self.selector_array[x]) > 0):
    #    self.is_markdown = True
    #    self.update_row(view)
    #    return
    #  else:
    #    self.is_markdown = False

  def on_selection_modified(self, view):
    if (self.file_type > 0):
      self.update_row(view)

  def update_row(self, view):
    loc = view.sel()[0]
    self.last_pos = loc.begin()
    row, col = view.rowcol(self.last_pos)
    self.last_line = row

  def on_modified(self, view):
    if self.Modifying == False:
      self.Modifying = True
      loc = view.sel()[0]
      row, col = view.rowcol(loc.begin())
      point_last_row = view.text_point(row - 1,0)
      if (row - self.last_line == 1):
        previous_line = view.substr(view.line(self.last_pos))
        if row != 0 and previous_line != "":
          bullet_chars = self.bullet_chars[self.file_type].split()
          bullet_re = "|".join(map(re.escape, bullet_chars))
          search_re = "^( *|\t*)(%s|([0-9]+)\.)(.*)" % bullet_re
          match_pattern = re.search(search_re, previous_line)
          if match_pattern != None:
            if match_pattern.group(4) in [" ",""]:
              # remove empty bullet point upon newline
              reg_remove = view.find("\S.*", point_last_row)
              edit = view.begin_edit()
              view.erase(edit,reg_remove)
              view.end_edit(edit)
            else:
              if match_pattern.group(3) != None:
                # insert incremented number
                last_number = int(match_pattern.group(3))
                insertion = str(last_number+1) + ". "
              else:
                # insert bullet
                insertion = match_pattern.group(2) + " "
              edit = view.begin_edit()
              view.insert(edit, loc.end(), insertion)
              view.end_edit(edit)
      self.update_row(view)
      self.Modifying = False

