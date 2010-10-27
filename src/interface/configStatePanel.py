"""
Panel presenting the configuration state for tor or arm. Options can be edited
and the resulting configuration files saved.
"""

import curses
import threading

from util import conf, panel, torTools, uiTools

DEFAULT_CONFIG = {"torrc.map": {}}

TOR_STATE, ARM_STATE = range(1, 3) # state to be presented

class ConfigEntry():
  """
  Configuration option in the panel.
  """
  
  def __init__(self, option, value, type, description = ""):
    self.option = option
    self.value = value
    self.type = type
    self.description = description

class ConfigStatePanel(panel.Panel):
  """
  Renders a listing of the tor or arm configuration state, allowing options to
  be selected and edited.
  """
  
  def __init__(self, stdscr, configType, config=None):
    panel.Panel.__init__(self, stdscr, "confState", 0)
    
    self._config = dict(DEFAULT_CONFIG)
    if config: config.update(self._config)
    
    self.configType = configType
    self.confContents = []
    self.scroll = 0
    self.valsLock = threading.RLock()
    
    # TODO: this will need to be able to listen for SETCONF events (arg!)
    
    if self.configType == TOR_STATE:
      # for all recognized tor config options, provide their current value
      conn = torTools.getConn()
      configOptionQuery = conn.getInfo("config/names", "").strip().split("\n")
      
      for lineNum in range(len(configOptionQuery)):
        # lines are of the form "<option> <type>", like:
        # UseEntryGuards Boolean
        line = configOptionQuery[lineNum]
        confOption, confType = line.strip().split(" ", 1)
        
        confValue = None
        if confOption in self._config["torrc.map"]:
          confMappings = conn.getOptionMap(self._config["torrc.map"][confOption], {})
          if confOption in confMappings: confValue = confMappings[confOption]
          fetchConfOption = self._config["torrc.map"][confOption]
        else:
          confValue = ", ".join(conn.getOption(confOption, [], True))
        
        # provides nicer values for recognized types
        if not confValue: confValue = "<none>"
        elif confType == "Boolean" and confValue in ("0", "1"):
          confValue = "False" if confValue == "0" else "True"
        elif confType == "DataSize" and confValue.isdigit():
          confValue = uiTools.getSizeLabel(int(confValue))
        elif confType == "TimeInterval" and confValue.isdigit():
          confValue = uiTools.getTimeLabel(int(confValue), isLong = True)
        
        self.confContents.append(ConfigEntry(confOption, confValue, confType))
    elif self.configType == ARM_STATE:
      # loaded via the conf utility
      armConf = conf.getConfig("arm")
      for key in armConf.getKeys():
        self.confContents.append(ConfigEntry(key, ", ".join(armConf.getValue(key, [], True)), ""))
      #self.confContents.sort() # TODO: make contents sortable?
  
  def handleKey(self, key):
    self.valsLock.acquire()
    if uiTools.isScrollKey(key):
      pageHeight = self.getPreferredSize()[0] - 1
      newScroll = uiTools.getScrollPosition(key, self.scroll, pageHeight, len(self.confContents))
      
      if self.scroll != newScroll:
        self.scroll = newScroll
        self.redraw(True)
  
  def draw(self, subwindow, width, height):
    self.valsLock.acquire()
    
    # draws the top label
    sourceLabel = "Tor" if self.configType == TOR_STATE else "Arm"
    self.addstr(0, 0, "%s Config:" % sourceLabel, curses.A_STANDOUT)
    
    # draws left-hand scroll bar if content's longer than the height
    scrollOffset = 0
    if len(self.confContents) > height - 1:
      scrollOffset = 3
      self.addScrollBar(self.scroll, self.scroll + height - 1, len(self.confContents), 1)
    
    # determines the width for the columns
    optionColWidth, valueColWidth, typeColWidth = 0, 0, 0
    
    for entry in self.confContents:
      optionColWidth = max(optionColWidth, len(entry.option))
      valueColWidth = max(valueColWidth, len(entry.value))
      typeColWidth = max(typeColWidth, len(entry.type))
    
    # TODO: make the size dynamic between the value and description
    optionColWidth = min(25, optionColWidth)
    valueColWidth = min(25, valueColWidth)
    
    for lineNum in range(self.scroll, len(self.confContents)):
      entry = self.confContents[lineNum]
      drawLine = lineNum + 1 - self.scroll
      
      optionLabel = uiTools.cropStr(entry.option, optionColWidth)
      valueLabel = uiTools.cropStr(entry.value, valueColWidth)
      
      self.addstr(drawLine, scrollOffset, optionLabel, curses.A_BOLD | uiTools.getColor("green"))
      self.addstr(drawLine, scrollOffset + optionColWidth + 1, valueLabel, curses.A_BOLD | uiTools.getColor("green"))
      self.addstr(drawLine, scrollOffset + optionColWidth + valueColWidth + 2, entry.type, curses.A_BOLD | uiTools.getColor("green"))
      
      if drawLine >= height: break
    
    self.valsLock.release()
