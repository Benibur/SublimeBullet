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
  # last_row = 0
  # last_pos = 0
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
    if self.file_type > 0 and self.Modifying == False:
      self.update_last_pos(view)

  def update_last_pos(self, view):
    last_line = view.line(view.sel()[0])
    last_line_start = sublime.Region(last_line.begin())
    view.add_regions(BULLET_LAST_POINT, [last_line_start], BULLET_SCOPE, "", sublime.HIDDEN)

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
      self.Modifying = True
      insert_point = view.sel()[0].begin()
      row, col = view.rowcol(insert_point)
      last_cmd, last_cmd_args, last_cmd_count = view.command_history(0)
      non_undo = view.command_history(1)[0] == None

      # new line
      last_row = self.last_row(view)
      if last_row is not None and row > 0 and abs(row - last_row) == 1:
        self.bullet_event(view, insert_point, last_row)
      # elif non_undo and last_cmd == "join_lines":
        # TODO: remove leading bullet from joined lines
      self.update_last_pos(view)
      self.Modifying = False

  def bullet_event(self, view, insert_point, ref_row):
    ref_line = view.line(view.text_point(ref_row, 0))
    ref_row_start = ref_line.begin()
    ref_line_txt = view.substr(ref_line)
    if ref_line_txt != "":
      bullet_chars = self.bullet_chars[self.file_type].split()
      bullet_re = "|".join(map(re.escape, bullet_chars))
      search_re = "^( *|\t*)(%s|([0-9]+)\.) (.*)" % bullet_re
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
          # duplicate ref_line init whitespace
          line_start = view.line(insert_point).begin()
          init_whitespace = sublime.Region(line_start, insert_point)
          replacement = match_pattern.group(1)+insertion
          view.replace(edit, init_whitespace, replacement)
          final_pos = view.sel()[0].end()
          view.sel().clear()
          view.sel().add(sublime.Region(final_pos))
          view.end_edit(edit)
