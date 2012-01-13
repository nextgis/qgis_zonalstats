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

import zonalstatsdialog

from __init__ import mVersion

import resources_rc

class ZonalStatsPlugin( object ):
  def __init__( self, iface ):
    self.iface = iface
    self.iface = iface
    try:
      self.QgisVersion = unicode( QGis.QGIS_VERSION_INT )
    except:
      self.QgisVersion = unicode( QGis.qgisVersion )[ 0 ]

    print "**** VERSION", self.QgisVersion

    # For i18n support
    userPluginPath = QFileInfo( QgsApplication.qgisUserDbFilePath() ).path() + "/python/plugins/zonalstats"
    systemPluginPath = QgsApplication.prefixPath() + "/python/plugins/zonalstats"

    overrideLocale = QSettings().value( "locale/overrideFlag", QVariant( False ) ).toBool()
    if not overrideLocale:
      localeFullName = QLocale.system().name()
    else:
      localeFullName = QSettings().value( "locale/userLocale", QVariant( "" ) ).toString()

    if QFileInfo( userPluginPath ).exists():
      translationPath = userPluginPath + "/i18n/zonalstats_" + localeFullName + ".qm"
    else:
      translationPath = systemPluginPath + "/i18n/zonalstats_" + localeFullName + ".qm"

    self.localePath = translationPath
    if QFileInfo( self.localePath ).exists():
      self.translator = QTranslator()
      self.translator.load( self.localePath )
      QCoreApplication.installTranslator( self.translator )

  def initGui( self ):
    # FIXME: need to adjust version check
    if int( self.QgisVersion ) < 10702:
      QMessageBox.warning( self.iface.mainWindow(), "ZonalStats",
                           QCoreApplication.translate( "ZonalStats", "Quantum GIS version detected: " ) + unicode( self.QgisVersion ) + ".xx\n" +
                           QCoreApplication.translate( "ZonalStats", "This version of ZonalStats requires at least QGIS version 1.7.2\nPlugin will not be enabled." ) )
      return None

    self.actionRun = QAction( QIcon( ":icons/zonalstats.png" ), "ZonalStats", self.iface.mainWindow() )
    self.actionRun.setStatusTip( QCoreApplication.translate( "ZonalStats", "Extended zonal statistics and report generation" ) )
    self.actionRun.setWhatsThis( QCoreApplication.translate( "ZonalStats", "Extended zonal statistics" ) )
    self.actionAbout = QAction( QIcon( ":icons/about.png" ), "About", self.iface.mainWindow() )

    QObject.connect( self.actionRun, SIGNAL( "triggered()" ), self.run )
    QObject.connect( self.actionAbout, SIGNAL( "triggered()" ), self.about )

    if hasattr( self.iface, "addPluginToRasterMenu" ):
      self.iface.addPluginToRasterMenu( QCoreApplication.translate( "ZonalStats", "ZonalStats" ), self.actionRun )
      self.iface.addPluginToRasterMenu( QCoreApplication.translate( "ZonalStats", "ZonalStats" ), self.actionAbout )
      self.iface.addRasterToolBarIcon( self.actionRun )
    else:
      self.iface.addPluginToMenu( QCoreApplication.translate( "ZonalStats", "ZonalStats" ), self.actionRun )
      self.iface.addPluginToMenu( QCoreApplication.translate( "ZonalStats", "ZonalStats" ), self.actionAbout )
      self.iface.addToolBarIcon( self.actionRun )

  def unload( self ):
    if hasattr( self.iface, "addPluginToRasterMenu" ):
      self.iface.removePluginRasterMenu( QCoreApplication.translate( "ZonalStats", "ZonalStats" ), self.actionRun )
      self.iface.removePluginRasterMenu( QCoreApplication.translate( "ZonalStats", "ZonalStats" ), self.actionAbout )
      self.iface.removeRasterToolBarIcon( self.actionRun )
    else:
      self.iface.removePluginMenu( QCoreApplication.translate( "ZonalStats", "ZonalStats" ), self.actionRun )
      self.iface.removePluginMenu( QCoreApplication.translate( "ZonalStats", "ZonalStats" ), self.actionAbout )
      self.iface.removeToolBarIcon( self.actionRun )

  def about( self ):
    dlgAbout = QDialog()
    dlgAbout.setWindowTitle( QApplication.translate( "ZonalStats", "About ZonalStats", "Window title" ) )
    lines = QVBoxLayout( dlgAbout )
    title = QLabel( QApplication.translate( "ZonalStats", "<b>ZonalStats</b>" ) )
    title.setAlignment( Qt.AlignHCenter | Qt.AlignVCenter )
    lines.addWidget( title )
    version = QLabel( QApplication.translate( "ZonalStats", "Version: %1" ).arg( mVersion ) )
    version.setAlignment( Qt.AlignHCenter | Qt.AlignVCenter )
    lines.addWidget( version )
    lines.addWidget( QLabel( QApplication.translate( "ZonalStats", "Extended zonal statistics and report generation" ) ) )
    lines.addWidget( QLabel( QApplication.translate( "ZonalStats", "<b>Developers:</b>" ) ) )
    lines.addWidget( QLabel( "  Alexander Bruy" ) )
    lines.addWidget( QLabel( QApplication.translate( "ZonalStats", "<b>Homepage:</b>") ) )

    overrideLocale = QSettings().value( "locale/overrideFlag", QVariant( False ) ).toBool()
    if not overrideLocale:
      localeFullName = QLocale.system().name()
    else:
      localeFullName = QSettings().value( "locale/userLocale", QVariant( "" ) ).toString()

    localeShortName = localeFullName[ 0:2 ]
    if localeShortName in [ "ru", "uk" ]:
      link = QLabel( "<a href=\"http://gis-lab.info/qa/zonalstats-qgis.html\">http://gis-lab.info/qa/zonalstats-qgis.html</a>" )
    else:
      link = QLabel( "<a href=\"http://gis-lab.info/qa/zonalstats-qgis.html\">http://gis-lab.info/qa/zonalstats-qgis.html</a>" )

    link.setOpenExternalLinks( True )
    lines.addWidget( link )

    btnClose = QPushButton( QApplication.translate( "ZonalStats", "Close" ) )
    lines.addWidget( btnClose )
    QObject.connect( btnClose, SIGNAL( "clicked()" ), dlgAbout, SLOT( "close()" ) )

    dlgAbout.exec_()

  def run( self ):
    dlg = zonalstatsdialog.ZonalStatsDialog( self.iface )
    dlg.exec_()
