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

from ui_zstatsdialogbase import Ui_ZStatsDialogBase

class ZStatsDialog( QDialog, Ui_ZStatsDialogBase ):
  def __init__( self, iface ):
    QDialog.__init__( self )
    self.setupUi( self )
    self.iface = iface

    self.okButton = self.buttonBox.button( QDialogButtonBox.Ok )
    self.closeButton = self.buttonBox.button( QDialogButtonBox.Close )

    QObject.connect( self.cmbVectorLayer, SIGNAL( "currentIndexChanged( QString )" ), self.updateFieldList )
    QObject.connect( self.chkGroupZones, SIGNAL( "stateChanged( int )" ), self.updateGrouping )
    QObject.connect( self.chkWriteReport, SIGNAL( "stateChanged( int )" ), self.updateReport )
    QObject.connect( self.btnBrowse, SIGNAL( "clicked()" ), self.selectReportFile )

    self.manageGui()

  def manageGui( self ):
    # disable some controls by default
    self.cmbGroupField.setEnabled( False )
    self.leReportFile.setEnabled( False )
    self.btnBrowse.setEnabled( False )

    self.cmbRasterLayer.addItems( utils.getRasterLayersNames() )
    self.cmbVectorLayer.addItems( utils.getVectorLayersNames() )

  def updateFieldList( self, layerName ):
    self.cmbGroupField.clear()
    vLayer = utils.getVectorLayerByName( layerName )
    fields = utils.getFieldList( vLayer )
    for i in fields:
      if fields[ i ].type() in [ QVariant.Int, QVariant.String ]:
        self.cmbGroupField.addItem( fields[ i ].name() )

  def updateGrouping( self, state ):
    if state == Qt.Checked:
      self.cmbGroupField.setEnabled( True )
    else:
      self.cmbGroupField.setEnabled( False )

  def updateReport( self, state ):
    if state == Qt.Checked:
      self.leReportFile.setEnabled( True )
      self.btnBrowse.setEnabled( True )
    else:
      self.leReportFile.setEnabled( False )
      self.btnBrowse.setEnabled( False )

  def selectReportFile( self ):
    lastUsedDir = utils.lastUsedDir()
    fileName = QFileDialog.getSaveFileName( self, self.tr( "Save report" ),
               lastUsedDir, "HTML files (*.html *.HTML *.htm *.HTM)" )

    if fileName.isEmpty():
      return

    utils.setLastUsedDir( fileName )

    # ensure the user never ommited the extension from the file name
    if ( not fileName.toLower().endsWith( ".htm" ) ) and ( not fileName.toLower().endsWith( ".html" ) ):
      fileName += ".html"

    self.leReportFile.setText( fileName )

  def accept( self ):
    pass
