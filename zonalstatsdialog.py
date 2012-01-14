# -*- coding: utf-8 -*-

#******************************************************************************
#
# ZonalStats
# ---------------------------------------------------------
# Extended zonal statistics and report generation
#
# Copyright (C) 2011 Alexander Bruy (alexander.bruy@nextgis.org)
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

import zonalstats_utils as utils

from ui_zonalstatsdialogbase import Ui_ZonalStatsDialogBase

class ZonalStatsDialog( QDialog, Ui_ZonalStatsDialogBase ):
  def __init__( self, iface ):
    QDialog.__init__( self )
    self.setupUi( self )
    self.iface = iface

    self.okButton = self.buttonBox.button( QDialogButtonBox.Ok )
    self.closeButton = self.buttonBox.button( QDialogButtonBox.Close )

    QObject.connect( self.cmbVectorLayer, SIGNAL( "currentIndexChanged( QString )" ), self.updateFieldList )
    QObject.connect( self.chkSaveData, SIGNAL( "stateChanged( int )" ), self.updateDataPath )
    QObject.connect( self.btnSaveReport, SIGNAL( "clicked()" ), self.selectReportFile )
    QObject.connect( self.btnSaveData, SIGNAL( "clicked()" ), self.selectDataFile )

    self.manageGui()

  def manageGui( self ):
    self.leDataFile.setEnabled( False )
    self.btnSaveData.setEnabled( False )

    self.cmbRasterLayer.addItems( utils.getRasterLayersNames() )
    self.cmbVectorLayer.addItems( utils.getVectorLayersNames() )

  def updateFieldList( self, layerName ):
    self.cmbGroupField.clear()
    vLayer = utils.getVectorLayerByName( layerName )
    fields = utils.getFieldList( vLayer )
    for i in fields:
      if fields[ i ].type() in [ QVariant.Int, QVariant.String ]:
        self.cmbGroupField.addItem( fields[ i ].name() )

  def updateDataPath( self, state ):
    if state == Qt.Checked:
      self.leDataFile.setEnabled( True )
      self.btnSaveData.setEnabled( True )
    else:
      self.leDataFile.setEnabled( False )
      self.btnSaveData.setEnabled( False )

  def selectReportFile( self ):
    lastUsedDir = utils.lastUsedReportDir()
    fileName = QFileDialog.getSaveFileName( self, self.tr( "Save report" ),
               lastUsedDir, "HTML files (*.html *.HTML *.htm *.HTM)" )

    if fileName.isEmpty():
      return

    utils.setLastUsedReportDir( fileName )

    # ensure the user never ommited the extension from the file name
    if ( not fileName.toLower().endsWith( ".htm" ) ) and ( not fileName.toLower().endsWith( ".html" ) ):
      fileName += ".html"

    self.leReportFile.setText( fileName )

    # also generate data file path if checkbox not checked
    if not self.chkSaveData.isChecked():
      fi = QFileInfo( fileName )
      dataPath = fi.path() + "/" + fi.completeBaseName() + "_data.csv"
      self.leDataFile.setText( dataPath )

  def selectDataFile( self ):
    lastUsedDir = utils.lastUsedDataDir()
    fileName = QFileDialog.getSaveFileName( self, self.tr( "Save data as" ),
               lastUsedDir, "CSV files (*.csv *.CSV)" )

    if fileName.isEmpty():
      return

    utils.setLastUsedDataDir( fileName )

    # ensure the user never ommited the extension from the file name
    if not fileName.toLower().endsWith( ".csv" ):
      fileName += ".csv"

    self.leDataFile.setText( fileName )

  def accept( self ):
    # check input parameters
    if self.cmbRasterLayer.currentIndex() == -1:
      QMessageBox.warning( self, self.tr( "ZonalStats: Warning" ),
                           self.tr( "Please select raster layer to analyse" ) )
      return

    if self.cmbVectorLayer.currentIndex()  == -1:
      QMessageBox.warning( self, self.tr( "ZonalStats: Warning" ),
                           self.tr( "Please select vector layer to analyse" ) )
      return

    if self.leReportFile.text().isEmpty():
      QMessageBox.warning( self, self.tr( "ZonalStats: Warning" ),
                           self.tr( "Please select where to save report file" ) )
      return

    if self.leDataFile.text().isEmpty():
      QMessageBox.warning( self, self.tr( "ZonalStats: Warning" ),
                           self.tr( "Please select where to save data file" ) )
      return

    rasterPath = utils.getRasterLayerByName( self.cmbRasterLayer.currentText() ).source()
    vLayer = utils.getVectorLayerByName( self.cmbVectorLayer.currentText() )
    reportPath = self.leReportFile.text()
    dataPath = self.leDataFile.text()

    self.progressBar.setRange( 0, 3 )
    self.progressBar.setValue( 0 )

    memLayer = utils.loadInMemory( vLayer )
    memProvider = memLayer.dataProvider()

    self.progressBar.setValue( self.progressBar.value() + 1 )

    # get pixel size (need it for area calculation)
    pixelSize = utils.getRasterLayerByName( self.cmbRasterLayer.currentText() ).rasterUnitsPerPixel()

    # TODO: check attribute prefix
    prefix = ""

    # calculate zonal statistics
    zs = QgsZonalStatistics( memLayer, rasterPath, prefix )
    pd = QProgressDialog( self.tr( "Calculating zonal statistics" ), self.tr( "Abort..." ), 0, 0 )
    zs.calculateStatistics( pd )

    self.progressBar.setValue( self.progressBar.value() + 1 )

    if pd.wasCanceled():
      QMessageBox.error( self, self.tr( "ZonalStats: Error" ),
                         self.tr( "Hey!.. You abort statistics calculation, so there are no data for analysis. Exiting..." ) )
      self.progressBar.setValue( 0 )
      return

    # save full statistics to file near the input shapefile
    #fi = QFileInfo( vLayer.source() )
    #fPath = fi.path() + "/" + fi.completeBaseName() + "_full_stat.csv"
    #utils.saveStatsToCSV( memLayer, fPath )

    # get count field index
    #idxCount = memLayer.fieldNameIndex( "count" )
    idxCount = memLayer.fieldNameIndex( "sum" )

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
        stats = [ unicode( groupName ), str( len( fIds ) ), 0 ]
        for i in fIds:
          memLayer.featureAtId( i, ft, False, True )
          attrMap = ft.attributeMap()
          stats[ 2 ] += attrMap[ idxCount ].toFloat()[ 0 ]
        stats[ 2 ] = str( stats[ 2 ] * pixelSize )
        reportData.append( stats )
    else:
      allAttrs = memProvider.attributeIndexes()
      memLayer.select( allAttrs, QgsRectangle(), False )
      nameFieldIndex = memLayer.fieldNameIndex( self.cmbGroupField.currentText() )
      while memLayer.nextFeature( ft ):
        attrMap = ft.attributeMap()
        stats = [ unicode( attrMap[ nameFieldIndex ].toString() ), "1", "0" ]
        stats[ 2 ] = str( attrMap[ idxCount ].toFloat()[ 0 ] * pixelSize )
        reportData.append( stats )

    # save report as HTML
    rpt = utils.writeReport( reportPath, dataPath, reportData, unicode( self.cmbGroupField.currentText() ) )

    self.progressBar.setValue( self.progressBar.value() + 1 )

    # display report in viewer
    self.teReport.setHtml( rpt )
    self.progressBar.setValue( 0 )

    memLayer = None
