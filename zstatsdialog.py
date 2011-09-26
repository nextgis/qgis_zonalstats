# -*- coding: utf-8 -*-

#******************************************************************************
#
# ZStats
# ---------------------------------------------------------
# Extended zonal statistics and report generation
#
# Copyright (C) 2011 Alexander Bruy (alexander.bruy@gmail.com)
#
# This source is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# This code is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# A copy of the GNU General Public License is available on the World Wide Web
# at <http://www.gnu.org/copyleft/gpl.html>. You can also obtain it by writing
# to the Free Software Foundation, Inc., 59 Temple Place - Suite 330, Boston,
# MA 02111-1307, USA.
#
#******************************************************************************

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from qgis.core import *
from qgis.gui import *

import zstats_utils as utils

from ui_zstatsdialogbase import Ui_ZStatsDialog

class ZStatsDialog( QDialog, Ui_ZStatsDialog ):
  def __init__( self, iface ):
    QDialog.__init__( self )
    self.setupUi( self )
    self.iface = iface

    self.okButton = self.buttonBox.button( QDialogButtonBox.Ok )
    self.closeButton = self.buttonBox.button( QDialogButtonBox.Close )

    self.manageGui()

  def manageGui( self ):
    self.cmbRasterLayer.addItems( utils.getRasterLayersNames() )
    self.cmbVectorLayer.addItems( utils.getVectorLayersNames() )
