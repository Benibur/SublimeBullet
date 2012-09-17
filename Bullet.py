# -*- coding: UTF-8 -*-
import sublime
import sublime_plugin
import re

# TODO: Better multi line pasting behaviour (esp the bug that if you paste a 2 lines content, a * will be added to the end of the pasting )
#       Just check whether the line is a empty line before inserting
# TODO: Can try to write to keymap files during start of sublime text. So the when one change the settings it will change the keymapping
# TODO: Write a text file in the plugin to indicate whether the settings are updated or not. When updated, write the keymap file accordingly.
# TODO: Also, put instruction text in the keymap file say they shouldn't manage the keymap file directly. If they really want to, they should put a false in the settings file "manage keymap autoamtically" part first.

BULLET_SCOPE = "sublime_bullet"
BULLET_LAST_POINT = "sublime_bullet_last_point"

class Bullet(sublime_plugin.EventListener):
  Modifying = False
  md_enabled = False
  rest_enabled = False
  file_type = 0
  bullet_chars = [
    "",
    "* - > +", # Markdown
    u"* - + \u2022 \u2043 \u2023" # reStructuredText (* - + • ⁃ ‣)
  ]

  def __init__(self):
    s = sublime.load_settings("Bullet.sublime-settings")
    self.md_enabled = s.get("markdown_bullet_enabled", True)
    self.rest_enabled = s.get("restructuredtext_bullet_enabled", False)

  def on_activated(self, view):
    # determine file_type
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

    # update last pos
    if self.file_type > 0:
      self.update_last_pos(view)
    else:
      view.erase_regions(BULLET_LAST_POINT)

  def on_selection_modified(self, view):
    if self.file_type > 0:
      self.update_last_pos(view)

  def match_bullet_line(self, text):
    bullet_chars = self.bullet_chars[self.file_type].split()
    bullet_re = "|".join(map(re.escape, bullet_chars))
    search_re = "^( *|\t*)(%s|([0-9]+)\.)(.*)" % bullet_re
    match_result = re.search(search_re, text)
    return match_result

  def update_last_pos(self, view):
    last_line = view.line(view.sel()[0])
    last_line_txt = view.substr(last_line)
    match_result = self.match_bullet_line(last_line_txt)
    if match_result is None:
      view.erase_regions(BULLET_LAST_POINT)
    else:
      last_line_start = sublime.Region(last_line.begin())
      view.add_regions(BULLET_LAST_POINT, [last_line_start], BULLET_SCOPE, "")

  def last_pos(self, view):
    last_regions = view.get_regions(BULLET_LAST_POINT)
    if len(last_regions) > 0:
      return last_regions[0].begin()

  def last_row(self, view):
    last_pos = self.last_pos(view)
    if last_pos is not None:
      return view.rowcol(last_pos)[0]

  def on_modified(self, view):
    if self.file_type > 0 and self.Modifying == False:
      last_row = self.last_row(view)
      if last_row is not None:
        self.Modifying = True
        current_point = view.sel()[0].begin()
        current_row = view.rowcol(current_point)[0]
        last_cmd, last_cmd_args, last_cmd_count = view.command_history(0)
        non_undo = view.command_history(1)[0] == None

        # new line
        if current_row > 0 and abs(current_row - last_row) == 1:
          self.add_or_remove_bullet(view)
        elif non_undo and last_cmd == "join_lines":
          self.join_bullet_lines(view)
        self.Modifying = False

  def add_or_remove_bullet(self, view):
    ref_row_start = self.last_pos(view)
    ref_line = view.line(ref_row_start)
    ref_line_txt = view.substr(ref_line)
    if ref_line_txt != "":
      match_result = self.match_bullet_line(ref_line_txt)
      if match_result != None:
        pre_bullet, bullet, num_bullet, bullet_contents = match_result.groups()
        if bullet_contents in [" ",""]:
          # remove empty bullet point upon newline
          reg_remove = view.find("\S.*", ref_row_start)
          edit = view.begin_edit()
          view.erase(edit,reg_remove)
          view.end_edit(edit)
        else:
          if num_bullet != None:
            # insert incremented number
            last_number = int(num_bullet)
            insertion = str(last_number+1) + ". "
          else:
            # insert bullet
            insertion = bullet + " "
          edit = view.begin_edit()
          # duplicate ref_line init whitespace
          insert_point = view.sel()[0].begin()
          line_start = view.line(insert_point).begin()
          init_whitespace = sublime.Region(line_start, insert_point)
          replacement = pre_bullet+insertion
          view.replace(edit, init_whitespace, replacement)
          final_pos = view.sel()[0].end()
          view.sel().clear()
          view.sel().add(sublime.Region(final_pos))
          view.end_edit(edit)

  def join_bullet_lines(self, view):
    line_start = self.last_pos(view)
    line = view.line(line_start)
    line_txt = view.substr(line)
    line_end = line.end()
    match_result = self.match_bullet_line(line_txt)
    bullet = match_result.groups()[1]
    if bullet.isdigit():
      bullet_re = "\d "
    else:
      bullet_re = re.escape(bullet)+" "

    first_bullet = view.find(bullet_re, line_start) #ignore
    search_start = first_bullet.end()
    found_bullets = []
    while True:
      b = view.find(bullet_re, search_start)
      if b is not None and b.end() < line_end:
        found_bullets.append(b)
        search_start = b.end()
      else:
        break

    edit = view.begin_edit()
    for b in reversed(found_bullets):
      view.erase(edit, b)
    view.end_edit(edit)

