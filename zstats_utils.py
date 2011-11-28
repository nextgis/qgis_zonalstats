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

from osgeo import gdal

import csv
import codecs, cStringIO

class UnicodeWriter:
  def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
    # Redirect output to a queue
    self.queue = cStringIO.StringIO()
    self.writer = csv.writer(self.queue, dialect=dialect, **kwds)
    self.stream = f
    self.encoder = codecs.getincrementalencoder(encoding)()

  def writerow(self, row):
    self.writer.writerow([s.encode("utf-8") for s in row])
    # Fetch UTF-8 output from the queue ...
    data = self.queue.getvalue()
    data = data.decode("utf-8")
    # ... and reencode it into the target encoding
    data = self.encoder.encode(data)
    # write to the target stream
    self.stream.write(data)
    # empty queue
    self.queue.truncate(0)

  def writerows(self, rows):
    for row in rows:
      self.writerow(row)

def getVectorLayerByName( layerName ):
  layerMap = QgsMapLayerRegistry.instance().mapLayers()
  for name, layer in layerMap.iteritems():
    if layer.type() == QgsMapLayer.VectorLayer and layer.name() == layerName:
      if layer.isValid():
        return layer
      else:
        return None

def getRasterLayerByName( layerName ):
  layerMap = QgsMapLayerRegistry.instance().mapLayers()
  for name, layer in layerMap.iteritems():
    if layer.type() == QgsMapLayer.RasterLayer and ( layer.usesProvider() and layer.providerKey() == 'gdal' ) and layer.name() == layerName:
        if layer.isValid():
          return layer
        else:
          return None

def getVectorLayersNames():
  layerList = []
  layerMap = QgsMapLayerRegistry.instance().mapLayers()
  for name, layer in layerMap.iteritems():
    if layer.type() == QgsMapLayer.VectorLayer and layer.geometryType() == QGis.Polygon:
      layerList.append( unicode( layer.name() ) )
  return layerList

def getRasterLayersNames():
  layerList = []
  layerMap = QgsMapLayerRegistry.instance().mapLayers()
  for name, layer in layerMap.iteritems():
    if layer.type() == QgsMapLayer.RasterLayer and ( layer.usesProvider() and layer.providerKey() == 'gdal' ):
        layerList.append( unicode( layer.name() ) )
  return layerList

def getFieldList( vLayer ):
  vProvider = vLayer.dataProvider()
  return vProvider.fields()

def loadInMemory( vLayer ):
  crs = vLayer.crs().authid().toLower()
  uri = "Polygon?crs=" + crs + "&index=yes"
  mLayer = QgsVectorLayer( uri, "temp_poly", "memory" )
  mProvider = mLayer.dataProvider()

  vProvider = vLayer.dataProvider()
  allAttrs = vProvider.attributeIndexes()
  allFields = vLayer.dataProvider().fields()

  fields = []
  for i in allFields:
    fields.append( allFields[ i ] )

  mProvider.addAttributes( fields )

  vProvider.select( allAttrs )
  ft = QgsFeature()
  while vProvider.nextFeature( ft ):
    mProvider.addFeatures( [ ft ] )

  # FIXME: maybe this is not necessary and can be removed
  mLayer.startEditing()
  mLayer.commitChanges()
  return mLayer

def saveStatsToCSV( mLayer, filePath ):
  mProvider = mLayer.dataProvider()
  allAttrs = mProvider.attributeIndexes()
  mProvider.rewind()
  mProvider.select( allAttrs, QgsRectangle(), False )

  f = open( filePath, "wb" )
  writer = csv.writer( f )

  # first create column names
  row = []
  fields = mProvider.fields()
  for k, v in fields.iteritems():
    row.append( v.name() )
  writer.writerow( row )

  # now write data
  row = []
  feat = QgsFeature()
  while mProvider.nextFeature( feat ):
    attrMap = feat.attributeMap()
    for index, value in attrMap.iteritems():
      row.append( unicode( value.toString() ) )
    writer.writerow( row )
    row = []

  f.close()

def searchInLayer( vLayer, searchString ):
  search = QgsExpression( searchString )
  #print "SQL", searchString
  allAttrs = vLayer.dataProvider().attributeIndexes()

  if search.hasParserError():
    #QMessageBox.critical( this, tr( "Parsing error" ), search.parserErrorString() )
    print "Parsing error", str( search.parserErrorString() )
    return

  if not search.prepare( vLayer.pendingFields() ):
    #QMessageBox.critical( this, tr( "Evaluation error" ), search.evalErrorString() )
    print "Evaluation error", str( search.evalErrorString() )
    return

  vLayer.select( allAttrs, QgsRectangle(), False )
  f = QgsFeature()
  selectedFeatureIds = []
  while vLayer.nextFeature( f ):
    if search.evaluate( f ).toInt()[ 0 ] != 0:
      selectedFeatureIds.append( f.id() )

    # check if there were errors during evaluating
    if search.hasEvalError():
      print "Eval error during search"
      break

  return selectedFeatureIds

def writeReport( rptPath, dataPath, rptData, fieldName ):
  f = open( dataPath, "wb" )
  #writer = csv.writer( f )
  writer = UnicodeWriter( f )
  writer.writerow( [ fieldName, "object_count", "area" ] )

  rpt = QString( "<html><body>" )

  rpt += "<table width=\"100%\" border=\"1\">"
  rpt += "<tr><th>"
  rpt += QString( fieldName )
  rpt += "</th><th>"
  rpt += "Object count"
  rpt += "</th><th>"
  rpt += "Area"
  rpt += "</th></tr>"
  for row in rptData:
    rpt += "<tr><td align=\"center\">"
    rpt += QString( row[ 0 ] )
    rpt += "</td><td align=\"center\">"
    rpt += QString().setNum( int( row[ 1 ] ) )
    rpt += "</td><td align=\"center\">"
    rpt += QString().setNum( float( row[ 2 ] ) )
    rpt += "</td></tr>"
    #print row
    writer.writerow( row )
  rpt += "</table>"
  rpt += "</body></html>"

  f.close()

  # write report to file
  f = QFile( rptPath )
  if not f.open( QIODevice.WriteOnly | QIODevice.Text ):
    #QMessageBox::warning( this, tr( "Saving shortcuts" ),
    #                      tr( "Cannot write file %1:\n%2." )
    #                      .arg( fileName )
    #                      .arg( file.errorString() ) );
    print "Cannot write file"
    return

  out = QTextStream( f )
  out << rpt

  return rpt

def lastUsedReportDir():
  settings = QSettings( "NextGIS", "zstats" )
  return settings.value( "lastUsedReportDir", QVariant( "" ) ).toString()

def setLastUsedReportDir( lastDir ):
  path = QFileInfo( lastDir ).absolutePath()
  settings = QSettings( "NextGIS", "zstats" )
  settings.setValue( "lastUsedReportDir", QVariant( path ) )

def lastUsedDataDir():
  settings = QSettings( "NextGIS", "zstats" )
  return settings.value( "lastUsedDataDir", QVariant( "" ) ).toString()

def setLastUsedDataDir( lastDir ):
  path = QFileInfo( lastDir ).absolutePath()
  settings = QSettings( "NextGIS", "zstats" )
  settings.setValue( "lastUsedDataDir", QVariant( path ) )
