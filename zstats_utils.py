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
  print "SQL", searchString
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

def lastUsedDir():
  settings = QSettings( "NextGIS", "zstats" )
  return settings.value( "lastUsedDir", QVariant( "" ) ).toString()

def setLastUsedDir( lastDir ):
  path = QFileInfo( lastDir ).absolutePath()
  settings = QSettings( "NextGIS", "zstats" )
  settings.setValue( "lastUsedDir", QVariant( path ) )
