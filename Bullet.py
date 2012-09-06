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
  last_row = 0
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
    self.last_row = row

  def on_modified(self, view):
    if self.Modifying == False:
      self.Modifying = True
      insert_point = view.sel()[0].begin()
      row, col = view.rowcol(insert_point)
      last_cmd, last_cmd_args, last_cmd_count = view.command_history(0)

      # new line
      if row != 0 and row - self.last_row == 1:
        ref_row = row - 1 # row above
        self.bullet_event(view, insert_point, ref_row)
      elif last_cmd == "run_macro_file" and last_cmd_count == 1 \
          and last_cmd_args == {'file': u'Packages/Default/Add Line Before.sublime-macro'}:
        ref_row = row + 1
        self.bullet_event(view, insert_point, ref_row)
      self.update_row(view)
      self.Modifying = False

  def bullet_event(self, view, insert_point, ref_row):
    ref_line = view.line(view.text_point(ref_row, 0))
    ref_row_start = ref_line.begin()
    ref_line_txt = view.substr(ref_line)
    if ref_line_txt != "":
      bullet_chars = self.bullet_chars[self.file_type].split()
      bullet_re = "|".join(map(re.escape, bullet_chars))
      search_re = "^( *|\t*)(%s|([0-9]+)\.)(.*)" % bullet_re
      match_pattern = re.search(search_re, ref_line_txt)
      if match_pattern != None:
        if match_pattern.group(4) in [" ",""]:
          # remove empty bullet point upon newline
          reg_remove = view.find("\S.*", ref_row_start)
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
          view.insert(edit, insert_point, insertion)
          view.end_edit(edit)
