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
from qgis.analysis import *

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
    QObject.connect( self.btnBrowse, SIGNAL( "clicked()" ), self.selectReportFile )

    self.manageGui()

  def manageGui( self ):
    self.cmbRasterLayer.addItems( utils.getRasterLayersNames() )
    self.cmbVectorLayer.addItems( utils.getVectorLayersNames() )

  def updateFieldList( self, layerName ):
    self.cmbGroupField.clear()
    vLayer = utils.getVectorLayerByName( layerName )
    fields = utils.getFieldList( vLayer )
    for i in fields:
      if fields[ i ].type() in [ QVariant.Int, QVariant.String ]:
        self.cmbGroupField.addItem( fields[ i ].name() )

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
    # check input parameters
    if self.cmbRasterLayer.currentIndex() == -1:
      QMessageBox.warning( self, self.tr( "ZStats: Warning" ),
                           self.tr( "Please select raster layer to analyse" ) )
      return

    if self.cmbVectorLayer.currentIndex()  == -1:
      QMessageBox.warning( self, self.tr( "ZStats: Warning" ),
                           self.tr( "Please select vector layer to analyse" ) )
      return

    rasterPath = utils.getRasterLayerByName( self.cmbRasterLayer.currentText() ).source()
    vLayer = utils.getVectorLayerByName( self.cmbVectorLayer.currentText() )
    reportPath = self.leReportFile.text()

    memLayer = utils.loadInMemory( vLayer )
    memProvider = memLayer.dataProvider()

    # get pixel size (need it for area calculation)
    pixelSize = utils.getRasterLayerByName( self.cmbRasterLayer.currentText() ).rasterUnitsPerPixel()

    # TODO: check attribute prefix
    prefix = ""

    # calculate zonal statistics
    zs = QgsZonalStatistics( memLayer, rasterPath, prefix )
    pd = QProgressDialog( self.tr( "Calculating zonal statistics" ), self.tr( "Abort..." ), 0, 0 )
    zs.calculateStatistics( pd )

    # for testing (should be removed)
    QgsMapLayerRegistry.instance().addMapLayer( memLayer )

    # save full statistics to file near the input shapefile
    fi = QFileInfo( vLayer.source() )
    fPath = fi.path() + "/" + fi.completeBaseName() + "_full_stat.csv"
    utils.saveStatsToCSV( memLayer, fPath )

    # get count field index
    idxCount = memLayer.fieldNameIndex( "count" )
    print "IDX", idxCount

    reportData = []
    ft = QgsFeature()

    # generate report
    if self.chkGroupZones.isChecked():
      grpFieldIndex = 0
      isString = False
      fieldName = self.cmbGroupField.currentText()
      for k, v in memProvider.fields().iteritems():
        if v.name() == fieldName:
          if v.type() == QVariant.String :
            isString = True
          grpFieldIndex = k
          break

      # get unique values
      uniqueValues = memProvider.uniqueValues( grpFieldIndex )
      allAttrs = memProvider.attributeIndexes()

      sqlString = None
      if isString:
        sqlString = QString( fieldName + " = '%1'")
      else:
        sqlString = QString( fieldName + " = %1" )

      # create zones
      for v in uniqueValues:
        groupName = v.toString()
        qry = sqlString.arg( groupName )
        fIds = utils.searchInLayer( memLayer, qry )
        stats = [ unicode( groupName ), len( fIds ), 0 ]
        for i in fIds:
          memLayer.featureAtId( i, ft, False, True )
          attrMap = ft.attributeMap()
          stats[ 2 ] += attrMap[ idxCount ].toFloat()[ 0 ]
        stats[ 2 ] = stats[ 2 ] * pixelSize
        reportData.append( stats )
    else:
      allAttrs = memProvider.attributeIndexes()
      memLayer.select( allAttrs, QgsRectangle(), False )
      nameFieldIndex = memLayer.fieldNameIndex( self.cmbGroupField.currentText() )
      while memLayer.nextFeature( ft ):
        attrMap = ft.attributeMap()
        stats = [ attrMap[ nameFieldIndex ].toString(), 1, 0 ]
        stats[ 2 ] = attrMap[ idxCount ].toFloat()[ 0 ] * pixelSize
        reportData.append( stats )

    # save report as HTML
    utils.writeReport( reportPath, reportData )
    memLayer = None
